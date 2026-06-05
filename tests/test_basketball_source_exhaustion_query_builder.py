import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS
from automation_scheduler.basketball_source_exhaustion_query_builder import (
    build_basketball_source_exhaustion_queries,
    build_basketball_source_exhaustion_query_plan,
)


class TestBasketballSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_query_plan_expands_unresolved_and_partial_lanes(self):
        report = build_basketball_source_exhaustion_query_plan()
        self.assertTrue(report["ok"])
        self.assertEqual(set(report["sports_included"]), set(SPORTS))
        self.assertGreaterEqual(report["query_count"], 80)
        self.assertTrue(all(len(rows) >= 12 for rows in report["lane_query_index"].values()))
        self.assertIn("exact_field_name", {row["query_family"] for row in report["query_rows"]})

    def test_query_list_matches_query_plan(self):
        plan = build_basketball_source_exhaustion_query_plan()
        report = build_basketball_source_exhaustion_queries()
        self.assertEqual(report["query_count"], plan["query_count"])
        self.assertEqual(len(report["queries"]), plan["query_count"])
        self.assertEqual(report["query_rows"], plan["query_rows"])


if __name__ == "__main__":
    unittest.main()
