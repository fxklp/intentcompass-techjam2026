from __future__ import annotations

from pathlib import Path

from solution.agent_impl import Agent as CoreAgent


class Agent:
    """Official interface adapter; all behavior lives in ``solution``."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self._core = CoreAgent(catalog_path)

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._core.reset(session_id, user_profile)

    def close(self) -> None:
        """Release local resources used by the optional offline retriever."""
        self._core.close()

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        return self._core.respond(session_id, user_message, turn, top_k)
