import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import build_basketball_paid_data_requirement_matrix


class TestBasketballPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_lanes_explain_free_source_insufficiency(self):
        report = build_basketball_paid_data_requirement_matrix()
        self.assertTrue(report["ok"])
        self.assertGreater(report["paid_required_count"], 0)
        for row in report["requirement_rows"]:
            self.assertTrue(row["why_free_sources_are_insufficient"])
            self.assertIn(row["priority"], {"critical", "high", "medium", "low"})
            self.assertTrue(row["recommendation"])


if __name__ == "__main__":
    unittest.main()
