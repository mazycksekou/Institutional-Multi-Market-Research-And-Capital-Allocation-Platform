import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot
from src.market_intelligence.multi_sport_model_registry import get_sport_model_config


def motogp_payload(**extra):
    data = deepcopy(get_sport_model_config("motogp")["screenshot_alias_test_payload"])
    data.update(extra)
    return data


class TestMotoGPModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**motogp_payload(**extra))))

    def _screenshot(self, **extra):
        data = motogp_payload(**extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "motogp_rider_bike_tire_weather_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "motogp")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["partial_model_mode"])

    def test_bad_text_input_safety_with_valid_envelope(self):
        response = self._sport(input_stats="bad motogp text")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertNotEqual(response["decision"], "CONFIRMED_BET")

    def test_primary_winner_market_confirmed_capable(self): self.assertTrue(self._sport(market="race_winner", odds_american=1200)["confirmed_bets"])
    def test_podium_top_finish_market_active(self): self.assert_active(self._sport(market="podium_finish"))
    def test_top_10_points_finish_market_active(self):
        self.assert_active(self._sport(market="top_10_finish"))
        self.assert_active(self._sport(market="points_finish"))

    def test_head_to_head_matchup_active(self): self.assert_active(self._sport(market="rider_matchup"))
    def test_qualifying_market_active(self): self.assert_active(self._sport(market="qualifying_matchup", input_stats=dict(motogp_payload()["input_stats"], session_type="qualifying")))
    def test_fastest_lap_active(self): self.assert_active(self._sport(market="fastest_lap"))
    def test_retire_not_classified_classified_active(self):
        self.assert_active(self._sport(market="rider_to_retire"))
        self.assert_active(self._sport(market="not_classified"))
        self.assert_active(self._sport(market="classified_finish"))

    def test_manufacturer_team_winner_active(self):
        self.assert_active(self._sport(market="manufacturer_winner", selection="Ducati"))
        self.assert_active(self._sport(market="team_winner", selection="Ducati Lenovo Team"))

    def test_finishing_position_active(self): self.assert_active(self._sport(market="finishing_position", selection="under", line=5.5, input_stats=dict(motogp_payload()["input_stats"], line=5.5)))
    def test_negative_edge_returns_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-300)["status"], "evaluated_no_bet")
    def test_edge_too_small_returns_evaluated_no_bet_edge_too_small(self): self.assertEqual(self._sport(odds_american=-220)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_returns_evaluated_no_bet_low_confidence(self):
        stats = dict(motogp_payload()["input_stats"], book_count=1, rain_pct=0.75, crash=0.24, opp_crash=0.24, front_tire_stress=0.82, rear_tire_stress=0.84, practice_report_quality="low", qualifying_report_quality="low")
        self.assertEqual(self._sport(input_stats=stats)["status"], "evaluated_no_bet_low_confidence")

    def test_odds_stability_across_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [r["final_probability"] for r in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_provider_failure_safety(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("boom")):
            self.assertTrue(self._screenshot()["ok"])

    def test_weather_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"rain_pct": 0.8, "track_temp_c": 28})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_practice_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"practice_lap_time": 105.2, "long_run_pace": 93})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_qualifying_only_enrichment_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"qualy_pos": 1, "grid_pos": 1, "qualy_pace": 95})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_social_crowd_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"social_sentiment": 95, "crowd_consensus": 90})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_screenshot_analysis_alias_path(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])

    def test_direct_versus_screenshot_normalization_parity(self):
        direct = self._sport()
        screenshot = self._screenshot()["model_analysis"]
        self.assertEqual(direct["model_status"], "active")
        self.assertEqual(screenshot["model_status"], "active")
        self.assertIsNotNone(direct["final_probability"])
        self.assertIsNotNone(screenshot["final_probability"])

    def test_confirmed_no_bet_same_selection_mutual_exclusion(self):
        response = self._sport()
        confirmed = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["confirmed_bets"]}
        no_bets = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_logbook_rows_include_required_fields(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake"):
            self.assertIn(field, row)

    def test_league_calibration_label(self): self.assertEqual(self._sport()["league_calibration_applied"], "motogp")

    def test_module_specific_calibration_fields_present(self):
        response = self._sport()
        self.assertEqual(response["session_calibration_applied"], "race")
        self.assertEqual(response["track_type_calibration_applied"], "flowing")
        self.assertEqual(response["weather_calibration_applied"], "dry")

    def test_malformed_text_numeric_fields_cannot_activate_from_defaults(self):
        malformed = dict(motogp_payload()["input_stats"])
        for key in ("rider_power_rating", "bike_pace", "race_pace", "grid_pos", "crash", "rain_pct"):
            malformed[key] = "bad text"
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertEqual(analysis["confirmed_bets"], [])
        self.assertNotEqual(analysis["decision"], "CONFIRMED_BET")
        self.assertTrue(analysis["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
