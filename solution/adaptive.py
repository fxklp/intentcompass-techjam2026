"""Core-private orchestration over the existing retrieval-lane protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from solution.clarification import choose_adaptive_question
from solution.config import CoreConfig
from solution.context import ContextMemory
from solution.contracts import AgentResponse, Candidate
from solution.ranker import rank_candidates
from solution.retrieval import BaselineFTS5Retriever, DualRouteInMemoryRetriever
from solution.retrieval.contracts import RetrievalConstraint, RetrievalRequest
from solution.state import SessionState
from solution.semantic import MAX_CANDIDATES, SemanticReranker
from solution.workflow import WorkflowState


@dataclass
class AdaptiveSession:
    memory: ContextMemory
    workflow: WorkflowState = field(default_factory=WorkflowState)
    last_trace: dict = field(default_factory=dict)


class AdaptiveController:
    def __init__(self, catalog_path: Path, config: CoreConfig) -> None:
        backend = DualRouteInMemoryRetriever if config.retrieval == "dual_route" else BaselineFTS5Retriever
        self.retriever = backend(catalog_path)
        self.backend_name = config.retrieval
        self.sessions: dict[str, AdaptiveSession] = {}
        self.semantic = SemanticReranker()

    def reset(self, session_id: str, profile: dict) -> None:
        self.sessions[session_id] = AdaptiveSession(ContextMemory.create(profile))

    def close(self) -> None:
        self.retriever.close()
        self.sessions.clear()

    def respond(self, state: SessionState, message: str, turn: int, top_k: int) -> dict:
        session = self.sessions[state.session_id]
        state.apply_user_message(message, turn, flexible=True)
        changed = session.memory.observe(state, message)
        plan = session.workflow.plan(state, message, changed=changed)
        output_limit = max(0, min(10, int(top_k)))
        query = state.retrieval_query(turn)
        if plan.recovery and state.category:
            query = state.category
        request = RetrievalRequest(
            query=query,
            limit=plan.pool_limit,
            route_hint=plan.route,
            category=state.category,
            constraints=tuple(RetrievalConstraint(key, slot.values) for key, slot in state.preferences.items()),
            turn=turn,
        )
        result = self.retriever.search(request)
        candidates = [Candidate(item.parent_asin, item.retrieval_rank, item.retrieval_score, item.searchable_text, item.price) for item in result.candidates]
        # Popularity fallback is a compatibility promise: do not reinterpret
        # metadata from a no-match pool as query relevance or profile evidence.
        ranking_limit = max(output_limit, MAX_CANDIDATES) if self.semantic.enabled else output_limit
        ranked = candidates[:ranking_limit] if result.trace.fallback_used else rank_candidates(
            candidates, state, ranking_limit, profile_priors=session.memory.active_priors(),
        )
        context = session.memory.distill(state)
        semantic_result = None
        if not result.trace.fallback_used and output_limit > 0:
            semantic_result = self.semantic.rerank(ranked, context)
            ranked = semantic_result.candidates
        ranked = ranked[:output_limit]
        question = choose_adaptive_question(state, candidates, output_limit=output_limit, fallback_used=result.trace.fallback_used)
        state.mark_asked(question.attribute)
        session.workflow.overloaded = question.overloaded
        session.workflow.last_fallback = result.trace.fallback_used
        session.last_trace = {
            "mode": "adaptive",
            "backend": self.backend_name,
            "intent_route": plan.route,
            "workflow": plan.reason,
            "query": query,
            "pool_limit": plan.pool_limit,
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
