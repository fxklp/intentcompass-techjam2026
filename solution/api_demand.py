"""Target-blind API gating and bounded, session-local memoization."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from solution.contracts import Candidate
from solution.semantic import SemanticResult, safe_context


DEMAND_VARIANTS = {"demand20": (20, 480, 2), "demand40": (40, 320, 2), "demand20early": (20, 480, 1)}


def evidence_text(text: str, context: dict, limit: int) -> str:
    """Keep the title prefix and explicit-constraint evidence, not just a prefix."""
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    parts = [clean[:160]]
    lower = clean.lower()
    for values in safe_context(context)["explicit"].values():
        for value in values:
            position = lower.find(value.lower())
            if position >= 160:
                snippet = clean[max(160, position - 24):position + len(value) + 64]
                if snippet not in parts:
                    parts.append(snippet)
    parts.append(clean[160:limit])
    return " | ".join(parts)[:limit]


@dataclass
class DemandState:
    """Owned by AdaptiveSession, so reset and interleaved sessions stay isolated."""

    attempts: int = 0
    key: str | None = None
    ordered_ids: tuple[str, ...] = ()

    def rerank(self, model, candidates: list[Candidate], context: dict) -> SemanticResult:
        zero = {"prompt_tokens": 0, "completion_tokens": 0}
        safe = safe_context(context)
        supplied = sum(bool(values) for key, values in safe["explicit"].items() if key != "category")
        if supplied < getattr(model, "minimum_attributes", 2):
            return SemanticResult(candidates, "demand_insufficient_information", zero)
        # Full context and candidate bytes, including order, affect the key.
        # No answer labels, session IDs, global response cache or persisted memo.
        material = {"context": safe, "candidates": [
            [c.parent_asin, c.searchable_text, c.price] for c in candidates
        ]}
        key = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if key == self.key:
            by_id = {c.parent_asin: c for c in candidates}
            return SemanticResult([by_id[i] for i in self.ordered_ids], "demand_exact_cache", zero)
        if self.attempts >= 3:
            return SemanticResult(candidates, "demand_session_call_limit", zero)
        result = model.rerank(candidates, context)
        self.attempts += int(result.attempted)
        if result.reason == "model_ranked":
            self.key = key
            self.ordered_ids = tuple(c.parent_asin for c in result.candidates)
        return result
