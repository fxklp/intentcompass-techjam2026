from __future__ import annotations

import json
import math
import re
import sqlite3
import weakref
from dataclasses import dataclass
from pathlib import Path

from solution.contracts import flatten_text


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
}


def terms(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


def float_or_none(value: object) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class ProductRecord:
    parent_asin: str
    searchable_text: str
    price: float | None
    categories: tuple[str, ...]


class FTS5CatalogIndex:
    """One in-memory catalog copy shared by all lexical candidate routes."""

    def __init__(self, catalog_path: str | Path) -> None:
        self.connection = sqlite3.connect(":memory:")
        self._finalizer = weakref.finalize(self, self.connection.close)
        self.products: dict[str, ProductRecord] = {}
        self.fallback_ids: list[str] = []
        self._build(Path(catalog_path))

    def close(self) -> None:
        self._finalizer()

    def _build(self, catalog_path: Path) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        batch: list[tuple[str, str, str, str, str, str, str]] = []
        popularity: list[tuple[float, float, str]] = []
        with catalog_path.open(encoding="utf-8") as handle:
            for line in handle:
                product = json.loads(line)
                parent_asin = str(product["parent_asin"])
                fields = (
                    flatten_text(product.get("title")),
                    flatten_text(product.get("categories")),
                    flatten_text(product.get("features")),
                    flatten_text(product.get("details")),
                    flatten_text(product.get("store")),
                    flatten_text(product.get("description")),
                )
                price = float_or_none(product.get("price"))
                rating = float_or_none(product.get("average_rating")) or 0.0
                rating_count = int(float_or_none(product.get("rating_number")) or 0)
                self.products[parent_asin] = ProductRecord(
                    parent_asin=parent_asin,
                    searchable_text=" ".join(fields),
                    price=price,
                    categories=tuple(str(value) for value in product.get("categories") or ()),
                )
                popularity.append((math.log1p(max(0, rating_count)) * rating, rating, parent_asin))
                batch.append((parent_asin, *fields))
                if len(batch) >= 1000:
                    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                    batch.clear()
        if batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
        self.connection.commit()
        popularity.sort(key=lambda item: (-item[0], -item[1], item[2]))
        self.fallback_ids = [item[2] for item in popularity]

    def search(
        self,
        expression: str,
        limit: int,
        weights: tuple[float, float, float, float, float, float],
    ) -> list[tuple[str, float]]:
        if not expression or limit <= 0:
            return []
        sql = (
            "SELECT parent_asin, bm25(products, 0.0, ?, ?, ?, ?, ?, ?) "
            "FROM products WHERE products MATCH ? ORDER BY 2 LIMIT ?"
        )
        try:
            rows = self.connection.execute(sql, (*weights, expression, int(limit))).fetchall()
        except sqlite3.Error:
            return []
        return [(str(parent_asin), float(score)) for parent_asin, score in rows]

    def candidate_data(self, parent_asin: str) -> ProductRecord:
        return self.products[parent_asin]


def or_expression(values: list[str] | tuple[str, ...], *, column: str | None = None) -> str:
    unique = list(dict.fromkeys(values))
    if not unique:
        return ""
    joined = " OR ".join(f'"{value}"' for value in unique)
    return f"{column} : ({joined})" if column else joined


def and_expression(values: list[str] | tuple[str, ...], *, column: str | None = None) -> str:
    unique = list(dict.fromkeys(values))
    if not unique:
        return ""
    joined = " AND ".join(f'"{value}"' for value in unique)
    return f"{column} : ({joined})" if column else joined
