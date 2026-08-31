"""Narrow explicit constraints; do not reinterpret ambiguous compound prose."""
from __future__ import annotations

import re

from solution.state import COLOR_RE, MATERIAL_RE


UPPER_BUDGET_RE = re.compile(r"\b(?:under|below|less than|at most|up to|max(?:imum)?(?: budget)?)\s*\$?\s*(\d+(?:\.\d+)?)\b", re.I)
NEGATIVE_RE = re.compile(r"^(?:not|no|avoid|exclude|without)\s+([a-z]+)$", re.I)


def excluded_term(value: str) -> str | None:
    match = NEGATIVE_RE.fullmatch(value.strip().rstrip(".!"))
    if not match:
        return None
    term = match.group(1).casefold()
    return term if MATERIAL_RE.fullmatch(term) or COLOR_RE.fullmatch(term) else None


def upper_budget(values: tuple[str, ...]) -> float | None:
    for value in values:
        match = UPPER_BUDGET_RE.search(value)
        if match:
            return float(match.group(1))
    return None


def contradicts_exclusion(document: str, term: str) -> bool:
    # Explicit "not cotton" / "cotton-free" is not positive cotton evidence.
    text = re.sub(rf"\b(?:not|no|without)\s+{re.escape(term)}\b|\b{re.escape(term)}[- ]free\b", "", document, flags=re.I)
    return bool(re.search(rf"\b{re.escape(term)}\b", text, re.I))
