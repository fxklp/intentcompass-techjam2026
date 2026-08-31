from __future__ import annotations

import unittest

from solution.contracts import PreferenceSlot
from solution.question_policy import choose_question
from solution.state import SessionState


class SessionStateTest(unittest.TestCase):
    def test_explicit_override_replaces_old_slot_value(self) -> None:
        state = SessionState.create("session", {})
        state.apply_user_message("I'm looking for a shirt. I prefer red.", 1)
        self.assertIn("red", " ".join(state.active_values()).lower())

        state.apply_user_message("Actually, make it blue instead.", 2)

        active = " ".join(state.active_values()).lower()
        self.assertIn("blue", active)
        self.assertNotIn("red", active)

    def test_broad_override_clears_old_value_from_a_different_slot(self) -> None:
        state = SessionState.create("session", {})
        state.apply_user_message("I'm looking for a shirt. I prefer red.", 1)

        state.apply_user_message(
            "Actually, ignore my earlier preference. What I need is: cotton.",
            2,
        )

        active = " ".join(state.active_values()).lower()
        self.assertIn("cotton", active)
        self.assertNotIn("red", active)

    def test_no_preference_clears_slot_and_question_does_not_repeat(self) -> None:
        state = SessionState.create("session", {})
        state.mark_asked("material")
        state.preferences["material"] = PreferenceSlot("material", ("cotton",), 1)

        state.apply_user_message("I don't have a preference for material.", 2)
        attribute, _ = choose_question(state)

        self.assertNotIn("material", state.preferences)
        self.assertIn("material", state.unconstrained_attributes)
        self.assertNotEqual(attribute, "material")

    def test_reset_factory_copies_profile(self) -> None:
        profile = {"tags": ["value"]}
        state = SessionState.create("session", profile)
        profile["tags"].append("changed")
        self.assertEqual(state.user_profile, {"tags": ["value"]})
if __name__ == "__main__":
    unittest.main()
