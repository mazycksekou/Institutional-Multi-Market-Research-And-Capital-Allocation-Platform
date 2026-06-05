import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import FREE_VS_PAID_CATEGORIES, SPORTS, build_basketball_free_vs_paid_source_ledger


class TestBasketballFreeVsPaidSourceLedger(unittest.TestCase):
    def test_every_lane_has_exactly_one_allowed_category(self):
        report = build_basketball_free_vs_paid_source_ledger()
        self.assertTrue(report["ok"])
        self.assertEqual({row["sport"] for row in report["source_ledger_rows"]}, set(SPORTS))
        for row in report["source_ledger_rows"]:
            self.assertIn(row["free_or_paid_category"], FREE_VS_PAID_CATEGORIES)
            self.assertEqual(row["primary_category_count"], 1)

    def test_no_generic_unknown_or_research_later_actions(self):
        report = build_basketball_free_vs_paid_source_ledger()
        rendered = str(report).lower()
        self.assertNotIn("research later", rendered)
        self.assertNotIn("look into it", rendered)
        self.assertNotIn("maybe paid", rendered)
        self.assertNotIn("'unknown'", rendered)


if __name__ == "__main__":
    unittest.main()
