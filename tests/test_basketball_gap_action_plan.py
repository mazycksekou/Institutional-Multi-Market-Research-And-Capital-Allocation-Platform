import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import GAP_ACTIONS, build_basketball_free_vs_paid_gap_action_plan


class TestBasketballGapActionPlan(unittest.TestCase):
    def test_every_gap_action_is_concrete(self):
        report = build_basketball_free_vs_paid_gap_action_plan()
        self.assertTrue(report["ok"])
        self.assertGreater(report["gap_rows_total"], 0)
        for row in report["action_rows"]:
            self.assertIn(row["action"], GAP_ACTIONS)
            self.assertTrue(row["allowed_action"])


if __name__ == "__main__":
    unittest.main()
