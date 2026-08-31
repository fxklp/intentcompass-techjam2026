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
from solution.retrieval import BaselineFTS5Retriever, DualRouteInMemoryRetriever
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
        if config.retrieval == "hybrid":
            from solution.retrieval.hybrid import HybridRetriever
            self.retriever = HybridRetriever(catalog_path, assets)
        else:
            self.retriever = backend(catalog_path)
        self.mode = config.mode
        self.backend_name = config.retrieval
        self.offline_ranking = os.environ.get("INTENTCOMPASS_OFFLINE_RANKING", "baseline")
        self.field_evidence = None
        if self.offline_ranking.startswith("field_"):
            from solution.field_evidence import FieldEvidence
            self.field_evidence = FieldEvidence(self.retriever.index.connection)
        self.sessions: dict[str, AdaptiveSession] = {}
        self.semantic = make_reranker()
        if os.environ.get("INTENTCOMPASS_SEMANTIC") == "local":
            from solution.local_reranker import LocalReranker
            self.semantic = LocalReranker(assets)

    def reset(self, session_id: str, profile: dict) -> None:
        self.sessions[session_id] = AdaptiveSession(ContextMemory.create(profile))

    def close(self) -> None:
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
        request = RetrievalRequest(
            query=query,
            limit=50 if self.mode == "integrated" else plan.pool_limit,
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
        ranked = candidates[:ranking_limit] if result.trace.fallback_used else rank_candidates(
            candidates, state, ranking_limit, profile_priors=() if self.mode == "integrated" else session.memory.active_priors(),
            primary_fields=self.field_evidence.get([c.parent_asin for c in candidates]) if self.field_evidence else None,
            policy=self.offline_ranking,
        )
        context = session.memory.distill(state)
        semantic_result = None
        cutoff = self.mode == "integrated" and plan.reason == "cutoff_and_clarify"
        if not result.trace.fallback_used and output_limit > 0 and not cutoff:
            if getattr(self.semantic, "demand_variant", "legacy") != "legacy":
                semantic_result = session.demand.rerank(self.semantic, ranked, context)
            else:
                semantic_result = self.semantic.rerank(ranked, context)
            ranked = semantic_result.candidates
        ranked = ranked[:output_limit]
        if self.mode == "integrated":
            attribute, question_message = choose_question(state)
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
