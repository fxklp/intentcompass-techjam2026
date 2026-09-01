"""Accepted offline title tie-break and bounded clarification policy.

Uses observable dialogue/catalog evidence only. This is the selected TASK-014
combination, without the unselected research variants or unused pool statistics.
"""
from __future__ import annotations

from itertools import groupby

from solution.constraint_semantics import excluded_term
from solution.field_evidence import FieldEvidence
from solution.precision_order import matches_all
from solution.question_policy import QUESTION_TEXT, choose_question
from solution.retrieval.index import terms
from solution.state import NO_PREFERENCE_RE, OVERRIDE_RE
from solution.terminal_recovery import tokens

DEFAULT = "on"
VARIANTS = ("off", "on")


class FinalPolicy:
    def __init__(self, index, precision):
        self.index, self.precision = index, precision
        self.streaks: dict[str, int] = {}
        self.rank_changes = self.question_changes = 0

    def reset(self, session_id):
        self.streaks.pop(session_id, None)

    def close(self):
        self.streaks.clear()  # PrecisionOrder owns the shared field cache.

    def primary(self, candidates):
        if self.precision.fields is None:
            self.precision.fields = FieldEvidence(self.index.connection)
        return self.precision.fields.get([c.parent_asin for c in candidates])

    def reorder(self, candidates, state, *, fallback=False):
        if (fallback or len(candidates) < 2 or "budget" in state.preferences
                or any(excluded_term(v) for slot in state.preferences.values() for v in slot.values)):
            return candidates
        queries = [tokens(v) for slot in state.preferences.values() for v in slot.values if tokens(v)]
        if not queries:
            return candidates
        head = candidates[:10]
        texts = self.primary(head)
        wanted = set(terms(state.category or ""))
        title = {c.parent_asin: frozenset(i for i, q in enumerate(queries) if matches_all(
            [q], texts[c.parent_asin].split(" \n ")[0], separate=True)) for c in head}

        def group_key(candidate):
            category = set(terms(" ".join(self.index.products[candidate.parent_asin].categories)))
            return len(wanted & category), matches_all(queries, texts[candidate.parent_asin], separate=True)

        def better(left, right):
            return (abs(left.retrieval_rank-right.retrieval_rank) <= 3
                    and title[left.parent_asin] > title[right.parent_asin])

        ranked = []
        # Contiguous groups preserve prior category and full-phrase decisions.
        # Strict set inclusion leaves tied/incomparable evidence in input order.
        for _, group in groupby(head, key=group_key):
            items = list(group)
            for i in range(1, len(items)):
                j = i
                while j and better(items[j], items[j-1]):
                    items[j-1], items[j] = items[j], items[j-1]
                    j -= 1
            ranked.extend(items)
        self.rank_changes += ranked != head
        return [*ranked, *candidates[10:]]

    def question(self, state, candidates, message, *, fallback=False, output_limit=10):
        baseline = choose_question(state)
        unchanged = NO_PREFERENCE_RE.search(message) and not OVERRIDE_RE.search(message)
        streak = self.streaks.get(state.session_id, 0)+1 if unchanged else 0
        self.streaks[state.session_id] = streak
        if (state.latest_turn >= 10 or fallback or output_limit <= 0 or len(candidates) < 2
                or baseline[0] in {None, "feature", "other"}):
            return baseline
        excluded = set(state.asked_attributes) | state.unconstrained_attributes | set(state.preferences)
        if streak >= 3 and "other" not in excluded:
            self.question_changes += 1
            return "other", QUESTION_TEXT["other"]
        return baseline
