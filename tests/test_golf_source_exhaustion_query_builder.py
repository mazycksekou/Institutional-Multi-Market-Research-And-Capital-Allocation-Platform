import unittest

from automation_scheduler.golf_source_exhaustion_query_builder import QUERY_FAMILIES, build_golf_source_exhaustion_query_plan


class TestGolfSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_required_query_families_are_present(self):
        report = build_golf_source_exhaustion_query_plan()
        self.assertGreaterEqual(report["query_count"], 125)
        self.assertEqual(len(QUERY_FAMILIES), 20)
        self.assertIn("golf_strokes_gained_public_data", QUERY_FAMILIES)
        self.assertIn("lpga_results_public_data", QUERY_FAMILIES)


if __name__ == "__main__":
    unittest.main()
