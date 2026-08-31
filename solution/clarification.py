"""Candidate-derived split value, with explicit sparse-evidence fallback."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from solution.contracts import Candidate
from solution.question_policy import QUESTION_PRIORITY, QUESTION_TEXT, choose_question
from solution.state import COLOR_RE, MATERIAL_RE, SessionState


PATTERNS = {
    "material": MATERIAL_RE,
    "color": COLOR_RE,
    "size": re.compile(r"\b(wide|narrow|small|medium|large|xl|xxl)\b", re.I),
    "style": re.compile(r"\b(casual|formal|vintage|modern|slim|loose|fitted)\b", re.I),
    "use_case": re.compile(r"\b(hiking|running|walking|gym|winter|outdoor|work|wedding|travel)\b", re.I),
    "feature": re.compile(r"\b(waterproof|lightweight|breathable|stretch|pockets|adjustable|cushioned|washable)\b", re.I),
}


@dataclass(frozen=True)
class Clarification:
    attribute: str | None
    message: str
    reason: str
    overloaded: bool
    information_gain: float = 0.0
    coverage: float = 0.0


def _attribute_split(candidates: list[Candidate], attribute: str) -> tuple[float, float]:
    observed: list[set[str]] = []
    for candidate in candidates:
        if attribute == "budget":
            price = candidate.price
            values = {str(int(math.log2(max(1.0, price))))} if price is not None and math.isfinite(price) and price >= 0 else set()
        else:
            pattern = PATTERNS.get(attribute)
            values = {match.group(0).casefold() for match in pattern.finditer(candidate.searchable_text)} if pattern else set()
        if values:
            observed.append(values)
    if len(observed) < 2:
        return 0.0, 0.0
    counts = Counter(value for values in observed for value in values)
    best_entropy = 0.0
    for count in counts.values():
        probability = count / len(observed)
        if 0 < probability < 1:
            entropy = -probability * math.log2(probability) - (1 - probability) * math.log2(1 - probability)
            best_entropy = max(best_entropy, entropy)
    coverage = len(observed) / len(candidates)
    return best_entropy * coverage, coverage


def choose_adaptive_question(
    state: SessionState,
    candidates: list[Candidate],
    *,
    output_limit: int,
    fallback_used: bool,
) -> Clarification:
    overloaded = len(candidates) > max(10, output_limit * 2)
    if state.latest_turn >= 10:
        return Clarification(None, "Here are the closest matches for your current preferences.", "turn_budget_exhausted", overloaded)
    excluded = set(state.asked_attributes) | state.unconstrained_attributes | set(state.preferences)
    if fallback_used and not state.category and "category" not in excluded:
        return Clarification("category", "What type of product are you looking for?", "missing_category_after_no_match", False)
    if overloaded and not fallback_used:
        evidence = [(_attribute_split(candidates, attribute), attribute) for attribute in QUESTION_PRIORITY if attribute not in excluded]
        # Stable priority resolves equal evidence. Missing fields are not negative facts.
        evidence.sort(key=lambda item: -item[0][0])
        if evidence and evidence[0][0][0] > 0:
            (gain, coverage), attribute = evidence[0]
            return Clarification(attribute, QUESTION_TEXT[attribute], "candidate_information_gain", True, gain, coverage)
    attribute, message = choose_question(state)
    return Clarification(attribute, message, "sparse_evidence_fallback" if attribute else "attributes_exhausted", overloaded)
