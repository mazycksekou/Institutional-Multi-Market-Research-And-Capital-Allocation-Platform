import unittest
from automation_scheduler.ncaaf_source_exhaustion_query_builder import QUERY_FAMILIES, build_ncaaf_source_exhaustion_query_plan

class TestNcaafSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_query_floor_is_met(self):
        report = build_ncaaf_source_exhaustion_query_plan()
        self.assertGreaterEqual(report["query_count"], 150)
        self.assertGreaterEqual(report["source_policy_query_count"], 30)
        self.assertEqual(len(QUERY_FAMILIES), 22)

if __name__ == "__main__":
    unittest.main()
