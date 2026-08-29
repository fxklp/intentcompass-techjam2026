from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


ALLOWED_ATTRIBUTES = (
    "category",
    "material",
    "color",
    "size",
    "style",
    "brand",
    "budget",
    "feature",
    "use_case",
    "other",
)


@dataclass(frozen=True)
class PreferenceSlot:
    """One replaceable active preference, with all values from its latest update."""

    attribute: str
    values: tuple[str, ...]
    source_turn: int


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    limit: int


@dataclass(frozen=True)
class Candidate:
    parent_asin: str
    retrieval_rank: int
    retrieval_score: float
    searchable_text: str
    price: float | None = None


class CandidateRetriever(Protocol):
    def search(self, request: RetrievalRequest) -> list[Candidate]: ...


@dataclass(frozen=True)
class AgentResponse:
    message: str
    ask_attribute: str | None
    recommendations: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict:
        ask_attribute = self.ask_attribute if self.ask_attribute in ALLOWED_ATTRIBUTES else None
        seen: set[str] = set()
        ordered: list[dict[str, str]] = []
        for parent_asin in self.recommendations:
            normalized = str(parent_asin).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append({"parent_asin": normalized})
            if len(ordered) >= 10:
                break
        return {
            "message": str(self.message),
            "ask_attribute": ask_attribute,
            "recommendations": ordered,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }


def flatten_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(f"{key} {item}" for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value)
