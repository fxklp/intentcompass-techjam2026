"""Bounded, session-local context distilled from caller-visible information."""
from __future__ import annotations

from dataclasses import dataclass, field

from solution.contracts import PreferenceSlot
from solution.state import OVERRIDE_RE, SessionState, classify_preference


def profile_priors(profile: dict) -> tuple[PreferenceSlot, ...]:
    """Only controlled preference tags; never infer identity from a profile."""
    tags = profile.get("preference_tags", ())
    if not isinstance(tags, (list, tuple)):
        return ()
    grouped: dict[str, list[str]] = {}
    for tag in tags[:16]:
        if not isinstance(tag, str):
            continue
        text = " ".join(tag.split())[:96]
        attribute = classify_preference(text, "other")
        if text and attribute != "other":
            grouped.setdefault(attribute, []).append(text)
    return tuple(PreferenceSlot(key, tuple(dict.fromkeys(values)), 0) for key, values in grouped.items())


@dataclass
class ContextMemory:
    priors: tuple[PreferenceSlot, ...]
    suppressed_priors: set[str] = field(default_factory=set)
    revision: int = 0
    signature: tuple = ()

    @classmethod
    def create(cls, profile: dict) -> "ContextMemory":
        return cls(profile_priors(profile))

    def observe(self, state: SessionState, message: str) -> bool:
        self.suppressed_priors.update(state.preferences)
        self.suppressed_priors.update(state.unconstrained_attributes)
        if OVERRIDE_RE.search(message) and "ignore my earlier" in message.lower():
            self.suppressed_priors.update(slot.attribute for slot in self.priors)
        signature = (
            state.category,
            tuple((key, slot.values) for key, slot in sorted(state.preferences.items())),
            tuple(sorted(state.unconstrained_attributes)),
        )
        changed = signature != self.signature
        if changed:
            self.revision += 1
            self.signature = signature
        return changed

    def active_priors(self) -> tuple[PreferenceSlot, ...]:
        return tuple(slot for slot in self.priors if slot.attribute not in self.suppressed_priors)

    def distill(self, state: SessionState) -> dict:
        # Rebuilt from current slots: no concatenated transcript or stale override.
        return {
            "revision": self.revision,
            "category": (state.category or "")[:160],
            "explicit": {key: list(slot.values)[:4] for key, slot in state.preferences.items()},
            "profile_priors": {slot.attribute: list(slot.values) for slot in self.active_priors()},
            "unconstrained": sorted(state.unconstrained_attributes),
        }
