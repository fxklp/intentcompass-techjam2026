"""Read primary catalog fields from the existing in-memory FTS table."""
from __future__ import annotations

import sqlite3
from collections import OrderedDict
from solution.constraint_semantics import excluded_term


class FieldEvidence:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.rowids = {str(identifier): rowid for rowid, identifier in connection.execute("SELECT rowid, parent_asin FROM products")}
        self.cache: OrderedDict[str, str] = OrderedDict()

    def get(self, identifiers: list[str]) -> dict[str, str]:
        missing = [identifier for identifier in dict.fromkeys(identifiers) if identifier not in self.cache and identifier in self.rowids]
        fetched = {}
        if missing:
            placeholders = ",".join("?" for _ in missing)
            rows = self.connection.execute(f"SELECT parent_asin, title, features, details FROM products WHERE rowid IN ({placeholders})", [self.rowids[i] for i in missing])
            fetched = {str(row[0]): " \n ".join(str(v or "") for v in row[1:]).casefold() for row in rows}
        result = {}
        for identifier in identifiers:
            text = self.cache.get(identifier, fetched.get(identifier, ""))
            result[identifier] = text
            self.cache[identifier] = text
            self.cache.move_to_end(identifier)
            while len(self.cache) > 256:
                self.cache.popitem(last=False)
        return result

    def close(self):
        self.cache.clear()
        self.rowids.clear()


def refine_by_dominance(candidates, state, fields):
    """Only move a strict evidence superset across an adjacent subset."""
    values = [v.casefold() for key, slot in state.preferences.items() if key != "budget"
              for v in slot.values if v and not excluded_term(v)]
    if not values:
        return candidates[:]
    head = candidates[:10]
    evidence = {c.parent_asin: frozenset(i for i,v in enumerate(values) if v in fields.get(c.parent_asin,"")) for c in head}
    # Stable insertion; incomparable evidence is never crossed, no arbitrary
    # scalar weights or profile priors can override a known explicit match.
    for i in range(1,len(head)):
        j=i
        while j>0 and evidence[head[j].parent_asin] > evidence[head[j-1].parent_asin]:
            head[j-1],head[j]=head[j],head[j-1]
            j-=1
    return [*head,*candidates[10:]]
