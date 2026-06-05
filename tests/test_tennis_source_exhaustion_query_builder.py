import unittest

from automation_scheduler.tennis_source_exhaustion_query_builder import QUERY_FAMILIES, build_tennis_source_exhaustion_query_plan


class TestTennisSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_query_plan_has_required_breadth(self):
        report = build_tennis_source_exhaustion_query_plan()
        self.assertTrue(report["ok"])
        self.assertGreaterEqual(report["query_count"], 100)
        self.assertTrue(set(QUERY_FAMILIES).issubset(set(report["query_families"])))
        for rows in report["lane_query_index"].values():
            self.assertGreaterEqual(len(rows), 10)


if __name__ == "__main__":
    unittest.main()
