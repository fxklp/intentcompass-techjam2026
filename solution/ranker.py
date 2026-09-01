from __future__ import annotations

import re
import os

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
    primary_fields: dict[str, str] | None = None,
    policy: str | None = None,
) -> list[Candidate]:
    if not candidates or limit <= 0:
        return []
    if not state.preferences and not profile_priors:
        return candidates[:limit]

    policy = policy or os.environ.get("INTENTCOMPASS_OFFLINE_RANKING", "baseline")
    if policy not in {"baseline", "constraints", "field_bonus", "field_groups", "field_top10"}:
        raise ValueError("unknown offline ranking policy")
    from solution.constraint_semantics import excluded_term, upper_budget, contradicts_exclusion
    use_constraints = policy != "baseline"

    budget_slot = state.preferences.get("budget")
    budget = _budget_target(budget_slot.values if budget_slot else ())
    upper = upper_budget(budget_slot.values) if use_constraints and budget_slot else None
    if upper is not None:
        budget = upper
    # Prepare per-request text once, not once for every catalog candidate.
    # No persistent cache or changed scoring arithmetic is needed.
    explicit_values = [
        (value.lower(), _tokens(value))
        for attribute, slot in state.preferences.items() if attribute != "budget"
        for value in slot.values
    ]
    exclusions = [term for value, _ in explicit_values if (term := excluded_term(value))] if use_constraints else []
    if exclusions:
        explicit_values = [(value, tokens) for value, tokens in explicit_values if not excluded_term(value)]
    groups = [[value.casefold() for value in slot.values if value and not excluded_term(value)]
              for attr, slot in state.preferences.items() if attr != "budget"] if primary_fields else []
    groups = [group for group in groups if group]
    prior_values = [
        _tokens(value)
        for slot in profile_priors
        if slot.attribute not in state.preferences and slot.attribute not in state.unconstrained_attributes
        for value in slot.values
    ]

    baseline_keys = {}

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
        if exclusions:
            boost -= 20.0 * sum(contradicts_exclusion(document, term) for term in exclusions)
        if budget is not None and candidate.price is not None and budget > 0:
            distance = max(0.0, candidate.price - upper) / upper if upper is not None and upper > 0 else abs(candidate.price - budget) / budget
            boost += max(-2.0, 3.0 - 5.0 * distance)
        prior_boost = 0.0
        for value_tokens in prior_values:
            if value_tokens:
                prior_boost = max(prior_boost, len(value_tokens & document_tokens) / len(value_tokens))
        combined = boost - 0.35 * candidate.retrieval_rank + 0.6 * prior_boost
        if policy == "field_top10":
            baseline_keys[candidate.parent_asin] = (-boost, -combined, candidate.retrieval_rank, candidate.parent_asin) if profile_priors else (-combined, candidate.retrieval_rank, candidate.parent_asin)
        primary = (primary_fields or {}).get(candidate.parent_asin, "")
        if policy == "field_bonus" and groups:
            values = [value for group in groups for value in group]
            combined += 3.0 * sum(value in primary for value in values) / len(values)
        if policy in {"field_groups", "field_top10"} and groups:
            return (-sum(all(value in primary for value in group) for group in groups), -combined, candidate.retrieval_rank, candidate.parent_asin)
        if profile_priors:
            # Profile priors may resolve close choices, never outrank stronger
            # explicit evidence. Aggregate tags are not hard constraints.
            return (-boost, -combined, candidate.retrieval_rank, candidate.parent_asin)
        return (-combined, candidate.retrieval_rank, candidate.parent_asin)

    if policy == "field_top10":
        keys = {c.parent_asin: score(c) for c in candidates}
        base = sorted(candidates, key=lambda c: baseline_keys[c.parent_asin])
        return [*sorted(base[:10], key=lambda c: keys[c.parent_asin]), *base[10:]][:limit]
    return sorted(candidates, key=score)[:limit]
