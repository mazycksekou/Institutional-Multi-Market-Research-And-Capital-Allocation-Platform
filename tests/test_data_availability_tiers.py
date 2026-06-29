import tempfile
import unittest
from pathlib import Path

from src.services.streamlit_dashboard_facade import SPORT_PROFILES, build_data_availability_report, build_prediction_calibration_metadata, evaluate_data_availability, get_tier_profile, write_data_availability_report
from src.services.streamlit_dashboard_facade import build_registry


NCAAF_T0 = ["teams", "game_id", "season", "week", "home_away", "final_score", "final_result"]


class TestDataAvailabilityTiers(unittest.TestCase):
    def test_required_profiles_exist(self):
        for module in (
            "basketball_nba",
            "basketball_wnba",
            "basketball_ncaab",
            "basketball_ncaaw",
            "americanfootball_nfl",
            "americanfootball_ncaaf",
            "baseball_mlb",
            "icehockey_nhl",
            "soccer",
            "tennis",
            "golf",
            "combat_sports",
            "prediction_market",
            "stock",
            "crypto",
            "sportsbook",
        ):
            self.assertIn(module, SPORT_PROFILES)
            self.assertEqual(get_tier_profile(module)["module"], module)

    def test_tier_0_assigned_when_only_results_and_schedule_exist(self):
        result = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0)
        self.assertEqual(result["data_availability_tier"], "TIER_0_OUTCOME_BACKFILL")
        self.assertTrue(result["can_backtest"])
        self.assertIn("epa", result["missing_advanced_inputs"])

    def test_higher_tiers_are_assigned_by_available_layer(self):
        tier1 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin"])
        tier2 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin", "spread"])
        tier3 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin", "spread", "epa"])
        tier4 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin", "spread", "epa", "injuries"])

        self.assertEqual(tier1["data_availability_tier"], "TIER_1_BASIC_FORM")
        self.assertEqual(tier2["data_availability_tier"], "TIER_2_MARKET_AWARE")
        self.assertEqual(tier3["data_availability_tier"], "TIER_3_ADVANCED_STATS")
        self.assertEqual(tier4["data_availability_tier"], "TIER_4_CONTEXT")
        self.assertNotEqual(tier1["calibration_bucket"], tier3["calibration_bucket"])

    def test_missing_advanced_is_reported_not_fabricated_and_does_not_block_basic(self):
        result = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin"])
        self.assertEqual(result["data_availability_tier"], "TIER_1_BASIC_FORM")
        self.assertTrue(result["can_train_baseline"])
        self.assertIn("epa", result["missing_advanced_inputs"])
        tier3 = result["tier_assessments"][3]
        self.assertIn("epa", tier3["unavailable_not_fabricated_fields"])
        self.assertLessEqual(result["confidence_cap"], 0.62)
        self.assertIn("cap", result["confidence_cap_reason"])

    def test_missing_critical_tier_0_blocks_calibration(self):
        result = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=["epa", "success_rate"])
        self.assertEqual(result["data_availability_tier"], "INSUFFICIENT_TIER_0")
        self.assertFalse(result["can_backtest"])
        self.assertEqual(result["confidence_cap"], 0.0)
        self.assertIn("game_id", result["missing_critical_inputs"])

    def test_prediction_metadata_shape(self):
        metadata = build_prediction_calibration_metadata(module="americanfootball_ncaaf", available_fields=NCAAF_T0)
        for key in (
            "data_availability_tier",
            "calibration_bucket",
            "missing_critical_inputs",
            "missing_advanced_inputs",
            "confidence_penalty_applied",
            "confidence_cap",
            "confidence_cap_reason",
            "expected_calibration_reliability",
            "recommended_next_data_layer",
            "data_not_available_warning",
        ):
            self.assertIn(key, metadata)

    def test_global_report_is_compact_safe_and_persists_expected_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_data_availability_report(registry=build_registry())
            paths = write_data_availability_report(report, base_data_dir=tmp)
            payload_text = Path(tmp, paths["latest_path"]).read_text(encoding="utf-8").lower()

        modules = {row["module"]: row for row in report["modules"]}
        self.assertIn("americanfootball_ncaaf", modules)
        self.assertIn("data_sources/data_availability/latest.json", paths["latest_path"])
        self.assertIn("data_sources/data_availability/items/", paths["item_path"])
        self.assertIn("data_sources/data_availability/daily/", paths["daily_json_path"])
        self.assertIn("data_sources/data_availability/daily/", paths["daily_markdown_path"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertNotIn("provider_payload", payload_text)
        self.assertNotIn("do-not-leak", payload_text)


if __name__ == "__main__":
    unittest.main()
