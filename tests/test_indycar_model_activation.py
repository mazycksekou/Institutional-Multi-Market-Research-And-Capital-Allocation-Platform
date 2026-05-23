import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot
from multi_sport_model_registry import get_sport_model_config


def indy_payload(**extra):
    data = deepcopy(get_sport_model_config("indycar")["screenshot_alias_test_payload"])
    data.update(extra)
    return data


class TestIndyCarModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**indy_payload(**extra))))

    def _screenshot(self, **extra):
        data = indy_payload(**extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "indycar_aero_strategy_restart_pit_variance_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "indycar")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["partial_model_mode"])

    def test_bad_text_input_safety_with_valid_envelope(self):
        response = self._sport(input_stats="bad indycar text")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertNotEqual(response["decision"], "CONFIRMED_BET")

    def test_primary_winner_market_confirmed_capable(self):
        self.assertTrue(self._sport(market="race_winner", odds_american=1800)["confirmed_bets"])

    def test_podium_top_finish_market_active(self): self.assert_active(self._sport(market="podium_finish"))
    def test_top_10_finish_market_active(self): self.assert_active(self._sport(market="top_10_finish"))
    def test_head_to_head_matchup_active(self): self.assert_active(self._sport(market="driver_matchup"))
    def test_qualifying_market_active(self): self.assert_active(self._sport(market="qualifying_matchup"))
    def test_fastest_lap_active(self): self.assert_active(self._sport(market="fastest_lap"))
    def test_retire_not_classified_classified_active(self):
        self.assert_active(self._sport(market="driver_to_retire"))
        self.assert_active(self._sport(market="not_classified"))
        self.assert_active(self._sport(market="classified_finish"))

    def test_manufacturer_winner_active(self): self.assert_active(self._sport(market="manufacturer_winner", selection="Honda"))
    def test_finishing_position_active(self): self.assert_active(self._sport(market="finishing_position", selection="under", line=8.5, input_stats=dict(indy_payload()["input_stats"], line=8.5)))
    def test_negative_edge_returns_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-300)["status"], "evaluated_no_bet")
    def test_edge_too_small_returns_evaluated_no_bet_edge_too_small(self): self.assertEqual(self._sport(odds_american=-250)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_returns_evaluated_no_bet_low_confidence(self):
        stats = dict(indy_payload()["input_stats"], book_count=1, caution_prob=0.78, overtime_prob=0.35, dnf_risk=0.24, crash=0.24, practice_report_quality="low", qualifying_report_quality="low")
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
        response = self._sport(input_stats={"weather": "rain", "precip_prob": 0.8})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_practice_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"single_lap_speed": 232.4, "ten_lap_avg": 231.2})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_qualifying_only_enrichment_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"qual_pos": 1, "start_pos": 1})
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

    def test_league_calibration_label(self): self.assertEqual(self._sport()["league_calibration_applied"], "indycar")

    def test_module_specific_calibration_fields_present(self):
        response = self._sport()
        self.assertEqual(response["series_calibration_applied"], "indycar")
        self.assertEqual(response["track_type_calibration_applied"], "superspeedway")
        self.assertEqual(response["race_environment_calibration_applied"], "dry")

    def test_malformed_text_numeric_fields_cannot_activate_from_defaults(self):
        malformed = dict(indy_payload()["input_stats"])
        for key in ("driver_power_rating", "car_speed", "long_run_speed", "start_pos", "dnf_risk", "caution_prob"):
            malformed[key] = "bad text"
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertEqual(analysis["confirmed_bets"], [])
        self.assertNotEqual(analysis["decision"], "CONFIRMED_BET")
        self.assertTrue(analysis["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
