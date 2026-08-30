from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


RouteHint = Literal["auto", "buying", "browsing"]


@dataclass(frozen=True)
class RetrievalConstraint:
    attribute: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalRequest:
    """Label-free inputs available at the candidate retrieval boundary."""

    query: str
    limit: int
    route_hint: RouteHint = "auto"
    category: str | None = None
    constraints: tuple[RetrievalConstraint, ...] = field(default_factory=tuple)
    turn: int = 1


@dataclass(frozen=True)
class RouteEvidence:
    route: str
    rank: int
    score: float


@dataclass(frozen=True)
class Candidate:
    parent_asin: str
    retrieval_rank: int
    retrieval_score: float
    searchable_text: str
    price: float | None = None
    categories: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[RouteEvidence, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievalTrace:
    selected_path: Literal["baseline", "buying", "browsing"]
    reason_codes: tuple[str, ...]
    routes: tuple[str, ...]
    route_candidate_counts: tuple[tuple[str, int], ...]
    query_terms: tuple[str, ...]
    expanded_terms: tuple[str, ...] = field(default_factory=tuple)
    fallback_used: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_path": self.selected_path,
            "reason_codes": list(self.reason_codes),
            "routes": list(self.routes),
            "route_candidate_counts": dict(self.route_candidate_counts),
            "query_terms": list(self.query_terms),
            "expanded_terms": list(self.expanded_terms),
            "fallback_used": self.fallback_used,
        }


@dataclass(frozen=True)
class RetrievalResult:
    candidates: tuple[Candidate, ...]
    trace: RetrievalTrace


class CandidateRetriever(Protocol):
    """Stable experiment boundary; implementations are offline and label-free."""

    def search(self, request: RetrievalRequest) -> RetrievalResult: ...

    def close(self) -> None: ...
