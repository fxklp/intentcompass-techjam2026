from __future__ import annotations

import json
import re
import sqlite3
import weakref
from pathlib import Path

from solution.contracts import AgentResponse, Candidate, RetrievalRequest, flatten_text
from solution.question_policy import choose_question
from solution.ranker import rank_candidates
from solution.state import SessionState


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
}


def _terms(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


class _BaselineBM25Index:
    """Internal compatibility bridge until the owned retrieval lane is integrated."""

    def __init__(self, catalog_path: Path) -> None:
        self.connection = sqlite3.connect(":memory:")
        self._finalizer = weakref.finalize(self, self.connection.close)
        self.products: dict[str, tuple[str, float | None, float, int]] = {}
        self.fallback_ids: list[str] = []
        self._build(catalog_path)

    def close(self) -> None:
        """Release the in-memory FTS index; safe to call more than once."""
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
                text = " ".join(fields)
                price = _float_or_none(product.get("price"))
                rating = _float_or_none(product.get("average_rating")) or 0.0
                rating_count = int(_float_or_none(product.get("rating_number")) or 0)
                self.products[parent_asin] = (text, price, rating, rating_count)
                popularity.append((math_log1p(rating_count) * rating, rating, parent_asin))
                batch.append((parent_asin, *fields))
                if len(batch) >= 1000:
                    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                    batch.clear()
        if batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
        self.connection.commit()
        popularity.sort(key=lambda item: (-item[0], -item[1], item[2]))
        self.fallback_ids = [item[2] for item in popularity]

    def search(self, request: RetrievalRequest) -> list[Candidate]:
        limit = max(0, int(request.limit))
        unique_terms = list(dict.fromkeys(_terms(request.query)))[:40]
        if limit == 0:
            return []
        rows: list[tuple[str, float]] = []
        if unique_terms:
            expression = " OR ".join(f'"{term}"' for term in unique_terms)
            try:
                rows = self.connection.execute(
                    "SELECT parent_asin, bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0) "
                    "FROM products WHERE products MATCH ? ORDER BY 2 LIMIT ?",
                    (expression, limit),
                ).fetchall()
            except sqlite3.Error:
                rows = []
        if not rows:
            rows = [(parent_asin, 0.0) for parent_asin in self.fallback_ids[:limit]]
        return [self._candidate(parent_asin, rank, score) for rank, (parent_asin, score) in enumerate(rows)]

    def _candidate(self, parent_asin: str, rank: int, score: float) -> Candidate:
        text, price, _, _ = self.products[parent_asin]
        return Candidate(
            parent_asin=parent_asin,
            retrieval_rank=rank,
            retrieval_score=-float(score),
            searchable_text=text,
            price=price,
        )


def _float_or_none(value: object) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def math_log1p(value: int) -> float:
    # Kept local so the offline fallback has no optional dependency.
    import math

    return math.log1p(max(0, value))


class Agent:
    """Deterministic offline orchestration for state, ranking, and questions."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog_path = Path(catalog_path)
        self._retriever = _BaselineBM25Index(self.catalog_path)
        self._sessions: dict[str, SessionState] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        normalized_id = str(session_id)
        self._sessions[normalized_id] = SessionState.create(normalized_id, user_profile)

    def close(self) -> None:
        self._retriever.close()

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        normalized_id = str(session_id)
        if normalized_id not in self._sessions:
            raise RuntimeError("reset must be called before respond")
        state = self._sessions[normalized_id]
        state.apply_user_message(str(user_message), int(turn))
        output_limit = max(0, min(10, int(top_k)))
        request = RetrievalRequest(
            query=state.retrieval_query(turn),
            limit=max(50, output_limit * 5),
        )
        candidates = self._retriever.search(request)
        ranked = rank_candidates(candidates, state, output_limit)
        ask_attribute, message = choose_question(state)
        state.mark_asked(ask_attribute)
        return AgentResponse(
            message=message,
            ask_attribute=ask_attribute,
            recommendations=tuple(candidate.parent_asin for candidate in ranked),
        ).to_payload()
