import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def f1_inputs(**extra):
    data = {
        "driver": "Max Verstappen", "constructor": "Red Bull Racing",
        "opponent": "Charles Leclerc", "opponent_constructor": "Ferrari",
        "circuit": "Circuit de Monaco", "race_name": "Monaco Grand Prix",
        "session_type": "race", "track_type": "street", "track_length_km": 3.337, "laps": 78,
        "weather_conditions": "dry", "rain_probability": 0.12, "temperature_celsius": 24,
        "wind_speed_kph": 8, "track_temperature_celsius": 38,
        "driver_rating": 94, "opponent_driver_rating": 90,
        "constructor_pace_rating": 93, "opponent_constructor_pace_rating": 89,
        "car_reliability_rating": 0.95, "opponent_car_reliability_rating": 0.91,
        "qualifying_pace_rating": 92, "opponent_qualifying_pace_rating": 91,
        "race_pace_rating": 94, "opponent_race_pace_rating": 89,
        "tire_degradation_rating": 87, "opponent_tire_degradation_rating": 82,
        "pit_crew_rating": 91, "opponent_pit_crew_rating": 84,
        "strategy_rating": 90, "opponent_strategy_rating": 84,
        "dirty_air_sensitivity": 0.34, "opponent_dirty_air_sensitivity": 0.42,
        "overtaking_rating": 89, "opponent_overtaking_rating": 84,
        "defending_rating": 92, "opponent_defending_rating": 88,
        "start_performance_rating": 90, "opponent_start_performance_rating": 86,
        "wet_weather_rating": 93, "opponent_wet_weather_rating": 88,
        "street_circuit_rating": 88, "opponent_street_circuit_rating": 93,
        "driver_recent_form_rating": 91, "opponent_recent_form_rating": 86,
        "constructor_recent_form_rating": 90, "opponent_constructor_recent_form_rating": 85,
        "starting_grid_position": 2, "opponent_starting_grid_position": 3,
        "qualifying_position": 2, "opponent_qualifying_position": 3,
        "practice_long_run_pace": 93, "opponent_practice_long_run_pace": 88,
        "practice_short_run_pace": 92, "opponent_practice_short_run_pace": 91,
        "dnf_probability": 0.05, "opponent_dnf_probability": 0.08,
        "penalty_risk": 0.03, "opponent_penalty_risk": 0.05,
        "engine_penalty": 0, "opponent_engine_penalty": 0,
        "crash_risk": 0.06, "opponent_crash_risk": 0.08,
        "safety_car_probability": 0.68, "virtual_safety_car_probability": 0.42,
        "track_position_importance": 0.92, "overtaking_difficulty": 0.88,
        "pit_stop_delta_seconds": 19.5,
        "constructor_driver_1_rating": 94, "constructor_driver_2_rating": 83,
        "constructor_race_pace_rating": 93, "constructor_qualifying_pace_rating": 92,
        "constructor_reliability_rating": 0.95, "constructor_strategy_rating": 90,
        "constructor_pit_crew_rating": 91, "book_count": 8,
    }
    data.update(extra)
    return data


def f1_alias_inputs(**extra):
    data = {
        "race": "Monaco Grand Prix", "track": "Circuit de Monaco", "driver_name": "Max Verstappen",
        "team": "Red Bull Racing", "opponent_name": "Charles Leclerc", "opponent_team": "Ferrari",
        "session_type": "race", "track_type": "street", "track_km": 3.337, "race_laps": 78,
        "weather": "dry", "rain_pct": 0.12, "temp_c": 24, "wind_kph": 8, "track_temp_c": 38,
        "driver_power_rating": 94, "opp_driver_rating": 90, "team_pace": 93, "opp_team_pace": 89,
        "car_reliability": 0.95, "opp_car_reliability": 0.91, "qualy_pace": 92,
        "opp_qualy_pace": 91, "race_pace": 94, "opp_race_pace": 89,
        "tire_deg": 87, "opp_tire_deg": 82, "pit_rating": 91, "opp_pit_rating": 84,
        "strategy": 90, "opp_strategy": 84, "dirty_air_sensitivity": 0.34,
        "opponent_dirty_air_sensitivity": 0.42, "overtaking": 89, "opp_overtaking": 84,
        "defending": 92, "opp_defending": 88, "starts": 90, "opp_starts": 86,
        "wet_rating": 93, "opp_wet_rating": 88, "street_rating": 88, "opp_street_rating": 93,
        "recent_form": 91, "opp_recent_form": 86, "team_form": 90, "opp_team_form": 85,
        "grid_pos": 2, "opp_grid_pos": 3, "qualy_pos": 2, "opp_qualy_pos": 3,
        "long_run_pace": 93, "opp_long_run_pace": 88, "short_run_pace": 92,
        "opp_short_run_pace": 91, "dnf_risk": 0.05, "opp_dnf_risk": 0.08,
        "penalty": 0.03, "opp_penalty": 0.05, "grid_penalty": 0, "opp_grid_penalty": 0,
        "crash": 0.06, "opp_crash": 0.08, "sc_probability": 0.68,
        "vsc_probability": 0.42, "track_position": 0.92, "overtake_difficulty": 0.88,
        "pit_delta": 19.5, "constructor_driver_1_rating": 94, "constructor_driver_2_rating": 83,
        "constructor_race_pace_rating": 93, "constructor_qualifying_pace_rating": 92,
        "constructor_reliability_rating": 0.95, "constructor_strategy_rating": 90,
        "constructor_pit_crew_rating": 91, "book_count": 8,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {
        "sport": "f1", "league": "Formula 1", "event_id": "Monaco Grand Prix",
        "event": "Monaco Grand Prix", "market": "head_to_head", "selection": "Max Verstappen",
        "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "source_type": "unit_test",
        "screenshot_text": "Max Verstappen head to head +100 vs Charles Leclerc",
        "visible_markets": ["head_to_head"], "input_stats": f1_inputs(),
    }
    data.update(extra)
    return data


class TestFormula1ModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "f1", "league": "Formula 1",
            "event": "Monaco Grand Prix", "market": "head_to_head", "selection": "Max Verstappen",
            "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
            "risk_profile": "moderate", "screenshot_text": "Max Verstappen head to head +100 vs Charles Leclerc",
            "visible_markets": ["head_to_head"], "input_stats": f1_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "f1_qualifying_race_pace_pit_strategy_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "f1")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["partial_model_mode"])

    def test_bad_text_input_safety_with_valid_envelope(self):
        response = self._sport(input_stats="bad f1 text")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertNotEqual(response["decision"], "CONFIRMED_BET")

    def test_race_winner_confirmed_capable(self):
        self.assertTrue(self._sport(market="race_winner")["confirmed_bets"])

    def test_podium_finish_active(self): self.assert_active(self._sport(market="podium_finish"))
    def test_top_5_finish_active(self): self.assert_active(self._sport(market="top_5_finish"))
    def test_top_10_finish_active(self): self.assert_active(self._sport(market="top_10_finish"))
    def test_points_finish_active(self): self.assert_active(self._sport(market="points_finish"))
    def test_head_to_head_active(self): self.assert_active(self._sport(market="head_to_head"))
    def test_qualifying_winner_active(self): self.assert_active(self._sport(market="qualifying_winner", input_stats=f1_inputs(session_type="qualifying")))
    def test_qualifying_head_to_head_active(self): self.assert_active(self._sport(market="qualifying_head_to_head", input_stats=f1_inputs(session_type="qualifying")))
    def test_fastest_lap_active(self): self.assert_active(self._sport(market="fastest_lap"))
    def test_driver_to_retire_active(self): self.assert_active(self._sport(market="driver_to_retire"))
    def test_constructor_winner_active(self): self.assert_active(self._sport(market="constructor_winner", selection="Red Bull Racing"))
    def test_safety_car_active(self): self.assert_active(self._sport(market="safety_car", selection="yes"))
    def test_classified_finish_active(self): self.assert_active(self._sport(market="classified_finish"))
    def test_laps_completed_markets_active(self):
        self.assert_active(self._sport(market="over_laps_completed", selection="over", line=76.5, input_stats=f1_inputs(line=76.5)))
        self.assert_active(self._sport(market="under_laps_completed", selection="under", line=77.5, input_stats=f1_inputs(line=77.5)))
    def test_negative_edge_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-400)["status"], "evaluated_no_bet")

    def test_edge_too_small_evaluated_no_bet(self):
        self.assertEqual(self._sport(odds_american=-200)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_no_bet(self):
        response = self._sport(input_stats=f1_inputs(book_count=1, rain_probability=0.75, weather_conditions="wet", dnf_probability=0.22, practice_report_quality="low", qualifying_report_quality="low"))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

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
        response = self._sport(input_stats={"weather": "wet", "rain_pct": 0.8})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_practice_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"long_run_pace": 92, "short_run_pace": 94})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_qualifying_only_enrichment_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"qualy_pace": 94, "grid_pos": 1, "qualy_pos": 1})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_social_crowd_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"social_sentiment": 95, "crowd_consensus": 90})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_screenshot_analysis_alias_path(self):
        response = self._screenshot()
        analysis = response["model_analysis"]
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

    def test_league_calibration_label(self):
        self.assertEqual(self._sport()["league_calibration_applied"], "f1")

    def test_session_circuit_weather_calibration_fields_present(self):
        response = self._sport()
        self.assertEqual(response["session_calibration_applied"], "race")
        self.assertEqual(response["circuit_calibration_applied"], "street")
        self.assertEqual(response["weather_calibration_applied"], "dry")

    def test_malformed_text_numeric_fields_cannot_activate_from_defaults(self):
        malformed = deepcopy(f1_alias_inputs())
        for key in ("driver_power_rating", "team_pace", "race_pace", "qualy_pace", "grid_pos", "dnf_risk"):
            malformed[key] = "bad text"
        response = self._screenshot(input_stats=malformed)
        analysis = response["model_analysis"]
        self.assertEqual(analysis["confirmed_bets"], [])
        self.assertNotEqual(analysis["decision"], "CONFIRMED_BET")
        self.assertTrue(analysis["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
