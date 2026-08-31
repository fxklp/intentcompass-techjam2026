"""Three-valued evidence for explicit Buying constraints.

Only visible parent-product metadata is used.  Absence is ``unknown`` and is
never converted into a match.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

from solution.constraint_semantics import excluded_term, upper_budget
from solution.contracts import Candidate
from solution.state import SessionState


Evidence = Literal["satisfied", "conflict", "unknown"]
TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
KNOWN_VALUES = {
    "color": frozenset("black white blue red pink green brown gray grey purple yellow orange beige gold silver".split()),
    "material": frozenset("cotton polyester nylon leather wool spandex silk rayon linen fabric suede denim".split()),
    "size": frozenset("xs small medium large xl xxl wide narrow".split()),
}


@dataclass(frozen=True)
class ConstraintReport:
    satisfied: int
    conflict: int
    unknown: int
    retained_unknown: bool

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "satisfied": self.satisfied,
            "conflict": self.conflict,
            "unknown": self.unknown,
            "retained_unknown": self.retained_unknown,
        }


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in TOKEN_RE.findall(text)}


def value_evidence(candidate: Candidate, attribute: str, value: str) -> Evidence:
    """Return evidence without treating missing metadata as satisfaction."""
    document = candidate.searchable_text.casefold()
    document_tokens = _tokens(document)
    negative = excluded_term(value)
    if attribute == "budget":
        ceiling = upper_budget((value,))
        if ceiling is None or candidate.price is None or not math.isfinite(candidate.price):
            return "unknown"
        return "satisfied" if candidate.price <= ceiling else "conflict"

    wanted = _tokens(negative or value)
    if not wanted:
        return "unknown"
    vocabulary = KNOWN_VALUES.get(attribute)
    observed = document_tokens & vocabulary if vocabulary else set()
    desired = wanted & vocabulary if vocabulary else wanted
    present = bool(desired & document_tokens) if vocabulary and desired else (
        wanted <= document_tokens or (negative or value).casefold() in document
    )
    if negative:
        if present:
            return "conflict"
        return "satisfied" if observed else "unknown"
    if present:
        return "satisfied"
    if observed:
        return "conflict"
    # Features/styles/brands have open vocabularies.  Missing text is unknown,
    # not a fabricated conflict or match.
    return "unknown"


def candidate_evidence(candidate: Candidate, state: SessionState) -> Evidence:
    statuses = [
        value_evidence(candidate, attribute, value)
        for attribute, slot in state.preferences.items()
        for value in slot.values
    ]
    if not statuses:
        return "unknown"
    if "conflict" in statuses:
        return "conflict"
    if all(status == "satisfied" for status in statuses):
        return "satisfied"
    return "unknown"


def filter_buying_candidates(
    candidates: list[Candidate], state: SessionState
) -> tuple[list[Candidate], ConstraintReport]:
    """Exclude confirmed conflicts; rank confirmed matches before unknowns.

    Unknown parent metadata is retained as an explicit relaxation because the
    frozen catalog is parent-level and sparse.  The report makes that relaxation
    observable to callers and tests.
    """
    groups: dict[Evidence, list[Candidate]] = {
        "satisfied": [], "conflict": [], "unknown": []
    }
    for candidate in candidates:
        groups[candidate_evidence(candidate, state)].append(candidate)
    retained = [*groups["satisfied"], *groups["unknown"]]
    # An all-conflict pool is an honest no-solution result; do not silently
    # restore known violations.
    report = ConstraintReport(
        len(groups["satisfied"]), len(groups["conflict"]), len(groups["unknown"]),
        bool(groups["unknown"]),
    )
    return retained, report
