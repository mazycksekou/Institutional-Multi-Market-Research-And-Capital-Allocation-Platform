import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


MLB_MISSING_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "team_projected_runs",
    "opponent_projected_runs",
    "team_starting_pitcher",
    "opponent_starting_pitcher",
    "team_starting_pitcher_era",
    "opponent_starting_pitcher_era",
    "team_starting_pitcher_fip",
    "opponent_starting_pitcher_fip",
    "team_starting_pitcher_xfip",
    "opponent_starting_pitcher_xfip",
    "team_starting_pitcher_k_rate",
    "opponent_starting_pitcher_k_rate",
    "team_starting_pitcher_bb_rate",
    "opponent_starting_pitcher_bb_rate",
    "team_starting_pitcher_hr_rate",
    "opponent_starting_pitcher_hr_rate",
    "team_starting_pitcher_innings_projection",
    "opponent_starting_pitcher_innings_projection",
    "team_bullpen_era",
    "opponent_bullpen_era",
    "team_bullpen_fip",
    "opponent_bullpen_fip",
    "team_bullpen_recent_usage",
    "opponent_bullpen_recent_usage",
    "team_bullpen_rest_status",
    "opponent_bullpen_rest_status",
    "team_woba",
    "opponent_woba",
    "team_xwoba",
    "opponent_xwoba",
    "team_wrc_plus",
    "opponent_wrc_plus",
    "team_iso",
    "opponent_iso",
    "team_k_rate",
    "opponent_k_rate",
    "team_bb_rate",
    "opponent_bb_rate",
    "park_factor_runs",
    "park_factor_home_runs",
    "weather_temperature",
    "weather_wind_mph",
    "weather_wind_direction",
    "roof_status",
    "injury_report_status",
    "lineup_status",
]


def mlb_full_inputs(**extra):
    data = {
        "team": "Dodgers",
        "opponent": "Giants",
        "selection": "Dodgers",
        "home_away": "home",
        "market": "moneyline",
        "team_projected_runs": 4.8,
        "opponent_projected_runs": 4.1,
        "team_starting_pitcher": "Dodgers SP",
        "opponent_starting_pitcher": "Giants SP",
        "team_starting_pitcher_era": 3.2,
        "opponent_starting_pitcher_era": 4.2,
        "team_starting_pitcher_fip": 3.3,
        "opponent_starting_pitcher_fip": 4.4,
        "team_starting_pitcher_xfip": 3.4,
        "opponent_starting_pitcher_xfip": 4.3,
        "team_starting_pitcher_k_rate": 0.27,
        "opponent_starting_pitcher_k_rate": 0.22,
        "team_starting_pitcher_bb_rate": 0.07,
        "opponent_starting_pitcher_bb_rate": 0.09,
        "team_starting_pitcher_hr_rate": 0.9,
        "opponent_starting_pitcher_hr_rate": 1.2,
        "team_starting_pitcher_innings_projection": 5.8,
        "opponent_starting_pitcher_innings_projection": 5.1,
        "team_bullpen_era": 3.6,
        "opponent_bullpen_era": 4.3,
        "team_bullpen_fip": 3.7,
        "opponent_bullpen_fip": 4.2,
        "team_bullpen_recent_usage": 2.0,
        "opponent_bullpen_recent_usage": 3.2,
        "team_bullpen_rest_status": "rested",
        "opponent_bullpen_rest_status": "tired",
        "team_woba": 0.335,
        "opponent_woba": 0.310,
        "team_xwoba": 0.340,
        "opponent_xwoba": 0.315,
        "team_wrc_plus": 112,
        "opponent_wrc_plus": 96,
        "team_iso": 0.180,
        "opponent_iso": 0.145,
        "team_k_rate": 0.21,
        "opponent_k_rate": 0.24,
        "team_bb_rate": 0.09,
        "opponent_bb_rate": 0.075,
        "park_factor_runs": 1.02,
        "park_factor_home_runs": 1.05,
        "weather_temperature": 74,
        "weather_wind_mph": 8,
        "weather_wind_direction": "left to right",
        "roof_status": "open",
        "injury_report_status": "clean",
        "lineup_status": "confirmed",
        "best_available_odds": 100,
        "book_count": 8,
        "current_odds": 100,
        "consensus_odds": 100,
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "mlb",
        "league": "mlb",
        "market": "moneyline",
        "event_id": "Giants at Dodgers",
        "selection": "Dodgers",
        "odds_american": -130,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": mlb_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestMlbModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "mlb",
            "league": "mlb",
            "event": "Giants at Dodgers",
            "teams": ["Giants", "Dodgers"],
            "market": "moneyline",
            "selection": "Dodgers",
            "odds_american": -130,
            "book": "DraftKings",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": mlb_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_mlb_missing_inputs_returns_partial_mode_and_exact_missing_inputs(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], MLB_MISSING_INPUTS)

    def test_mlb_missing_inputs_returns_no_confirmed_bets_and_zero_stake(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_mlb_full_moneyline_inputs_activate_negative_binomial_model(self):
        response = self._sport()
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["model_name"], "negative_binomial_run_model")
        self.assertEqual(response["model_status"], "active")

    def test_mlb_full_moneyline_inputs_return_probability_and_edge(self):
        response = self._sport()
        self.assertIsNotNone(response["estimated_true_probability"])
        self.assertIsNotNone(response["edge"])
        self.assertIn("raw_model_probability", response)
        self.assertIn("projected_team_runs", response)

    def test_mlb_negative_edge_returns_evaluated_no_bet(self):
        response = self._sport(odds_american=-400)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet")

    def test_mlb_positive_edge_below_threshold_returns_edge_too_small(self):
        response = self._sport(odds_american=-145)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet_edge_too_small")

    def test_mlb_positive_edge_with_confidence_passing_returns_confirmed_bet(self):
        response = self._sport(odds_american=100)
        self.assertGreaterEqual(response["edge"], 2.0)
        self.assertGreaterEqual(response["confidence"], 65)
        self.assertTrue(response["confirmed_bets"])
        self.assertEqual(response["status"], "confirmed_bet")

    def test_mlb_market_specific_required_inputs(self):
        self.assertIn("line", self._sport(market="runline", input_stats=mlb_full_inputs(market="runline"))["missing_inputs"])
        self.assertIn("total_line", self._sport(market="total", selection="Over", input_stats=mlb_full_inputs(market="total"))["missing_inputs"])
        self.assertIn("team_total_line", self._sport(market="team_total", selection="Over Dodgers", input_stats=mlb_full_inputs(market="team_total"))["missing_inputs"])
        self.assertIn("total_line", self._sport(market="first_5_total", selection="Over", input_stats=mlb_full_inputs(market="first_5_total"))["missing_inputs"])

    def test_mlb_first_5_moneyline_uses_period_specific_projection(self):
        full_game = self._sport()
        first_5 = self._sport(market="first_5_moneyline", input_stats=mlb_full_inputs(market="first_5_moneyline"))
        self.assertEqual(first_5["model_status"], "active")
        self.assertLess(first_5["projected_total_runs"], full_game["projected_total_runs"])

    def test_mlb_player_prop_requires_complete_inputs(self):
        response = self._sport(market="player_prop", input_stats=mlb_full_inputs(market="player_prop"))
        for field in ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status"]:
            self.assertIn(field, response["missing_inputs"])

    def test_mlb_player_prop_complete_inputs_returns_clean_result(self):
        response = self._sport(
            market="player_prop",
            selection="Mookie Betts hits over",
            odds_american=110,
            input_stats=mlb_full_inputs(
                market="player_prop",
                selection="Mookie Betts hits over",
                player_name="Mookie Betts",
                prop_type="hits",
                prop_line=1.5,
                player_projection=1.7,
                player_starting_status="confirmed",
            ),
        )
        self.assertIn(response["decision"], {"NO_BET", "CONFIRMED_BET"})
        self.assertIn("target_props", response["full_board_preview"])

    def test_mlb_umpire_data_cannot_create_bet_when_base_missing(self):
        response = self._sport(input_stats={
            "umpire_name": "Test Umpire",
            "umpire_called_strike_rate": 0.64,
            "umpire_over_rate": 0.58,
        })
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["officiating_module_status"], "inactive_base_model")

    def test_mlb_umpire_data_appears_when_provided(self):
        response = self._sport(input_stats=mlb_full_inputs(
            umpire_name="Test Umpire",
            umpire_called_strike_rate=0.64,
            umpire_over_rate=0.58,
            official_sample_size=80,
            official_data_quality="strong",
            officiating_adjustment_probability_points=0.5,
        ))
        self.assertIn(response["officiating_module_status"], {"active_adjustment", "active_no_adjustment"})
        self.assertIn("umpire", response["officiating_analysis"]["official_type"])

    def test_mlb_provider_failure_does_not_create_top_level_route_error(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertIsNone(response.get("error"))
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")

    def test_mlb_screenshot_analysis_passes_full_inputs_to_model(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["missing_inputs"], [])
        self.assertEqual(response["model_analysis"]["model_name"], "negative_binomial_run_model")

    def test_mlb_confirmed_bets_and_no_bets_are_mutually_exclusive(self):
        response = self._sport(odds_american=100)
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_mlb_same_stats_keep_probability_stable_as_odds_change(self):
        responses = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probabilities = [responses[odds]["final_probability"] for odds in (-130, 100, 120)]
        implied = [responses[odds]["implied_probability"] for odds in (-130, 100, 120)]
        edges = [responses[odds]["edge_percent"] for odds in (-130, 100, 120)]
        self.assertLess(max(probabilities) - min(probabilities), 0.03)
        self.assertGreater(implied[0], implied[1])
        self.assertGreater(implied[1], implied[2])
        self.assertLess(edges[0], edges[1])
        self.assertLess(edges[1], edges[2])

    def test_mlb_total_over_and_under_work(self):
        over = self._sport(market="total", selection="Over", total_line=8.5, input_stats=mlb_full_inputs(market="total", total_line=8.5))
        under = self._sport(market="total", selection="Under", total_line=11.5, input_stats=mlb_full_inputs(market="total", total_line=11.5, selection="Under"))
        self.assertEqual(over["model_status"], "active")
        self.assertEqual(under["model_status"], "active")
        self.assertIsNotNone(over["estimated_true_probability"])
        self.assertIsNotNone(under["estimated_true_probability"])

    def test_mlb_runline_favorite_and_underdog_work(self):
        favorite = self._sport(market="runline", line=-1.5, input_stats=mlb_full_inputs(market="runline", line=-1.5))
        underdog = self._sport(market="runline", line=1.5, input_stats=mlb_full_inputs(market="runline", line=1.5, selection="Giants"))
        self.assertEqual(favorite["model_status"], "active")
        self.assertEqual(underdog["model_status"], "active")

    def test_mlb_team_total_over_and_under_work(self):
        over = self._sport(market="team_total", selection="Over Dodgers", team_total_line=4.5, input_stats=mlb_full_inputs(market="team_total", team_total_line=4.5))
        under = self._sport(market="team_total", selection="Under Dodgers", team_total_line=6.5, input_stats=mlb_full_inputs(market="team_total", team_total_line=6.5, selection="Under Dodgers"))
        self.assertEqual(over["model_status"], "active")
        self.assertEqual(under["model_status"], "active")

    def test_no_mlb_input_creates_500(self):
        bad_inputs = [
            None,
            [],
            "bad",
            {"team": "Dodgers"},
            mlb_full_inputs(team_projected_runs="bad"),
            mlb_full_inputs(lineup_status="unconfirmed"),
        ]
        for input_stats in bad_inputs:
            response = self._sport(input_stats=input_stats)
            self.assertIn("ok", response)
            self.assertNotEqual(response.get("error"), "sport_analysis_failed")
            self.assertIn("full_board_preview", response)


if __name__ == "__main__":
    unittest.main()
