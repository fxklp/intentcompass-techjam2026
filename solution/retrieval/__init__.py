"""Deterministic candidate retrieval implementations for isolated experiments."""

from solution.retrieval.baseline import BaselineFTS5Retriever
from solution.retrieval.contracts import (
    Candidate,
    CandidateRetriever,
    RetrievalConstraint,
    RetrievalRequest,
    RetrievalResult,
    RetrievalTrace,
)
from solution.retrieval.dual_route import DualRouteInMemoryRetriever

__all__ = [
    "BaselineFTS5Retriever",
    "Candidate",
    "CandidateRetriever",
    "DualRouteInMemoryRetriever",
    "RetrievalConstraint",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalTrace",
]
