from __future__ import annotations

import time
from pathlib import Path

from solution.contracts import AgentResponse, Candidate as CoreCandidate
from solution.question_policy import choose_question
from solution.ranker import rank_candidates
from solution.retrieval import (
    BaselineFTS5Retriever,
    DualRouteInMemoryRetriever,
    RetrievalConstraint,
    RetrievalRequest,
)
from solution.state import SessionState


class RetrievalExperimentAgent:
    """Main-Agent-compatible shell used only to isolate candidate retrieval."""

    def __init__(self, catalog_path: str | Path, mode: str) -> None:
        started = time.perf_counter()
        if mode == "baseline":
            self._retriever = BaselineFTS5Retriever(catalog_path)
        elif mode == "candidate":
            self._retriever = DualRouteInMemoryRetriever(catalog_path)
        else:
            raise ValueError(f"unsupported retrieval mode: {mode}")
        self.startup_seconds = time.perf_counter() - started
        self.mode = mode
        self._sessions: dict[str, SessionState] = {}
        self._audits: dict[str, dict[str, object]] = {}
        self.session_audits: list[dict[str, object]] = []
        self.respond_latencies_ms: list[float] = []
        self.retrieval_latencies_ms: list[float] = []

    def close(self) -> None:
        self._retriever.close()

    def reset(self, session_id: str, user_profile: dict) -> None:
        normalized_id = str(session_id)
        self._sessions[normalized_id] = SessionState.create(normalized_id, user_profile)
        audit: dict[str, object] = {"turns": []}
        self._audits[normalized_id] = audit
        self.session_audits.append(audit)

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        respond_started = time.perf_counter()
        normalized_id = str(session_id)
        if normalized_id not in self._sessions:
            raise RuntimeError("reset must be called before respond")
        state = self._sessions[normalized_id]
        state.apply_user_message(str(user_message), int(turn))
        output_limit = max(0, min(10, int(top_k)))
        request = RetrievalRequest(
            query=state.retrieval_query(turn),
            limit=max(50, output_limit * 5),
            category=state.category,
            constraints=tuple(
                RetrievalConstraint(attribute=attribute, values=slot.values)
                for attribute, slot in state.preferences.items()
            ),
            turn=int(turn),
        )
        retrieval_started = time.perf_counter()
        result = self._retriever.search(request)
        retrieval_ms = (time.perf_counter() - retrieval_started) * 1000.0
        self.retrieval_latencies_ms.append(retrieval_ms)
        core_candidates = [
            CoreCandidate(
                parent_asin=item.parent_asin,
                retrieval_rank=item.retrieval_rank,
                retrieval_score=item.retrieval_score,
                searchable_text=item.searchable_text,
                price=item.price,
            )
            for item in result.candidates
        ]
        ranked = rank_candidates(core_candidates, state, output_limit)
        ask_attribute, message = choose_question(state)
        state.mark_asked(ask_attribute)
        turns = self._audits[normalized_id]["turns"]
        assert isinstance(turns, list)
        turns.append(
            {
                "turn": int(turn),
                "candidate_ids": [item.parent_asin for item in result.candidates],
                "trace": result.trace.to_dict(),
                "retrieval_ms": round(retrieval_ms, 6),
            }
        )
        payload = AgentResponse(
            message=message,
            ask_attribute=ask_attribute,
            recommendations=tuple(candidate.parent_asin for candidate in ranked),
        ).to_payload()
        self.respond_latencies_ms.append((time.perf_counter() - respond_started) * 1000.0)
        return payload
