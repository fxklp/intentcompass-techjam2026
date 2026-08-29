from __future__ import annotations

from solution.state import SessionState


QUESTION_PRIORITY = (
    "feature",
    "material",
    "color",
    "size",
    "style",
    "use_case",
    "budget",
    "brand",
    "other",
)

QUESTION_TEXT = {
    "feature": "Which feature matters most to you?",
    "material": "Do you have a material preference?",
    "color": "Do you have a color preference?",
    "size": "Is there a size or fit requirement?",
    "style": "What style would you prefer?",
    "use_case": "What will you mainly use it for?",
    "budget": "What budget should I keep in mind?",
    "brand": "Do you prefer a particular brand?",
    "other": "Is there another product detail I should prioritize?",
}


def choose_question(state: SessionState) -> tuple[str | None, str]:
    excluded = set(state.asked_attributes) | state.unconstrained_attributes
    for attribute in QUESTION_PRIORITY:
        if attribute not in excluded and attribute not in state.preferences:
            return attribute, QUESTION_TEXT[attribute]
    return None, "Here are the closest matches for your current preferences."
