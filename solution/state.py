from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from solution.contracts import ALLOWED_ATTRIBUTES, PreferenceSlot


NO_PREFERENCE_RE = re.compile(
    r"\b(?:no|don't|do not|without)\b.{0,35}\b(?:preference|care|matter|requirement)\b"
    r"|\b(?:anything|either)\s+is\s+fine\b",
    re.IGNORECASE,
)
OVERRIDE_RE = re.compile(
    r"\b(?:actually|instead|change|replace|ignore\s+my\s+earlier|rather\s+than|make\s+it)\b",
    re.IGNORECASE,
)
CATEGORY_RE = re.compile(
    r"\blooking\s+for\s+(.+?)(?:\.|,\s*(?:but|with)|\s+but\b|\s+with\b|$)",
    re.IGNORECASE,
)
EXPLICIT_VALUE_RE = re.compile(
    r"(?:what\s+i\s+need\s+is|key\s+requirement\s+is|what\s+matters\s+is)\s*:\s*(.+)$",
    re.IGNORECASE,
)
COLOR_RE = re.compile(
    r"\b(black|white|blue|red|pink|green|brown|gray|grey|purple|yellow|orange|beige|gold|silver)\b",
    re.IGNORECASE,
)
MATERIAL_RE = re.compile(
    r"\b(cotton|polyester|nylon|leather|wool|spandex|silk|rayon|linen|fabric|suede|denim)\b",
    re.IGNORECASE,
)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -;,.")


def classify_preference(value: str, fallback: str = "feature") -> str:
    lowered = value.lower()
    if re.search(r"(?:\$|\bunder\b|\bless\s+than\b|\bbudget\b|\bprice\b)\s*\$?\d", lowered):
        return "budget"
    if MATERIAL_RE.search(value):
        return "material"
    if COLOR_RE.search(value) or "color" in lowered or "colour" in lowered:
        return "color"
    if re.search(r"\b(size|sizing|width|wide|narrow|small|medium|large|\d{1,2}(?:\.5)?)\b", lowered):
        return "size"
    if re.search(r"\b(style|fit|sleeve|neck|casual|formal|vintage|modern)\b", lowered):
        return "style"
    if re.search(r"\b(hiking|running|walking|gym|winter|outdoor|work|wedding|travel)\b", lowered):
        return "use_case"
    if re.search(r"\b(brand|maker|store|manufacturer)\b", lowered):
        return "brand"
    return fallback if fallback in ALLOWED_ATTRIBUTES else "feature"


def _preference_values(message: str) -> tuple[str, ...]:
    explicit = EXPLICIT_VALUE_RE.search(message)
    value = explicit.group(1) if explicit else message
    return tuple(cleaned for part in value.split(";") if (cleaned := _clean(part)))


@dataclass
class SessionState:
    session_id: str
    user_profile: dict
    category: str | None = None
    preferences: dict[str, PreferenceSlot] = field(default_factory=dict)
    asked_attributes: list[str] = field(default_factory=list)
    unconstrained_attributes: set[str] = field(default_factory=set)
    last_asked_attribute: str | None = None
    first_message: str | None = None
    latest_turn: int = 0

    @classmethod
    def create(cls, session_id: str, user_profile: dict) -> "SessionState":
        return cls(session_id=session_id, user_profile=copy.deepcopy(user_profile))

    def mark_asked(self, attribute: str | None) -> None:
        if attribute is None:
            self.last_asked_attribute = None
            return
        if attribute not in self.asked_attributes:
            self.asked_attributes.append(attribute)
        self.last_asked_attribute = attribute

    def apply_user_message(self, message: str, turn: int, *, flexible: bool = False) -> None:
        text = _clean(str(message))
        self.latest_turn = int(turn)
        if self.first_message is None:
            self.first_message = text

        category_match = CATEGORY_RE.search(text)
        if category_match:
            if flexible and self.category and OVERRIDE_RE.search(text):
                self.preferences.clear()
            self.category = _clean(category_match.group(1))

        if NO_PREFERENCE_RE.search(text):
            attribute = self._named_attribute(text) or self.last_asked_attribute
            if attribute:
                self.preferences.pop(attribute, None)
                self.unconstrained_attributes.add(attribute)
            return

        is_override = bool(OVERRIDE_RE.search(text))
        values = _preference_values(text)
        if not values:
            return

        if self.last_asked_attribute and text.lower().startswith("for that"):
            self._replace_or_group(values, turn, self.last_asked_attribute)
            return

        explicit = EXPLICIT_VALUE_RE.search(text)
        if explicit:
            values = _preference_values(explicit.group(1))
        elif category_match:
            remainder = text[category_match.end():].strip(" ,.")
            if not remainder or "still exploring" in remainder.lower():
                return
            values = (remainder,)

        if is_override:
            replace_all = "ignore my earlier" in text.lower() or "what i need is" in text.lower()
            self._apply_override(values, turn, replace_all=replace_all)
        elif explicit or category_match:
            self._replace_or_group(values, turn)
        elif flexible:
            self._apply_plain_reply(text, turn)

    def _apply_plain_reply(self, text: str, turn: int) -> None:
        """Accept ordinary slot replies without treating feedback as a preference."""
        if re.search(
            r"not (?:quite |really )?right|none of|something else|still exploring|"
            r"just browsing|not sure what|surprise me",
            text,
            re.I,
        ):
            return
        if text.lower() in {"yes", "no", "thanks", "thank you", "ok", "okay", "..."}:
            return
        if self.last_asked_attribute == "category":
            self.category = text
            return
        if self.last_asked_attribute == "budget" and re.fullmatch(r"\d+(?:\.\d+)?", text):
            self._replace_or_group(("around $" + text,), turn, "budget")
            return
        if self.last_asked_attribute:
            self._replace_or_group(_preference_values(text), turn, self.last_asked_attribute)
        elif re.search(r"\b(?:prefer|need|want|must|under)\b", text, re.I):
            # A simple free-form requirement is evidence, not an inferred category.
            self._replace_or_group(_preference_values(text), turn)

    def _apply_override(self, values: tuple[str, ...], turn: int, *, replace_all: bool) -> None:
        grouped = self._group_values(values)
        attributes = set(grouped)
        if replace_all or attributes == {"feature"}:
            self.preferences.clear()
        else:
            for attribute in attributes:
                self.preferences.pop(attribute, None)
            # Initial free-form preferences are stored as features; an explicit
            # correction supersedes that ambiguous earlier value.
            self.preferences.pop("feature", None)
        for attribute, items in grouped.items():
            self.preferences[attribute] = PreferenceSlot(attribute, tuple(items), turn)
            self.unconstrained_attributes.discard(attribute)

    def _replace_or_group(
        self,
        values: tuple[str, ...],
        turn: int,
        fallback: str = "feature",
    ) -> None:
        for attribute, items in self._group_values(values, fallback).items():
            self.preferences[attribute] = PreferenceSlot(attribute, tuple(items), turn)
            self.unconstrained_attributes.discard(attribute)

    @staticmethod
    def _group_values(values: tuple[str, ...], fallback: str = "feature") -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for value in values:
            attribute = classify_preference(value, fallback)
            grouped.setdefault(attribute, []).append(value)
        return grouped

    @staticmethod
    def _named_attribute(message: str) -> str | None:
        lowered = message.lower()
        for attribute in ALLOWED_ATTRIBUTES:
            if re.search(rf"\b{re.escape(attribute.replace('_', ' '))}\b", lowered):
                return attribute
        return None

    def active_values(self) -> tuple[str, ...]:
        return tuple(
            value
            for attribute in self.preferences
            for value in self.preferences[attribute].values
        )

    def retrieval_query(self, turn: int) -> str:
        if int(turn) == 1 and self.first_message:
            return self.first_message
        parts = [self.category or "", *self.active_values()]
        return " ".join(part for part in parts if part).strip()
