from __future__ import annotations

import io
import re
import unittest
from contextlib import redirect_stdout

from demo.run_demo import (
    NOT_SCORED_UNTIL_OVERRIDE,
    official_target_rank,
    run_session,
    target_rank_display,
)


class RepeatableDemoTest(unittest.TestCase):
    def test_default_demo_is_truthful_and_hits_only_after_override(self) -> None:
        result = run_session(verbose=False)
        self.assertTrue(result["override_seen"])
        self.assertTrue(result["hit"])
        self.assertEqual(result["sample_id"], "public_0183")
        self.assertEqual(result["override_turn"], 4)
        self.assertEqual(result["first_hit_turn"], 5)
        self.assertEqual(result["best_rank"], 8)

        pre_override = [
            record for record in result["turns"]
            if not record["score_eligible"]
        ]
        self.assertEqual([record["turn"] for record in pre_override], [1, 2, 3])
        self.assertTrue(all(record["raw_target_rank"] is None for record in pre_override))
        self.assertTrue(all(
            record["scored_target_rank"] is None
            and record["target_rank_display"] == NOT_SCORED_UNTIL_OVERRIDE
            for record in pre_override
        ))

        scored_hits = [
            record for record in result["turns"]
            if record["scored_target_rank"] is not None
        ]
        self.assertEqual(len(scored_hits), 1)
        self.assertEqual(scored_hits[0]["turn"], result["first_hit_turn"])
        self.assertEqual(scored_hits[0]["scored_target_rank"], result["best_rank"])

        active = " ".join(
            value
            for values in result["override_preferences"].values()
            for value in values
        ).casefold()
        self.assertNotIn(result["old_value"].casefold(), active)
        self.assertIn(result["new_value"].casefold(), active)
        self.assertNotIn(result["old_value"].casefold(), result["override_query"].casefold())
        self.assertIn(result["new_value"].casefold(), result["override_query"].casefold())

    def test_verbose_output_never_shows_rank_before_override_then_claims_later_hit(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            run_session(verbose=True)
        output = buf.getvalue()
        turns = re.split(r"(?=\nTURN \d+)", output)
        first_hit_match = re.search(r"First hit turn:\s*(\d+)", output)
        self.assertIsNotNone(first_hit_match)
        first_hit_turn = int(first_hit_match.group(1))
        for chunk in turns:
            turn_match = re.match(r"\nTURN (\d+)", chunk)
            if not turn_match:
                continue
            turn_num = int(turn_match.group(1))
            rank_match = re.search(r"Target rank\s*:\s*(.+)", chunk)
            self.assertIsNotNone(rank_match)
            rank_text = rank_match.group(1).strip()
            if turn_num < first_hit_turn:
                self.assertIn(rank_text, (NOT_SCORED_UNTIL_OVERRIDE, "not in Top 10"))

    def test_pre_override_top_10_rank_is_never_presented_as_an_official_hit(self) -> None:
        self.assertIsNone(official_target_rank(1, score_eligible=False))
        self.assertEqual(
            target_rank_display(1, score_eligible=False),
            NOT_SCORED_UNTIL_OVERRIDE,
        )
        self.assertEqual(official_target_rank(1, score_eligible=True), 1)
        self.assertEqual(target_rank_display(1, score_eligible=True), "1")


if __name__ == "__main__":
    unittest.main()
