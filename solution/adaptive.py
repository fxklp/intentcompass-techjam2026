"""Core-private orchestration over the existing retrieval-lane protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from solution.clarification import Clarification, choose_adaptive_question
from solution.question_policy import choose_question
from solution.config import CoreConfig
from solution.context import ContextMemory
from solution.contracts import AgentResponse, Candidate
from solution.ranker import rank_candidates
from solution.retrieval import BaselineFTS5Retriever, CapabilityRetriever, DualRouteInMemoryRetriever
from solution.retrieval.contracts import RetrievalConstraint, RetrievalRequest
from solution.state import SessionState
from solution.semantic import MAX_CANDIDATES
from solution.chat_reranker import make_reranker
from solution.workflow import WorkflowState
from solution.api_demand import DemandState


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
        if config.retrieval == "capability":
            self.retriever = CapabilityRetriever(catalog_path, assets)
        elif config.retrieval == "hybrid":
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
        semantic_mode = os.environ.get("INTENTCOMPASS_SEMANTIC", "local" if config.retrieval == "capability" else "off")
        self.semantic = make_reranker()
        if semantic_mode == "local":
            from solution.local_reranker import LocalReranker
            self.semantic = LocalReranker(assets)
        ordering = os.environ.get("INTENTCOMPASS_CATEGORY_ORDER", "head")
        if ordering not in {"head", "off"}:
            raise ValueError("INTENTCOMPASS_CATEGORY_ORDER must be head or off")
        self.category_order = None
        if (ordering == "head" and self.mode == "integrated" and config.retrieval in {"baseline", "capability"}
                and self.offline_ranking == "constraints"):
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
        if self.mode != "integrated" and plan.recovery and state.category:
            query = state.category
        pool_limit = self.terminal.pool_limit(state, message, output_limit) if self.terminal else (50 if self.mode == "integrated" else plan.pool_limit)
        if plan.recovery:
            pool_limit = max(pool_limit, plan.pool_limit)
        request = RetrievalRequest(
            query=query,
            limit=pool_limit,
            route_hint=plan.route,
            category=state.category,
            constraints=tuple(RetrievalConstraint(key, slot.values) for key, slot in state.preferences.items()),
            turn=turn,
        )
        result = self.retriever.search(request)
        candidates = [Candidate(item.parent_asin, item.retrieval_rank, item.retrieval_score, item.searchable_text, item.price) for item in result.candidates]
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
            priors = session.memory.active_priors()
            if self.backend_name == "capability" and not state.user_profile.get("consent_personalization", False):
                priors = ()
            ranked = candidates[:ranking_limit] if result.trace.fallback_used else rank_candidates(
                candidates, state, ranking_limit, profile_priors=priors,
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
        if self.backend_name == "capability" and not state.user_profile.get("consent_personalization", False):
            # The same consent boundary applies to every ranking backend. Do
            # not expose unconsented aggregate priors to local/API semantics.
            context["profile_priors"] = {}
        semantic_result = None
        cutoff = self.mode == "integrated" and plan.reason == "cutoff_and_clarify"
        semantic_needed = (self.backend_name != "capability"
                           or "semantic_candidate" in result.trace.reason_codes
                           or os.environ.get("INTENTCOMPASS_FORCE_SEMANTIC") == "1")
        if not result.trace.fallback_used and output_limit > 0 and not cutoff and semantic_needed:
            if getattr(self.semantic, "demand_variant", "legacy") != "legacy":
                semantic_result = session.demand.rerank(self.semantic, ranked, context)
            else:
                semantic_result = self.semantic.rerank(ranked, context)
            ranked = semantic_result.candidates
        ranked = ranked[:output_limit]
        if self.mode == "integrated":
            attribute, question_message = choose_question(state)
            if self.final_policy is not None:
                attribute, question_message = self.final_policy.question(
                    state, candidates, message, fallback=result.trace.fallback_used, output_limit=output_limit)
            if turn >= 10:
                attribute, question_message = None, "Here are the closest matches for your current preferences."
            question = Clarification(attribute, question_message, "stable_priority_under_overload", len(candidates) > max(10, output_limit*2))
        else:
            question = choose_adaptive_question(state, candidates, output_limit=output_limit, fallback_used=result.trace.fallback_used)
        state.mark_asked(question.attribute)
        session.workflow.overloaded = question.overloaded
        session.workflow.last_fallback = result.trace.fallback_used
        session.last_trace = {
            "mode": self.mode,
            "backend": self.backend_name,
            "intent_route": plan.route,
            "workflow": plan.reason,
            "query": query,
            "pool_limit": request.limit,
            "candidate_count": len(candidates),
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
        payload = AgentResponse(question.message, question.attribute, tuple(item.parent_asin for item in ranked)).to_payload()
        if semantic_result is not None:
            if semantic_result.usage is None:
                payload.pop("usage", None)
            else:
                payload["usage"] = semantic_result.usage
        return payload
