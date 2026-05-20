import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


NHL_MISSING_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "game_date",
    "team_projected_goals",
    "opponent_projected_goals",
    "team_xg_for_per_game",
    "opponent_xg_for_per_game",
    "team_xg_against_per_game",
    "opponent_xg_against_per_game",
    "team_goals_for_per_game",
    "opponent_goals_for_per_game",
    "team_goals_against_per_game",
    "opponent_goals_against_per_game",
    "team_shots_for_per_game",
    "opponent_shots_for_per_game",
    "team_shots_against_per_game",
    "opponent_shots_against_per_game",
    "team_scoring_chances_for_per_game",
    "opponent_scoring_chances_for_per_game",
    "team_scoring_chances_against_per_game",
    "opponent_scoring_chances_against_per_game",
    "team_high_danger_chances_for_per_game",
    "opponent_high_danger_chances_for_per_game",
    "team_high_danger_chances_against_per_game",
    "opponent_high_danger_chances_against_per_game",
    "team_power_play_percent",
    "opponent_power_play_percent",
    "team_penalty_kill_percent",
    "opponent_penalty_kill_percent",
    "team_recent_form_points",
    "opponent_recent_form_points",
    "team_rest_days",
    "opponent_rest_days",
    "team_goalie_confirmed",
    "opponent_goalie_confirmed",
    "team_starting_goalie_save_percent",
    "opponent_starting_goalie_save_percent",
    "team_starting_goalie_gsaax",
    "opponent_starting_goalie_gsaax",
    "injury_report_status",
    "lineup_status",
]


def nhl_full_inputs(**extra):
    data = {
        "team": "Rangers",
        "opponent": "Bruins",
        "selection": "Rangers",
        "home_away": "home",
        "market": "moneyline",
        "league": "nhl",
        "game_date": "2026-11-12",
        "team_projected_goals": 3.35,
        "opponent_projected_goals": 2.75,
        "team_xg_for_per_game": 3.25,
        "opponent_xg_for_per_game": 2.85,
        "team_xg_against_per_game": 2.70,
        "opponent_xg_against_per_game": 3.05,
        "team_goals_for_per_game": 3.30,
        "opponent_goals_for_per_game": 2.90,
        "team_goals_against_per_game": 2.65,
        "opponent_goals_against_per_game": 3.10,
        "team_shots_for_per_game": 32.0,
        "opponent_shots_for_per_game": 29.0,
        "team_shots_against_per_game": 28.0,
        "opponent_shots_against_per_game": 31.0,
        "team_scoring_chances_for_per_game": 29.0,
        "opponent_scoring_chances_for_per_game": 25.0,
        "team_scoring_chances_against_per_game": 24.0,
        "opponent_scoring_chances_against_per_game": 28.0,
        "team_high_danger_chances_for_per_game": 12.0,
        "opponent_high_danger_chances_for_per_game": 9.0,
        "team_high_danger_chances_against_per_game": 8.0,
        "opponent_high_danger_chances_against_per_game": 11.0,
        "team_power_play_percent": 24.0,
        "opponent_power_play_percent": 19.0,
        "team_penalty_kill_percent": 83.0,
        "opponent_penalty_kill_percent": 77.0,
        "team_recent_form_points": 8,
        "opponent_recent_form_points": 5,
        "team_rest_days": 2,
        "opponent_rest_days": 1,
        "team_goalie_confirmed": True,
        "opponent_goalie_confirmed": True,
        "team_starting_goalie_save_percent": 0.918,
        "opponent_starting_goalie_save_percent": 0.904,
        "team_starting_goalie_gsaax": 6.0,
        "opponent_starting_goalie_gsaax": -2.0,
        "injury_report_status": "clean",
        "lineup_status": "confirmed",
        "best_available_odds": 100,
        "book_count": 8,
        "current_odds": 100,
        "consensus_odds": 100,
        "team_recent_xg_for_5": 3.35,
        "opponent_recent_xg_for_5": 2.70,
        "team_recent_xg_against_5": 2.60,
        "opponent_recent_xg_against_5": 3.10,
        "team_penalties_drawn_per_game": 3.4,
        "opponent_penalties_drawn_per_game": 2.8,
        "team_penalties_taken_per_game": 2.7,
        "opponent_penalties_taken_per_game": 3.3,
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "hockey",
        "league": "nhl",
        "market": "moneyline",
        "event_id": "Rangers vs Bruins",
        "selection": "Rangers",
        "odds_american": -130,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": nhl_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestNhlModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "nhl",
            "league": "nhl",
            "event": "Rangers vs Bruins",
            "teams": ["Rangers", "Bruins"],
            "market": "moneyline",
            "selection": "Rangers",
            "odds_american": -130,
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": nhl_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_nhl_missing_inputs_returns_partial_mode_and_exact_missing_inputs(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], NHL_MISSING_INPUTS)

    def test_nhl_missing_inputs_returns_no_confirmed_bets_and_zero_stake(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_nhl_full_moneyline_inputs_activate_model(self):
        response = self._sport()
        self.assertEqual(response["model_name"], "poisson_bivariate_goalie_special_teams_model")
        self.assertEqual(response["model_status"], "active")
        self.assertFalse(response["partial_model_mode"])

    def test_nhl_full_moneyline_inputs_return_probability_and_edge(self):
        response = self._sport()
        self.assertIsNotNone(response["estimated_true_probability"])
        self.assertIsNotNone(response["edge"])
        self.assertIn("regulation_draw_probability", response)
        self.assertIn("overtime_probability", response)

    def test_nhl_negative_edge_returns_evaluated_no_bet(self):
        response = self._sport(odds_american=-300)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet")

    def test_nhl_positive_edge_below_threshold_returns_edge_too_small(self):
        response = self._sport(odds_american=-160)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet_edge_too_small")

    def test_nhl_positive_edge_with_confidence_passing_returns_confirmed_bet(self):
        response = self._sport(odds_american=100)
        self.assertGreaterEqual(response["edge"], 2.0)
        self.assertGreaterEqual(response["confidence"], 65)
        self.assertTrue(response["confirmed_bets"])
        self.assertEqual(response["status"], "confirmed_bet")

    def test_nhl_standard_moneyline_is_not_three_way_moneyline(self):
        standard = self._sport(market="moneyline", input_stats=nhl_full_inputs(market="moneyline"))
        three_way = self._sport(market="three_way_moneyline", input_stats=nhl_full_inputs(market="three_way_moneyline"))
        self.assertNotEqual(standard["estimated_true_probability"], three_way["estimated_true_probability"])
        self.assertGreater(standard["estimated_true_probability"], three_way["estimated_true_probability"])

    def test_nhl_three_way_and_regulation_moneyline_work_separately(self):
        three_way = self._sport(market="three_way_moneyline", input_stats=nhl_full_inputs(market="three_way_moneyline"))
        regulation = self._sport(market="regulation_moneyline", input_stats=nhl_full_inputs(market="regulation_moneyline"))
        self.assertEqual(three_way["model_status"], "active")
        self.assertEqual(regulation["model_status"], "active")
        self.assertAlmostEqual(three_way["estimated_true_probability"], regulation["estimated_true_probability"], places=8)

    def test_nhl_market_specific_required_inputs(self):
        self.assertIn("line", self._sport(market="puckline", input_stats=nhl_full_inputs(market="puckline"))["missing_inputs"])
        self.assertIn("total_line", self._sport(market="total", selection="Over", input_stats=nhl_full_inputs(market="total"))["missing_inputs"])
        self.assertIn("team_total_line", self._sport(market="team_total", selection="Over Rangers", input_stats=nhl_full_inputs(market="team_total"))["missing_inputs"])
        self.assertIn("player_name", self._sport(market="anytime_goal_scorer", input_stats=nhl_full_inputs(market="anytime_goal_scorer"))["missing_inputs"])
        self.assertIn("player_name", self._sport(market="first_goal_scorer", input_stats=nhl_full_inputs(market="first_goal_scorer"))["missing_inputs"])

    def test_nhl_period_and_market_outputs_work(self):
        puckline = self._sport(market="puckline", line=-1.5, input_stats=nhl_full_inputs(market="puckline", line=-1.5))
        team_total = self._sport(market="team_total", selection="Over Rangers", team_total_line=2.5, input_stats=nhl_full_inputs(market="team_total", team_total_line=2.5, selection="Over Rangers"))
        first_period_ml = self._sport(market="first_period_moneyline", input_stats=nhl_full_inputs(market="first_period_moneyline"))
        first_period_total = self._sport(market="first_period_total", selection="Over", total_line=1.5, input_stats=nhl_full_inputs(market="first_period_total", total_line=1.5, selection="Over"))
        full_total = self._sport(market="total", selection="Over", total_line=5.5, input_stats=nhl_full_inputs(market="total", total_line=5.5, selection="Over"))
        for response in [puckline, team_total, first_period_ml, first_period_total, full_total]:
            self.assertEqual(response["model_status"], "active")
        self.assertTrue(first_period_total["period_lambda_adjustment_applied"])
        self.assertNotEqual(first_period_total["estimated_true_probability"], full_total["estimated_true_probability"])

    def test_nhl_player_prop_requires_and_complete_works(self):
        missing = self._sport(market="player_prop", input_stats=nhl_full_inputs(market="player_prop"))
        for field in ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status", "player_minutes_projection"]:
            self.assertIn(field, missing["missing_inputs"])
        complete = self._sport(
            market="player_prop",
            selection="Panarin shots over",
            odds_american=110,
            input_stats=nhl_full_inputs(
                market="player_prop",
                selection="Panarin shots over",
                player_name="Artemi Panarin",
                prop_type="shots_on_goal",
                prop_line=2.5,
                player_projection=3.2,
                player_starting_status="confirmed",
                player_minutes_projection=19,
            ),
        )
        self.assertIn(complete["decision"], {"NO_BET", "CONFIRMED_BET"})
        self.assertIn("target_props", complete["full_board_preview"])

    def test_nhl_officials_data_cannot_create_bet_when_base_missing(self):
        response = self._sport(input_stats={"referee_crew": "Crew A", "referee_power_play_rate": 3.8})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["officiating_module_status"], "inactive_base_model")

    def test_nhl_officials_data_appears_when_provided(self):
        response = self._sport(input_stats=nhl_full_inputs(
            referee_crew="Crew A",
            referee_power_play_rate=3.8,
            official_sample_size=48,
            official_data_quality="strong",
            officiating_adjustment_probability_points=0.4,
        ))
        self.assertIn(response["officiating_module_status"], {"active_adjustment", "active_no_adjustment"})
        self.assertEqual(response["officiating_analysis"]["official_type"], "referees and linesmen")

    def test_nhl_provider_failure_does_not_create_top_level_route_error(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertIsNone(response.get("error"))
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")

    def test_nhl_screenshot_analysis_passes_full_inputs_to_model(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["model_analysis"]["sport"], "icehockey_nhl")
        self.assertEqual(response["model_analysis"]["model_name"], "poisson_bivariate_goalie_special_teams_model")

    def test_nhl_confirmed_bets_and_no_bets_are_mutually_exclusive(self):
        response = self._sport(odds_american=100)
        seen_confirmed = {(b["sport"], b["event"], b["market"], b["selection"]) for b in response["confirmed_bets"]}
        seen_no_bets = {
            (
                response["sport"],
                response.get("event_id") or response["full_board_preview"]["logbook_ready_rows"][0].get("event"),
                response["market"],
                sport_payload()["selection"],
            )
            for _ in response["no_bets"]
        }
        self.assertTrue(seen_confirmed)
        self.assertTrue(seen_confirmed.isdisjoint(seen_no_bets))

    def test_nhl_same_stats_keep_probability_stable_as_odds_change(self):
        minus_130 = self._sport(odds_american=-130)
        plus_100 = self._sport(odds_american=100)
        plus_120 = self._sport(odds_american=120)
        probabilities = [r["final_probability"] for r in [minus_130, plus_100, plus_120]]
        self.assertLess(max(probabilities) - min(probabilities), 0.03)
        self.assertGreater(minus_130["implied_probability"], plus_100["implied_probability"])
        self.assertGreater(plus_100["implied_probability"], plus_120["implied_probability"])
        self.assertLess(minus_130["edge"], plus_100["edge"])
        self.assertLess(plus_100["edge"], plus_120["edge"])

    def test_nhl_adjustment_flags_are_exposed(self):
        response = self._sport()
        self.assertTrue(response["bivariate_poisson_adjustment_applied"])
        self.assertTrue(response["goalie_adjustment_applied"])
        self.assertTrue(response["special_teams_adjustment_applied"])
        self.assertTrue(response["time_decay_applied"])

    def test_no_nhl_input_creates_500(self):
        bad_payloads = [
            {"input_stats": None},
            {"input_stats": "not json"},
            {"input_stats": {"team_projected_goals": "bad", "opponent_projected_goals": object()}},
        ]
        for payload in bad_payloads:
            response = self._sport(**payload)
            self.assertTrue(response["ok"])
            self.assertEqual(response["confirmed_bets"], [])


if __name__ == "__main__":
    unittest.main()
