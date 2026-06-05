import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS
from automation_scheduler.basketball_source_discovery_query_builder import build_basketball_source_discovery_queries


class TestBasketballSourceDiscoveryQueryBuilder(unittest.TestCase):
    def test_queries_cover_each_basketball_sport_separately(self):
        report = build_basketball_source_discovery_queries()
        self.assertTrue(report["ok"])
        self.assertEqual(set(report["sports_included"]), set(SPORTS))
        for sport in SPORTS:
            self.assertTrue(any(row["sport"] == sport for row in report["queries"]))
        self.assertGreaterEqual(report["query_count"], 80)


if __name__ == "__main__":
    unittest.main()
