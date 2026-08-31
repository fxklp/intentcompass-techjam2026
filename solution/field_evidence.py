"""Read primary catalog fields from the existing in-memory FTS table."""
from __future__ import annotations

import sqlite3
from collections import OrderedDict


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
