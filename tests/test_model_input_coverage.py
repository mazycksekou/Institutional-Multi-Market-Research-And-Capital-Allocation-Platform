import unittest

from automation_scheduler.data_source_registry import MANDATORY_LANES, build_registry
from automation_scheduler.model_input_coverage import build_coverage_report


class TestModelInputCoverage(unittest.TestCase):
    def setUp(self):
        self.coverage = build_coverage_report(registry=build_registry())
        self.modules = {row["lane_id"]: row for row in self.coverage["modules"]}

    def test_every_mandatory_lane_appears_in_coverage(self):
        expected = {lane["lane_id"] for lane in MANDATORY_LANES}
        self.assertEqual(set(self.modules), expected)
        self.assertEqual(self.coverage["total_modules"], len(expected))

    def test_required_named_lanes_exist(self):
        for lane_id in (
            "basketball_nba",
            "basketball_wnba",
            "americanfootball_nfl",
            "americanfootball_ncaaf",
            "baseball_mlb",
            "icehockey_nhl",
            "soccer",
            "tennis",
            "ufc_mma",
            "boxing",
            "golf",
            "basketball_ncaab",
            "basketball_ncaaw",
            "prediction_markets",
            "stocks",
            "ETFs",
            "bonds",
            "rates",
            "macro",
            "major_assets",
            "sportsbooks",
            "odds",
            "weather",
            "officials",
            "injuries",
            "lineups",
            "schedules",
            "news_context",
        ):
            self.assertIn(lane_id, self.modules)

    def test_empty_lanes_are_not_hidden(self):
        self.assertEqual(self.modules["officials"]["candidate_sources"], [])
        self.assertEqual(self.modules["officials"]["lane_status"], "needs_external_research")
        self.assertIn("event_id", self.modules["officials"]["missing_inputs"])

    def test_unverified_sources_do_not_complete_lane(self):
        nba = self.modules["basketball_nba"]
        self.assertGreater(len(nba["candidate_sources"]), 0)
        self.assertEqual(nba["verified_sources"], [])
        self.assertIn("basketball_nba", self.coverage["modules_without_verified_source"])

    def test_coverage_report_is_safe(self):
        self.assertFalse(self.coverage["provider_write"])
        self.assertFalse(self.coverage["execution_allowed"])
        self.assertFalse(self.coverage["live_execution_enabled"])
        self.assertFalse(self.coverage["raw_payload_included"])


if __name__ == "__main__":
    unittest.main()
