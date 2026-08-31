from __future__ import annotations

import re

from solution.contracts import Candidate, PreferenceSlot
from solution.state import SessionState


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(value) if len(token) > 1}


def _budget_target(values: tuple[str, ...]) -> float | None:
    for value in values:
        match = re.search(r"(?:\$|\bunder\s+|\baround\s+\$?)\s*(\d+(?:\.\d+)?)", value, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def rank_candidates(
    candidates: list[Candidate],
    state: SessionState,
    limit: int,
    *,
    profile_priors: tuple[PreferenceSlot, ...] = (),
) -> list[Candidate]:
    if not candidates or limit <= 0:
        return []
    if not state.preferences and not profile_priors:
        return candidates[:limit]

    budget_slot = state.preferences.get("budget")
    budget = _budget_target(budget_slot.values if budget_slot else ())
    # Prepare per-request text once, not once for every catalog candidate.
    # No persistent cache or changed scoring arithmetic is needed.
    explicit_values = [
        (value.lower(), _tokens(value))
        for attribute, slot in state.preferences.items() if attribute != "budget"
        for value in slot.values
    ]
    prior_values = [
        _tokens(value)
        for slot in profile_priors
        if slot.attribute not in state.preferences and slot.attribute not in state.unconstrained_attributes
        for value in slot.values
    ]

    def score(candidate: Candidate) -> tuple:
        document = candidate.searchable_text.lower()
        document_tokens = _tokens(document)
        boost = 0.0
        for value_lower, value_tokens in explicit_values:
            if not value_tokens:
                continue
            overlap = len(value_tokens & document_tokens) / len(value_tokens)
            boost += 7.0 * overlap
            if value_lower in document:
                boost += 5.0
        if budget is not None and candidate.price is not None and budget > 0:
            distance = abs(candidate.price - budget) / budget
            boost += max(-2.0, 3.0 - 5.0 * distance)
        prior_boost = 0.0
        for value_tokens in prior_values:
            if value_tokens:
                prior_boost = max(prior_boost, len(value_tokens & document_tokens) / len(value_tokens))
        combined = boost - 0.35 * candidate.retrieval_rank + 0.6 * prior_boost
        if profile_priors:
            # Profile priors may resolve close choices, never outrank stronger
            # explicit evidence. Aggregate tags are not hard constraints.
            return (-boost, -combined, candidate.retrieval_rank, candidate.parent_asin)
        return (-combined, candidate.retrieval_rank, candidate.parent_asin)

    return sorted(candidates, key=score)[:limit]
