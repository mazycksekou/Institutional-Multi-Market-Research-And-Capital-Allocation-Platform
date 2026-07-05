import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def nascar_inputs(**extra):
    data = {
        "driver": "Kyle Larson", "team": "Hendrick Motorsports", "manufacturer": "Chevrolet",
        "opponent": "Denny Hamlin", "opponent_team": "Joe Gibbs Racing", "opponent_manufacturer": "Toyota",
        "race_name": "Daytona 500", "track": "Daytona International Speedway", "track_type": "intermediate",
        "track_length_miles": 2.5, "scheduled_laps": 200, "race_distance_miles": 500,
        "series": "NASCAR Cup Series", "session_type": "race",
        "starting_position": 4, "opponent_starting_position": 12,
        "qualifying_position": 4, "opponent_qualifying_position": 12,
        "practice_rank": 3, "opponent_practice_rank": 14,
        "practice_single_lap_speed": 189.4, "opponent_practice_single_lap_speed": 187.8,
        "practice_5_lap_average": 188.6, "opponent_practice_5_lap_average": 187.1,
        "practice_10_lap_average": 187.9, "opponent_practice_10_lap_average": 186.3,
        "practice_15_lap_average": 187.1, "opponent_practice_15_lap_average": 185.8,
        "driver_rating": 96, "opponent_driver_rating": 85,
        "season_driver_rating": 95, "opponent_season_driver_rating": 86,
        "track_history_rating": 90, "opponent_track_history_rating": 83,
        "track_type_rating": 93, "opponent_track_type_rating": 84,
        "recent_form_rating": 94, "opponent_recent_form_rating": 85,
        "car_speed_rating": 95, "opponent_car_speed_rating": 84,
        "long_run_speed_rating": 96, "opponent_long_run_speed_rating": 83,
        "short_run_speed_rating": 94, "opponent_short_run_speed_rating": 84,
        "clean_air_speed_rating": 93, "opponent_clean_air_speed_rating": 83,
        "dirty_air_speed_rating": 91, "opponent_dirty_air_speed_rating": 84,
        "restart_rating": 92, "opponent_restart_rating": 83,
        "passing_rating": 91, "opponent_passing_rating": 84,
        "defense_rating": 89, "opponent_defense_rating": 84,
        "tire_management_rating": 92, "opponent_tire_management_rating": 84,
        "pit_crew_rating": 93, "opponent_pit_crew_rating": 82,
        "crew_chief_rating": 92, "opponent_crew_chief_rating": 84,
        "strategy_rating": 91, "opponent_strategy_rating": 84,
        "manufacturer_rating": 89, "opponent_manufacturer_rating": 85,
        "track_position_importance": 0.72, "passing_difficulty": 0.58,
        "tire_wear_rating": 0.62, "fuel_strategy_importance": 0.48,
        "pit_road_sensitivity": 0.56, "caution_probability": 0.38,
        "multi_car_wreck_probability": 0.08, "overtime_probability": 0.08,
        "weather_temperature_f": 72, "weather_wind_mph": 10,
        "weather_precipitation_probability": 0.05, "track_temperature_f": 88,
        "day_night_transition": "day", "aero_sensitivity": 0.62,
        "drafting_importance": 0.42, "superspeedway_pack_variance": 0.10,
        "road_course_skill_importance": 0.35, "short_track_contact_variance": 0.25,
        "intermediate_track_aero_variance": 0.64,
        "dnf_probability": 0.05, "opponent_dnf_probability": 0.09,
        "mechanical_failure_risk": 0.04, "opponent_mechanical_failure_risk": 0.07,
        "crash_risk": 0.05, "opponent_crash_risk": 0.08,
        "penalty_risk": 0.03, "opponent_penalty_risk": 0.06,
        "inspection_risk": 0.03, "opponent_inspection_risk": 0.05,
        "backup_car": False, "opponent_backup_car": False,
        "engine_change_penalty": False, "opponent_engine_change_penalty": False,
        "start_at_rear": False, "opponent_start_at_rear": False,
        "field_size": 36, "playoff_race": False, "elimination_race": False,
        "superspeedway_race": False, "road_course_race": False,
        "short_track_race": False, "intermediate_track_race": True,
        "restrictor_plate_style_race": False,
        "team_momentum_rating": 90, "opponent_team_momentum_rating": 84,
        "manufacturer_speed_rating": 90, "manufacturer_reliability_rating": 88,
        "manufacturer_track_type_rating": 89, "manufacturer_recent_form_rating": 88,
        "manufacturer_driver_depth_rating": 87, "book_count": 8,
    }
    data.update(extra)
    return data


def nascar_alias_inputs(**extra):
    data = {
        "race": "Daytona 500", "track_name": "Daytona International Speedway",
        "driver_name": "Kyle Larson", "team_name": "Hendrick Motorsports",
        "manufacturer_name": "Chevrolet", "opponent_name": "Denny Hamlin",
        "opponent_team_name": "Joe Gibbs Racing", "opponent_manufacturer_name": "Toyota",
        "race_series": "NASCAR Cup Series", "session": "race", "track_type": "superspeedway",
        "track_miles": 2.5, "laps": 200, "distance_miles": 500,
        "start_pos": 6, "opp_start_pos": 15, "qual_pos": 6, "opp_qual_pos": 15,
        "practice_pos": 4, "opp_practice_pos": 16,
        "single_lap_speed": 189.4, "opp_single_lap_speed": 187.8,
        "five_lap_avg": 188.5, "opp_five_lap_avg": 187.2,
        "ten_lap_avg": 187.8, "opp_ten_lap_avg": 186.4,
        "fifteen_lap_avg": 187.0, "opp_fifteen_lap_avg": 185.9,
        "driver_power_rating": 94, "opp_driver_rating": 88,
        "season_rating": 93, "opp_season_rating": 87,
        "track_history": 88, "opp_track_history": 84,
        "track_type_score": 90, "opp_track_type_score": 85,
        "recent_form": 91, "opp_recent_form": 86,
        "car_speed": 92, "opp_car_speed": 86,
        "long_run_speed": 91, "opp_long_run_speed": 85,
        "short_run_speed": 93, "opp_short_run_speed": 86,
        "clean_air_speed": 91, "opp_clean_air_speed": 85,
        "dirty_air_speed": 90, "opp_dirty_air_speed": 86,
        "restart_score": 92, "opp_restart_score": 86,
        "passing_score": 91, "opp_passing_score": 86,
        "defense_score": 89, "opp_defense_score": 86,
        "tire_mgmt": 90, "opp_tire_mgmt": 85,
        "pit_rating": 91, "opp_pit_rating": 85,
        "crew_chief": 91, "opp_crew_chief": 85,
        "strategy": 90, "opp_strategy": 85,
        "manufacturer_score": 88, "opp_manufacturer_score": 86,
        "track_position": 0.52, "pass_difficulty": 0.44,
        "tire_wear": 0.42, "fuel_strategy": 0.56,
        "pit_sensitivity": 0.48, "caution_prob": 0.62,
        "wreck_prob": 0.18, "overtime_prob": 0.20,
        "temp_f": 72, "wind_mph": 12, "precip_prob": 0.08,
        "track_temp_f": 84, "day_night": "day", "aero": 0.44,
        "drafting": 0.92, "pack_variance": 0.82,
        "road_skill": 0.28, "contact_variance": 0.42, "aero_variance": 0.44,
        "dnf_risk": 0.08, "opp_dnf_risk": 0.11,
        "mechanical_risk": 0.05, "opp_mechanical_risk": 0.08,
        "crash": 0.10, "opp_crash": 0.14,
        "penalty": 0.04, "opp_penalty": 0.06,
        "inspection": 0.03, "opp_inspection": 0.05,
        "backup": False, "opp_backup": False,
        "engine_penalty": False, "opp_engine_penalty": False,
        "rear_start": False, "opp_rear_start": False,
        "field": 36, "playoff": False, "elimination": False,
        "superspeedway": True, "road_course": False, "short_track": False,
        "intermediate": False, "restrictor_plate": True,
        "team_momentum": 88, "opp_team_momentum": 85,
        "manufacturer_speed_rating": 89, "manufacturer_reliability_rating": 87,
        "manufacturer_track_type_rating": 88, "manufacturer_recent_form_rating": 87,
        "manufacturer_driver_depth_rating": 86, "book_count": 8,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {
        "sport": "nascar", "league": "NASCAR Cup Series", "event_id": "Daytona 500",
        "event": "Daytona 500", "market": "driver_matchup", "selection": "Kyle Larson",
        "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "source_type": "unit_test",
        "screenshot_text": "Kyle Larson driver matchup +100 vs Denny Hamlin",
        "visible_markets": ["driver_matchup"], "input_stats": nascar_inputs(),
    }
    data.update(extra)
    return data


class TestNascarModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "nascar", "league": "NASCAR Cup Series",
            "event": "Daytona 500", "market": "driver_matchup", "selection": "Kyle Larson",
            "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
            "risk_profile": "moderate", "screenshot_text": "Kyle Larson driver matchup +100 vs Denny Hamlin",
            "visible_markets": ["driver_matchup"], "input_stats": nascar_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "nascar_track_position_speed_rating_pit_variance_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "nascar")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["partial_model_mode"])

    def test_bad_text_input_safety_with_valid_envelope(self):
        response = self._sport(input_stats="bad nascar text")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertNotEqual(response["decision"], "CONFIRMED_BET")

    def test_race_winner_confirmed_capable(self):
        self.assertTrue(self._sport(market="race_winner", odds_american=1400)["confirmed_bets"])

    def test_top_5_finish_active(self): self.assert_active(self._sport(market="top_5_finish"))
    def test_top_10_finish_active(self): self.assert_active(self._sport(market="top_10_finish"))
    def test_top_20_finish_active(self): self.assert_active(self._sport(market="top_20_finish"))
    def test_driver_matchup_active(self): self.assert_active(self._sport(market="driver_matchup"))
    def test_group_winner_active(self): self.assert_active(self._sport(market="group_winner"))
    def test_stage_1_winner_active(self): self.assert_active(self._sport(market="stage_1_winner"))
    def test_qualifying_matchup_active(self): self.assert_active(self._sport(market="qualifying_matchup", input_stats=nascar_inputs(session_type="qualifying")))
    def test_fastest_lap_active(self): self.assert_active(self._sport(market="fastest_lap"))
    def test_laps_led_prop_active(self): self.assert_active(self._sport(market="driver_laps_led_over", selection="over", line=25.5, input_stats=nascar_inputs(line=25.5)))
    def test_finishing_position_active(self): self.assert_active(self._sport(market="finishing_position", selection="under", line=8.5, input_stats=nascar_inputs(line=8.5)))
    def test_driver_to_retire_active(self): self.assert_active(self._sport(market="driver_to_retire"))
    def test_classified_finish_active(self): self.assert_active(self._sport(market="classified_finish"))
    def test_caution_count_over_under_active(self):
        self.assert_active(self._sport(market="caution_count_over", selection="over", line=6.5, input_stats=nascar_inputs(line=6.5)))
        self.assert_active(self._sport(market="caution_count_under", selection="under", line=6.5, input_stats=nascar_inputs(line=6.5)))

    def test_green_flag_laps_over_under_active(self):
        self.assert_active(self._sport(market="green_flag_laps_over", selection="over", line=150.5, input_stats=nascar_inputs(line=150.5)))
        self.assert_active(self._sport(market="green_flag_laps_under", selection="under", line=150.5, input_stats=nascar_inputs(line=150.5)))

    def test_negative_edge_evaluated_no_bet(self):
        self.assertEqual(self._sport(odds_american=-700)["status"], "evaluated_no_bet")

    def test_edge_too_small_evaluated_no_bet(self):
        self.assertEqual(self._sport(odds_american=-600)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_no_bet(self):
        response = self._sport(input_stats=nascar_inputs(book_count=1, superspeedway_race=True, track_type="superspeedway", caution_probability=0.70, overtime_probability=0.34, dnf_probability=0.22, crash_risk=0.24, practice_report_quality="low", qualifying_report_quality="low"))
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
        response = self._sport(input_stats={"weather": "rain", "temp_f": 72, "wind_mph": 18})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_practice_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"single_lap_speed": 189.4, "ten_lap_avg": 188.2})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_qualifying_only_enrichment_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"qual_pos": 1, "start_pos": 1, "inspection": 0.05})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_pit_road_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"pit_rating": 95, "pit_sensitivity": 0.75})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_inspection_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"inspection": 0.4, "penalty": 0.3})
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
        self.assertEqual(self._sport()["league_calibration_applied"], "nascar")

    def test_series_track_type_race_environment_calibration_fields_present(self):
        response = self._sport()
        self.assertEqual(response["series_calibration_applied"], "cup")
        self.assertEqual(response["track_type_calibration_applied"], "intermediate")
        self.assertEqual(response["race_environment_calibration_applied"], "dry")

    def test_malformed_text_numeric_fields_cannot_activate_from_defaults(self):
        malformed = deepcopy(nascar_alias_inputs())
        for key in ("driver_power_rating", "car_speed", "long_run_speed", "start_pos", "dnf_risk", "caution_prob"):
            malformed[key] = "bad text"
        response = self._screenshot(input_stats=malformed)
        analysis = response["model_analysis"]
        self.assertEqual(analysis["confirmed_bets"], [])
        self.assertNotEqual(analysis["decision"], "CONFIRMED_BET")
        self.assertTrue(analysis["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
