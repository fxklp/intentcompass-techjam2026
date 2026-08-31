"""Core-private orchestration over the existing retrieval-lane protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
import os

from solution.clarification import Clarification, choose_adaptive_question
from solution.question_policy import choose_question
from solution.config import CoreConfig
from solution.context import ContextMemory
from solution.contracts import AgentResponse, Candidate
from solution.ranker import rank_candidates
from solution.retrieval import BaselineFTS5Retriever, DualRouteInMemoryRetriever
from solution.retrieval.contracts import RetrievalConstraint, RetrievalRequest
from solution.state import SessionState
from solution.semantic import MAX_CANDIDATES
from solution.chat_reranker import make_reranker
from solution.workflow import WorkflowState
from solution.api_demand import DemandState
from solution.buying_constraints import ConstraintReport, filter_buying_candidates
from solution.retrieval.contracts import RetrievalResult, RetrievalTrace


@dataclass
class AdaptiveSession:
    memory: ContextMemory
    workflow: WorkflowState = field(default_factory=WorkflowState)
    last_trace: dict = field(default_factory=dict)
    demand: DemandState = field(default_factory=DemandState)


class AdaptiveController:
    def __init__(self, catalog_path: Path, config: CoreConfig) -> None:
        backend = DualRouteInMemoryRetriever if config.retrieval == "dual_route" else BaselineFTS5Retriever
        assets = Path(os.environ.get("INTENTCOMPASS_SEMANTIC_ASSETS", str(Path(__file__).resolve().parents[1] / "artifacts/semantic")))
        if config.retrieval == "hybrid":
            from solution.retrieval.hybrid import HybridRetriever
            self.retriever = HybridRetriever(catalog_path, assets)
        else:
            self.retriever = backend(catalog_path)
        self.mode = config.mode
        self.backend_name = config.retrieval
        self.offline_ranking = os.environ.get(
            "INTENTCOMPASS_OFFLINE_RANKING",
            "constraints" if self.mode == "integrated" else "baseline",
        )
        self.field_evidence = None
        if self.offline_ranking.startswith("field_"):
            from solution.field_evidence import FieldEvidence
            self.field_evidence = FieldEvidence(self.retriever.index.connection)
        self.sessions: dict[str, AdaptiveSession] = {}
        self.evidence_counts: Counter[str] = Counter()
        self.semantic = make_reranker()
        if os.environ.get("INTENTCOMPASS_SEMANTIC") == "local":
            from solution.local_reranker import LocalReranker
            self.semantic = LocalReranker(assets)
        elif os.environ.get("INTENTCOMPASS_SEMANTIC") == "local_llm":
            from solution.local_llm_reranker import LocalLLMReranker
            self.semantic = LocalLLMReranker(assets)
        ordering = os.environ.get("INTENTCOMPASS_CATEGORY_ORDER", "head")
        if ordering not in {"head", "off"}:
            raise ValueError("INTENTCOMPASS_CATEGORY_ORDER must be head or off")
        self.category_order = None
        if (ordering == "head" and self.mode == "integrated" and config.retrieval == "baseline"
                and self.offline_ranking == "constraints" and not self.semantic.enabled):
            from solution.category_order import CategoryHeadOrder
            self.category_order = CategoryHeadOrder(self.retriever.index)
        terminal_mode = os.environ.get("INTENTCOMPASS_TERMINAL_RECOVERY", "lastchance")
        if terminal_mode not in {"off", "terminal", "lastchance"}:
            raise ValueError("invalid terminal recovery mode")
        self.terminal = None
        if terminal_mode != "off" and self.category_order is not None:
            from solution.terminal_recovery import TerminalRecovery
            self.terminal = TerminalRecovery(self.retriever.index, terminal_mode)
        from solution.precision_order import DEFAULT, VARIANTS, PrecisionOrder
        precision_mode = os.environ.get("INTENTCOMPASS_PRECISION_ORDER", DEFAULT)
        if precision_mode not in VARIANTS:
            raise ValueError("invalid precision ordering mode")
        self.precision = (PrecisionOrder(self.retriever.index, precision_mode)
                          if precision_mode != "off" and self.category_order is not None else None)
        from solution.final_policy import DEFAULT as FINAL_DEFAULT, VARIANTS as FINAL_VARIANTS, FinalPolicy
        final_mode = os.environ.get("INTENTCOMPASS_FINAL_POLICY", FINAL_DEFAULT)
        if final_mode not in FINAL_VARIANTS:
            raise ValueError("INTENTCOMPASS_FINAL_POLICY must be on or off")
        self.final_policy = (FinalPolicy(self.retriever.index, self.precision)
                             if final_mode == "on" and self.precision is not None else None)

    def reset(self, session_id: str, profile: dict) -> None:
        self.sessions[session_id] = AdaptiveSession(ContextMemory.create(profile))
        if self.final_policy is not None:
            self.final_policy.reset(session_id)
        if self.terminal:
            self.terminal.reset(session_id)

    def export_profile(self, session_id: str) -> dict:
        """Explicit caller-controlled handoff; never links sessions itself."""
        if session_id not in self.sessions:
            raise KeyError(session_id)
        return self.sessions[session_id].memory.export_profile()

    def close(self) -> None:
        if self.final_policy is not None:
            self.final_policy.close()
        if self.precision is not None:
            self.precision.close()
        if self.terminal:
            self.terminal.close()
        if self.field_evidence is not None:
            self.field_evidence.close()
        self.retriever.close()
        self.sessions.clear()

    def respond(self, state: SessionState, message: str, turn: int, top_k: int) -> dict:
        session = self.sessions[state.session_id]
        state.apply_user_message(message, turn, flexible=True)
        changed = session.memory.observe(state, message)
        plan = session.workflow.plan(state, message, changed=changed)
        output_limit = max(0, min(10, int(top_k)))
        query = state.retrieval_query(turn)
        if plan.recovery and state.category and (
            self.mode != "integrated" or self.backend_name != "baseline"
        ):
            query = state.category
        if plan.skip_expensive:
            pool_limit = 0
        elif self.terminal is not None:
            pool_limit = self.terminal.pool_limit(state, message, output_limit)
        else:
            pool_limit = plan.pool_limit
        request = RetrievalRequest(
            query=query,
            limit=pool_limit,
            route_hint=plan.route,
            category=state.category,
            constraints=tuple(RetrievalConstraint(key, slot.values) for key, slot in state.preferences.items()),
            turn=turn,
        )
        retrieval_calls = 0
        if plan.skip_expensive:
            # Popularity is already computed during initialization.  This path
            # performs no FTS/dense query and no model call.
            identifiers = self.retriever.index.fallback_ids[:output_limit]
            cheap = []
            for rank, identifier in enumerate(identifiers):
                product = self.retriever.index.candidate_data(identifier)
                cheap.append(self._retrieval_candidate(identifier, rank, product))
            result = RetrievalResult(
                tuple(cheap),
                RetrievalTrace(
                    plan.route,
                    ("pre_retrieval_cutoff", "cached_popularity_prior"),
                    ("cached_popularity_prior",),
                    (("cached_popularity_prior", len(cheap)),),
                    (),
                    fallback_used=True,
                ),
            )
        else:
            result = self.retriever.search(request)
            retrieval_calls = 1
        candidates = [Candidate(item.parent_asin, item.retrieval_rank, item.retrieval_score, item.searchable_text, item.price) for item in result.candidates]
        constraint_report = ConstraintReport(0, 0, len(candidates), bool(candidates))
        if plan.route == "buying" and not result.trace.fallback_used:
            candidates, constraint_report = filter_buying_candidates(candidates, state)
        # Popularity fallback is a compatibility promise: do not reinterpret
        # metadata from a no-match pool as query relevance or profile evidence.
        ranking_limit = max(output_limit, getattr(self.semantic, "candidate_limit", MAX_CANDIDATES)) if self.semantic.enabled else output_limit
        if self.terminal and request.limit > 50:
            ranking_limit = len(candidates)
        if self.offline_ranking == "field_dominance" and not result.trace.fallback_used:
            from solution.field_evidence import refine_by_dominance
            ranked = rank_candidates(candidates, state, ranking_limit, policy="constraints")
            ranked = refine_by_dominance(ranked, state, self.field_evidence.get([c.parent_asin for c in ranked[:10]]))
        else:
            ranked = candidates[:ranking_limit] if result.trace.fallback_used else rank_candidates(
                candidates, state, ranking_limit, profile_priors=session.memory.active_priors(),
                primary_fields=self.field_evidence.get([c.parent_asin for c in candidates]) if self.field_evidence else None,
                policy=self.offline_ranking,
            )
        if self.category_order is not None:
            ranked = self.category_order.reorder(ranked, state.category, fallback=result.trace.fallback_used)
        if self.precision is not None:
            ranked = self.precision.reorder(ranked, state, fallback=result.trace.fallback_used)
        if self.final_policy is not None:
            ranked = self.final_policy.reorder(ranked, state, fallback=result.trace.fallback_used)
        if self.terminal:
            if request.limit > 50:
                head = candidates[:output_limit] if result.trace.fallback_used else rank_candidates(
                    candidates[:50], state, output_limit, policy="constraints")
                head = self.category_order.reorder(head, state.category, fallback=result.trace.fallback_used)
                if self.precision is not None:
                    head = self.precision.reorder(head, state, fallback=result.trace.fallback_used)
                if self.final_policy is not None:
                    head = self.final_policy.reorder(head, state, fallback=result.trace.fallback_used)
                ids = {c.parent_asin for c in head}
                ranked = [*head, *(c for c in ranked if c.parent_asin not in ids)]
            ranked = self.terminal.reorder(candidates, state, ranked, message, output_limit, fallback=result.trace.fallback_used)
        context = session.memory.distill(state)
        semantic_result = None
        cutoff = plan.skip_expensive or (self.mode == "integrated" and plan.reason == "cutoff_and_clarify")
        if not result.trace.fallback_used and output_limit > 0 and not cutoff:
            if getattr(self.semantic, "demand_variant", "legacy") != "legacy":
                semantic_result = session.demand.rerank(self.semantic, ranked, context)
            else:
                semantic_result = self.semantic.rerank(ranked, context)
            ranked = semantic_result.candidates
        ranked = ranked[:output_limit]
        if self.mode == "integrated":
            if plan.skip_expensive:
                attribute, question_message = "category", "What type of product are you looking for?"
                question = Clarification(attribute, question_message, "pre_retrieval_cutoff", False)
            elif plan.recovery or session.workflow.rejected_turns > 0:
                # Candidate-derived information gain is most useful while
                # exploring or recovering from rejection.  Precise Buying
                # turns retain the established stable slot order.
                question = choose_adaptive_question(
                    state, candidates, output_limit=output_limit,
                    fallback_used=result.trace.fallback_used,
                )
            else:
                attribute, question_message = choose_question(state)
                question = Clarification(
                    attribute, question_message, "stable_buying_priority",
                    len(candidates) > max(10, output_limit * 2),
                )
            if self.final_policy is not None and not question.overloaded and not plan.skip_expensive:
                attribute, question_message = self.final_policy.question(
                    state, candidates, message, fallback=result.trace.fallback_used, output_limit=output_limit)
                question = Clarification(attribute, question_message, "final_policy", False)
            if turn >= 10:
                attribute, question_message = None, "Here are the closest matches for your current preferences."
                question = Clarification(attribute, question_message, "turn_budget_exhausted", question.overloaded)
        else:
            question = choose_adaptive_question(state, candidates, output_limit=output_limit, fallback_used=result.trace.fallback_used)
        state.mark_asked(question.attribute)
        # Candidate overload changes subsequent retrieval only when it follows
        # observable negative feedback.  A normal 50/80-item recall pool is not
        # itself evidence that the user is overloaded.
        session.workflow.overloaded = bool(
            question.overloaded and session.workflow.rejected_turns > 0
        )
        session.workflow.last_fallback = result.trace.fallback_used
        session.last_trace = {
            "mode": self.mode,
            "backend": self.backend_name,
            "intent_route": plan.route,
            "workflow": plan.reason,
            "query": query,
            "pool_limit": request.limit,
            "candidate_count": len(candidates),
            "constraint_evidence": constraint_report.to_dict(),
            "calls": {"retrieval": retrieval_calls, "semantic": int(bool(semantic_result and semantic_result.attempted))},
            "retrieval": result.trace.to_dict(),
            "question": {
                "attribute": question.attribute,
                "reason": question.reason,
                "overloaded": question.overloaded,
                "information_gain": question.information_gain,
                "coverage": question.coverage,
            },
            "context": context,
            "semantic": {
                "reason": semantic_result.reason if semantic_result else "fallback_or_no_output",
                "attempted": semantic_result.attempted if semantic_result else False,
                "usage_known": semantic_result.usage is not None if semantic_result else True,
            },
        }
        self.evidence_counts[f"route:{plan.route}"] += 1
        self.evidence_counts[f"workflow:{plan.reason}"] += 1
        self.evidence_counts[f"retrieval_calls:{retrieval_calls}"] += 1
        for route_name in result.trace.routes:
            self.evidence_counts[f"channel:{route_name}"] += 1
        semantic_reason = semantic_result.reason if semantic_result else "not_called"
        self.evidence_counts[f"semantic:{semantic_reason}"] += 1
        self.evidence_counts["constraint:satisfied"] += constraint_report.satisfied
        self.evidence_counts["constraint:conflict"] += constraint_report.conflict
        self.evidence_counts["constraint:unknown"] += constraint_report.unknown
        if context["profile_priors"]:
            self.evidence_counts["profile:consumed"] += 1
        payload = AgentResponse(question.message, question.attribute, tuple(item.parent_asin for item in ranked)).to_payload()
        if semantic_result is not None:
            if semantic_result.usage is None:
                payload.pop("usage", None)
            else:
                payload["usage"] = semantic_result.usage
        return payload

    @staticmethod
    def _retrieval_candidate(identifier: str, rank: int, product):
        from solution.retrieval.contracts import Candidate as RetrievalCandidate

        return RetrievalCandidate(
            identifier, rank, 0.0, product.searchable_text, product.price,
            product.categories,
        )
