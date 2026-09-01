"""Bounded catalog-only memoization, never conversation or target state."""
from collections import OrderedDict


class QueryCache:
    def __init__(self, capacity: int = 128) -> None:
        self.capacity = max(0, capacity)
        self.rows = OrderedDict()

    def get(self, key: tuple, compute) -> list:
        if key in self.rows:
            self.rows.move_to_end(key)
            return list(self.rows[key])
        result = compute()
        if self.capacity:
            self.rows[key] = tuple(result)
            if len(self.rows) > self.capacity:
                self.rows.popitem(last=False)
        return list(result)

    def clear(self) -> None:
        self.rows.clear()
