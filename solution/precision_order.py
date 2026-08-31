"""Conservative full-phrase ordering within the existing same-category Top10."""
from __future__ import annotations

from itertools import groupby

from solution.constraint_semantics import excluded_term
from solution.field_evidence import FieldEvidence
from solution.retrieval.index import terms
from solution.terminal_recovery import tokens

VARIANTS = ("off", "joined", "separate")
DEFAULT = "off"


def matches_all(queries: list[tuple[str, ...]], primary: str, *, separate: bool) -> bool:
    """Each requirement may match a different field; never infer missing values."""
    fields = primary.split(" \n ") if separate else [primary]
    normalized = [" " + " ".join(tokens(field)) + " " for field in fields]
    return all(any(" " + " ".join(query) + " " in field for field in normalized)
               for query in queries)


class PrecisionOrder:
    def __init__(self, index, variant: str):
        if variant not in VARIANTS or variant == "off":
            raise ValueError("invalid precision ordering variant")
        self.index, self.variant = index, variant
        self.fields = None
        self.rank_changes = 0

    def close(self):
        if self.fields is not None:
            self.fields.close()

    def reorder(self, candidates, state, *, fallback=False):
        if (fallback or len(candidates) < 2 or "budget" in state.preferences
                or any(excluded_term(v) for slot in state.preferences.values() for v in slot.values)):
            return candidates
        queries = [tokens(v) for slot in state.preferences.values() for v in slot.values if v and tokens(v)]
        if not queries or not any(len(q) >= 2 for q in queries):
            return candidates
        head = candidates[:10]
        if self.fields is None:
            self.fields = FieldEvidence(self.index.connection)
        primary = self.fields.get([c.parent_asin for c in head])
        matching = {c.parent_asin for c in head if matches_all(
            queries, primary[c.parent_asin], separate=self.variant == "separate")}
        wanted = set(terms(state.category or ""))

        def category(candidate):
            observed = set(terms(" ".join(self.index.products[candidate.parent_asin].categories)))
            return len(wanted & observed)

        result = []
        for _, group in groupby(head, key=category):
            result.extend(sorted(group, key=lambda c: c.parent_asin not in matching))
        self.rank_changes += int(result != head)
        return [*result, *candidates[10:]]
