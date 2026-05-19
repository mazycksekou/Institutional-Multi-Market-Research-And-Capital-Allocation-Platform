import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


NFL_MISSING_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "team_offensive_epa_per_play",
    "opponent_offensive_epa_per_play",
    "team_defensive_epa_per_play",
    "opponent_defensive_epa_per_play",
    "team_success_rate",
    "opponent_success_rate",
    "team_defensive_success_rate_allowed",
    "opponent_defensive_success_rate_allowed",
    "team_explosive_play_rate",
    "opponent_explosive_play_rate",
    "team_explosive_play_rate_allowed",
    "opponent_explosive_play_rate_allowed",
    "team_turnover_rate",
    "opponent_turnover_rate",
    "team_pressure_rate_allowed",
    "opponent_pressure_rate_allowed",
    "team_pressure_rate_generated",
    "opponent_pressure_rate_generated",
    "team_red_zone_td_rate",
    "opponent_red_zone_td_rate",
    "team_red_zone_td_rate_allowed",
    "opponent_red_zone_td_rate_allowed",
    "team_pace_seconds_per_play",
    "opponent_pace_seconds_per_play",
    "qb_status",
    "offensive_line_health",
    "injury_report_status",
]


def nfl_full_inputs(**extra):
    data = {
        "team": "Bills",
        "opponent": "Jets",
        "selection": "Bills",
        "home_away": "home",
        "team_offensive_epa_per_play": 0.12,
        "opponent_offensive_epa_per_play": 0.03,
        "team_defensive_epa_per_play": -0.04,
        "opponent_defensive_epa_per_play": 0.02,
        "team_success_rate": 0.47,
        "opponent_success_rate": 0.42,
        "team_defensive_success_rate_allowed": 0.40,
        "opponent_defensive_success_rate_allowed": 0.44,
        "team_explosive_play_rate": 0.12,
        "opponent_explosive_play_rate": 0.09,
        "team_explosive_play_rate_allowed": 0.09,
        "opponent_explosive_play_rate_allowed": 0.11,
        "team_turnover_rate": 0.09,
        "opponent_turnover_rate": 0.12,
        "team_pressure_rate_allowed": 0.28,
        "opponent_pressure_rate_allowed": 0.34,
        "team_pressure_rate_generated": 0.36,
        "opponent_pressure_rate_generated": 0.29,
        "team_red_zone_td_rate": 0.62,
        "opponent_red_zone_td_rate": 0.54,
        "team_red_zone_td_rate_allowed": 0.50,
        "opponent_red_zone_td_rate_allowed": 0.58,
        "team_pace_seconds_per_play": 27.5,
        "opponent_pace_seconds_per_play": 29.0,
        "qb_status": "healthy",
        "offensive_line_health": "good",
        "injury_report_status": "clean",
        "best_available_odds": 110,
        "book_count": 8,
        "current_odds": 100,
        "consensus_odds": 105,
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "nfl",
        "league": "nfl",
        "market": "moneyline",
        "event_id": "Jets at Bills",
        "selection": "Bills",
        "odds_american": -130,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": nfl_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestNflModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "nfl",
            "league": "nfl",
            "event": "Jets at Bills",
            "teams": ["Jets", "Bills"],
            "market": "moneyline",
            "selection": "Bills",
            "odds_american": -130,
            "book": "DraftKings",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": nfl_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_nfl_missing_inputs_returns_partial_mode_and_exact_missing_inputs(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], NFL_MISSING_INPUTS)
        self.assertTrue(response["manual_review_required"])

    def test_nfl_missing_inputs_returns_no_confirmed_bets_and_zero_stake(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_nfl_full_moneyline_inputs_activate_model(self):
        response = self._sport()
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["model_name"], "drive_expected_points_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["component_statuses"]["drive_expected_points_model"], "active")

    def test_nfl_full_moneyline_inputs_return_estimated_true_probability(self):
        response = self._sport()
        self.assertIsNotNone(response["estimated_true_probability"])
        self.assertGreater(response["estimated_true_probability"], 0)
        self.assertLess(response["estimated_true_probability"], 1)
        self.assertLess(response["estimated_true_probability"], 0.90)
        self.assertIn("raw_model_probability", response)
        self.assertIn("calibrated_model_probability", response)
        self.assertIn("market_anchor_probability", response)

    def test_nfl_full_moneyline_inputs_return_edge(self):
        response = self._sport()
        self.assertIsNotNone(response["implied_probability"])
        self.assertIsNotNone(response["edge"])
        self.assertEqual(response["edge"], response["edge_percent"])

    def test_nfl_negative_edge_returns_evaluated_no_bet(self):
        response = self._sport(odds_american=-150)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["logbook_ready_row"]["status"], "evaluated_no_bet")
        self.assertEqual(response["no_bets"], [{"reason": "negative edge"}])
        self.assertFalse(response["full_board_preview"]["manual_review_required"])

    def test_nfl_positive_edge_below_threshold_returns_edge_too_small(self):
        response = self._sport(odds_american=-130)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["logbook_ready_row"]["status"], "evaluated_no_bet_edge_too_small")
        self.assertEqual(response["no_bets"], [{"reason": "edge too small"}])

    def test_nfl_positive_edge_with_confidence_passing_returns_confirmed_bet(self):
        response = self._sport(odds_american=-120)
        self.assertGreaterEqual(response["edge"], 2.0)
        self.assertGreaterEqual(response["confidence"], 65)
        self.assertTrue(response["confirmed_bets"])
        self.assertEqual(response["logbook_ready_row"]["status"], "confirmed_bet")
        self.assertEqual(response["logbook_ready_row"]["decision"], "CONFIRMED_BET")
        self.assertGreater(response["suggested_stake"], 0)
        self.assertEqual(response["no_bets"], [])

    def test_nfl_extreme_favorite_can_return_higher_probability_with_reason(self):
        response = self._sport(odds_american=-400, input_stats=nfl_full_inputs(
            team_offensive_epa_per_play=1.4,
            opponent_offensive_epa_per_play=-0.6,
            team_defensive_epa_per_play=-0.6,
            opponent_defensive_epa_per_play=0.8,
            team_success_rate=0.70,
            opponent_success_rate=0.25,
            team_defensive_success_rate_allowed=0.25,
            opponent_defensive_success_rate_allowed=0.70,
            team_explosive_play_rate=0.28,
            opponent_explosive_play_rate=0.03,
            team_explosive_play_rate_allowed=0.03,
            opponent_explosive_play_rate_allowed=0.28,
            team_pressure_rate_allowed=0.08,
            opponent_pressure_rate_allowed=0.55,
            team_pressure_rate_generated=0.60,
            opponent_pressure_rate_generated=0.08,
            team_red_zone_td_rate=0.90,
            opponent_red_zone_td_rate=0.20,
            team_red_zone_td_rate_allowed=0.20,
            opponent_red_zone_td_rate_allowed=0.90,
            team_recent_epa_per_play_3=0.50,
            opponent_recent_epa_per_play_3=-0.30,
            team_special_teams_epa=0.20,
            opponent_special_teams_epa=-0.20,
        ))
        self.assertGreaterEqual(response["projected_margin"], 10)
        self.assertGreaterEqual(response["estimated_true_probability"], 0.80)
        self.assertLessEqual(response["estimated_true_probability"], 0.85)
        self.assertIn("projected margin", response["probability_cap_reason"])

    def test_nfl_low_confidence_returns_low_confidence_status(self):
        response = self._sport(odds_american=150, input_stats=nfl_full_inputs(
            qb_status="questionable",
            offensive_line_health="poor",
            injury_report_status="uncertain",
            weather_wind_mph=22,
            book_count=3,
            best_available_odds=None,
        ))
        self.assertEqual(response["confirmed_bets"], [])
        self.assertIn("low confidence", response["no_bet_flags"])
        self.assertEqual(response["logbook_ready_row"]["status"], "evaluated_no_bet_low_confidence")

    def test_nfl_spread_requires_line(self):
        response = self._sport(market="spread", input_stats=nfl_full_inputs(market_type="spread"))
        self.assertTrue(response["partial_model_mode"])
        self.assertIn("line", response["missing_inputs"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_nfl_total_requires_total_line(self):
        response = self._sport(market="total", selection="Over", input_stats=nfl_full_inputs(market_type="total"))
        self.assertTrue(response["partial_model_mode"])
        self.assertIn("total_line", response["missing_inputs"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_nfl_officiating_data_cannot_create_confirmed_bet_when_base_missing(self):
        response = self._sport(input_stats={
            "referee_crew": "Crew A",
            "penalty_rate": 1.4,
            "holding_rate": 0.3,
            "defensive_pass_interference_rate": 0.2,
            "officiating_adjustment_probability_points": 1.5,
        })
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["officiating_module_status"], "inactive_base_model")

    def test_nfl_officiating_data_appears_in_response_when_provided(self):
        response = self._sport(input_stats=nfl_full_inputs(
            referee_crew="Crew A",
            penalty_rate=1.4,
            holding_rate=0.3,
            defensive_pass_interference_rate=0.2,
            officiating_adjustment_probability_points=0.75,
        ))
        self.assertEqual(response["officiating_module_status"], "active_adjustment")
        self.assertTrue(response["officiating_edge_detected"])
        self.assertIn("referee crew", response["officiating_analysis"]["official_type"])
        self.assertIn("officiating_module_status", response["logbook_ready_row"])

    def test_nfl_provider_failure_does_not_create_top_level_route_error(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")
        self.assertIsNone(response.get("error"))

    def test_nfl_screenshot_analysis_passes_full_inputs_to_model(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["missing_inputs"], [])
        self.assertEqual(response["model_analysis"]["model_name"], "drive_expected_points_model")
        self.assertIsNotNone(response["model_analysis"]["estimated_true_probability"])
        self.assertTrue(response["logbook_ready_rows"])

    def test_nfl_confirmed_bets_and_no_bets_are_mutually_exclusive(self):
        response = self._sport(odds_american=-120)
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        self.assertTrue(response["confirmed_bets"])
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_no_nfl_input_creates_500(self):
        bad_inputs = [
            None,
            [],
            "bad",
            {"team": "Bills"},
            nfl_full_inputs(team_offensive_epa_per_play="not-a-number"),
            nfl_full_inputs(qb_status="out", offensive_line_health="poor"),
        ]
        for input_stats in bad_inputs:
            response = self._sport(input_stats=input_stats)
            self.assertIn("ok", response)
            self.assertNotEqual(response.get("error"), "sport_analysis_failed")
            self.assertIn("full_board_preview", response)


if __name__ == "__main__":
    unittest.main()
