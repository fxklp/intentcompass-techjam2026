"""Session-local recovery after explicit rejection or a repeated final turn."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re

from solution.constraint_semantics import excluded_term, contradicts_exclusion, upper_budget
from solution.field_evidence import FieldEvidence
from solution.question_policy import choose_question
from solution.retrieval.index import terms
from solution.state import OVERRIDE_RE
from solution.workflow import REJECTION_RE

NO_ADDITIONAL = re.compile(r"\b(?:no|don't have an?|do not have an?)\s+(?:additional|further|extra)\s+(?:preference|requirement)", re.I)
WEIGHTS = (2, 1, 2, 3, 3, 1, 0, 0, .5, 0, 1, 20)


def tokens(text):
    return tuple(re.findall(r"[a-z0-9]+", text.casefold()))


def grams(sequence, n):
    return set(zip(*(sequence[i:] for i in range(n)))) if len(sequence) >= n else set()


def coverage(wanted, observed):
    return len(wanted & observed) / len(wanted) if wanted else 0.0


def features(candidate, state, primary, category, position, max_bm25):
    values = [v for key, slot in state.preferences.items() if key != "budget"
              for v in slot.values if v and not excluded_term(v)]
    queries = [tokens(v) for v in values if tokens(v)]
    p = tokens(primary)
    d = tokens(candidate.searchable_text)
    psets = [grams(p, n) for n in (1, 2, 3)]
    dset = set(d)
    normalized_p = " " + " ".join(p) + " "
    normalized_d = " " + " ".join(d) + " "
    per_query = [[coverage(grams(q, n), psets[n-1]) for n in (1, 2, 3)] for q in queries]
    mean = lambda items: sum(items) / len(items) if items else 0.0
    budget_slot = state.preferences.get("budget")
    cap = upper_budget(budget_slot.values) if budget_slot else None
    budget = (max(-1.0, 1 - max(0, candidate.price - cap) / cap)
              if cap and candidate.price is not None and math.isfinite(candidate.price) else 0.0)
    exclusions = [x for slot in state.preferences.values() for v in slot.values
                  if (x := excluded_term(v))]
    return [coverage(set(terms(state.category or "")), set(terms(category))),
            *[mean([row[i] for row in per_query]) for i in range(3)],
            mean([float(" " + " ".join(q) + " " in normalized_p) for q in queries]),
            min((row[0] for row in per_query), default=0.0),
            mean([coverage(set(q), dset) for q in queries]),
            mean([float(" " + " ".join(q) + " " in normalized_d) for q in queries]),
            1 / math.log2(position + 2),
            candidate.retrieval_score / max_bm25 if max_bm25 > 0 else 0.0,
            budget, -float(any(contradicts_exclusion(candidate.searchable_text, x) for x in exclusions))]


@dataclass
class RejectionHistory:
    signature: tuple = ()
    shown: tuple[str, ...] = ()
    rejected: set[str] = field(default_factory=set)


def signature(state):
    return state.category, tuple((key, slot.values) for key, slot in sorted(state.preferences.items()))


class TerminalRecovery:
    def __init__(self, index, mode="terminal"):
        if mode not in {"terminal", "lastchance"}:
            raise ValueError("invalid terminal recovery mode")
        self.index, self.mode = index, mode
        self.sessions = {}
        self.fields = None
        self.last_active = False

    def reset(self, session_id):
        self.sessions.pop(session_id, None)

    def close(self):
        self.sessions.clear()
        if self.fields:
            self.fields.close()
            self.fields = None

    def pool_limit(self, state, message, top_k):
        old = self.sessions.get(state.session_id)
        if not top_k or old is None or old.signature != signature(state) or OVERRIDE_RE.search(message):
            return 50
        terminal = choose_question(state)[0] is None and REJECTION_RE.search(message)
        final = self.mode == "lastchance" and state.latest_turn >= 10 and (NO_ADDITIONAL.search(message) or REJECTION_RE.search(message))
        return 200 if old.rejected or terminal or final else 50

    def reorder(self, candidates, state, baseline, message, top_k, *, fallback=False):
        limit = max(0, min(10, int(top_k)))
        current = signature(state)
        history = self.sessions.setdefault(state.session_id, RejectionHistory())
        same = history.signature == current and not OVERRIDE_RE.search(message)
        if not same:
            history.shown = ()
            history.rejected.clear()
        terminal = same and choose_question(state)[0] is None and REJECTION_RE.search(message)
        repeated = bool(history.shown) and tuple(c.parent_asin for c in baseline[:limit]) == history.shown
        final = (self.mode == "lastchance" and state.latest_turn >= 10 and same and repeated
                 and (NO_ADDITIONAL.search(message) or REJECTION_RE.search(message)))
        if not fallback and (terminal or final):
            history.rejected.update(history.shown)
        self.last_active = bool(history.rejected) and not fallback and limit > 0
        ranked = baseline
        if self.last_active:
            ranked = [c for c in baseline if c.parent_asin not in history.rejected] or baseline
            if state.preferences:
                if self.fields is None:
                    self.fields = FieldEvidence(self.index.connection)
                fields = self.fields.get([c.parent_asin for c in candidates])
                maximum = max((c.retrieval_score for c in candidates), default=0)
                positions = {c.parent_asin: i for i, c in enumerate(ranked)}
                def key(c):
                    row = features(c, state, fields[c.parent_asin],
                                   " ".join(self.index.products[c.parent_asin].categories),
                                   positions[c.parent_asin], maximum)
                    return -sum(w*x for w, x in zip(WEIGHTS, row))
                ranked = sorted(ranked, key=key)
        history.signature = current
        history.shown = tuple(c.parent_asin for c in ranked[:limit])
        return ranked
