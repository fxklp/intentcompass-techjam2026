"""Explicit bounded workflow decisions; no evaluator or target information."""
from __future__ import annotations

import re
from dataclasses import dataclass

from solution.state import SessionState


REJECTION_RE = re.compile(r"not (?:quite |really )?right|none of (?:these|those)|something else", re.I)
HARD_ATTRIBUTES = frozenset({"material", "color", "size", "brand", "budget", "feature"})
GENERIC_CATEGORIES = frozenset({"anything", "something", "item", "items", "product", "products", "clothes", "clothing"})


@dataclass(frozen=True)
class WorkflowPlan:
    route: str
    pool_limit: int
    recovery: bool
    reason: str
    skip_expensive: bool = False


@dataclass
class WorkflowState:
    rejected_turns: int = 0
    overloaded: bool = False
    last_fallback: bool = False

    def plan(self, state: SessionState, message: str, *, changed: bool) -> WorkflowPlan:
        if changed:
            self.rejected_turns = 0
            self.overloaded = False
            self.last_fallback = False
        if REJECTION_RE.search(message):
            self.rejected_turns += 1
        buying = bool(set(state.preferences) & HARD_ATTRIBUTES)
        route = "buying" if buying else "browsing"
        category = (state.category or "").strip().casefold()
        broad_language = bool(re.search(
            r"\b(?:anything|something|not sure|still exploring|just browsing|surprise me)\b",
            message,
            re.I,
        ))
        if not buying and (not category or category in GENERIC_CATEGORIES) and broad_language:
            return WorkflowPlan("browsing", 0, False, "pre_retrieval_cutoff", True)
        if self.last_fallback or self.rejected_turns >= 2:
            # Query broadens, explicit preferences still apply at ranking time.
            return WorkflowPlan(route, 80, True, "recover_after_miss_or_rejection")
        if self.overloaded:
            return WorkflowPlan(route, 40, False, "cutoff_and_clarify")
        return WorkflowPlan(route, 50 if buying else 80, False, "precise" if buying else "explore")
