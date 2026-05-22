import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


SOCCER_MISSING_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "match_date",
    "team_expected_goals",
    "opponent_expected_goals",
    "team_xg_for",
    "opponent_xg_for",
    "team_xg_against",
    "opponent_xg_against",
    "team_goals_for_per_match",
    "opponent_goals_for_per_match",
    "team_goals_against_per_match",
    "opponent_goals_against_per_match",
    "team_shots_per_match",
    "opponent_shots_per_match",
    "team_shots_allowed_per_match",
    "opponent_shots_allowed_per_match",
    "team_shots_on_target_per_match",
    "opponent_shots_on_target_per_match",
    "team_shots_on_target_allowed_per_match",
    "opponent_shots_on_target_allowed_per_match",
    "team_big_chances_per_match",
    "opponent_big_chances_per_match",
    "team_big_chances_allowed_per_match",
    "opponent_big_chances_allowed_per_match",
    "team_possession_percent",
    "opponent_possession_percent",
    "team_recent_form_points",
    "opponent_recent_form_points",
    "team_rest_days",
    "opponent_rest_days",
    "injury_report_status",
    "lineup_status",
]


def soccer_full_inputs(**extra):
    data = {
        "team": "Arsenal",
        "opponent": "Chelsea",
        "selection": "Arsenal",
        "home_away": "home",
        "market": "three_way_moneyline",
        "league": "soccer_epl",
        "match_date": "2026-08-15",
        "team_expected_goals": 1.75,
        "opponent_expected_goals": 1.05,
        "team_xg_for": 1.80,
        "opponent_xg_for": 1.20,
        "team_xg_against": 1.05,
        "opponent_xg_against": 1.45,
        "team_goals_for_per_match": 2.0,
        "opponent_goals_for_per_match": 1.35,
        "team_goals_against_per_match": 0.95,
        "opponent_goals_against_per_match": 1.45,
        "team_shots_per_match": 15.2,
        "opponent_shots_per_match": 11.3,
        "team_shots_allowed_per_match": 9.2,
        "opponent_shots_allowed_per_match": 13.4,
        "team_shots_on_target_per_match": 5.8,
        "opponent_shots_on_target_per_match": 4.1,
        "team_shots_on_target_allowed_per_match": 3.1,
        "opponent_shots_on_target_allowed_per_match": 4.9,
        "team_big_chances_per_match": 2.8,
        "opponent_big_chances_per_match": 1.7,
        "team_big_chances_allowed_per_match": 1.2,
        "opponent_big_chances_allowed_per_match": 2.2,
        "team_possession_percent": 58,
        "opponent_possession_percent": 49,
        "team_recent_form_points": 12,
        "opponent_recent_form_points": 8,
        "team_rest_days": 6,
        "opponent_rest_days": 4,
        "injury_report_status": "clean",
        "lineup_status": "confirmed",
        "best_available_odds": 100,
        "book_count": 8,
        "current_odds": 100,
        "consensus_odds": 100,
        "team_recent_xg_for_5": 1.9,
        "opponent_recent_xg_for_5": 1.15,
        "team_recent_xg_against_5": 0.95,
        "opponent_recent_xg_against_5": 1.55,
        "team_corner_rate": 6.0,
        "opponent_corner_rate": 4.6,
        "team_cards_per_match": 1.8,
        "opponent_cards_per_match": 2.2,
    }
    data.update(extra)
    return data


def soccer_live_smoke_inputs(**extra):
    data = soccer_full_inputs(
        team="Arsenal",
        opponent="Chelsea",
        selection="Arsenal",
        market="three_way_moneyline",
        league="soccer_epl",
        match_date="2026-08-15",
        best_available_odds=100,
        current_odds=100,
        consensus_odds=100,
        book_count=8,
    )
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "football",
        "league": "soccer_epl",
        "market": "three_way_moneyline",
        "event_id": "Arsenal vs Chelsea",
        "selection": "Arsenal",
        "odds_american": -130,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": soccer_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestSoccerModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "soccer",
            "league": "soccer_epl",
            "event": "Arsenal vs Chelsea",
            "teams": ["Arsenal", "Chelsea"],
            "market": "three_way_moneyline",
            "selection": "Arsenal",
            "odds_american": -130,
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": soccer_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_soccer_missing_inputs_returns_partial_mode_and_exact_missing_inputs(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], SOCCER_MISSING_INPUTS)

    def test_soccer_missing_inputs_returns_no_confirmed_bets_and_zero_stake(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_soccer_full_three_way_inputs_activate_model(self):
        response = self._sport()
        self.assertEqual(response["model_name"], "poisson_dixon_coles_bivariate_goal_model")
        self.assertEqual(response["model_status"], "active")
        self.assertFalse(response["partial_model_mode"])

    def test_soccer_full_inputs_return_probability_and_edge(self):
        response = self._sport()
        self.assertIsNotNone(response["estimated_true_probability"])
        self.assertIsNotNone(response["edge"])
        self.assertIn("team_lambda", response)
        self.assertIn("draw_probability", response)

    def test_soccer_negative_edge_returns_evaluated_no_bet(self):
        response = self._sport(odds_american=-300)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet")

    def test_soccer_positive_edge_below_threshold_returns_edge_too_small(self):
        response = self._sport(odds_american=-105)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet_edge_too_small")

    def test_soccer_positive_edge_with_confidence_passing_returns_confirmed_bet(self):
        response = self._sport(odds_american=100)
        self.assertGreaterEqual(response["edge"], 2.0)
        self.assertGreaterEqual(response["confidence"], 65)
        self.assertTrue(response["confirmed_bets"])
        self.assertEqual(response["status"], "confirmed_bet")

    def test_soccer_market_specific_missing_inputs(self):
        self.assertIn("total_line", self._sport(market="total", selection="Over", input_stats=soccer_full_inputs(market="total"))["missing_inputs"])
        self.assertIn("team_total_line", self._sport(market="team_total", selection="Over Arsenal", input_stats=soccer_full_inputs(market="team_total"))["missing_inputs"])
        self.assertIn("line", self._sport(market="asian_handicap", input_stats=soccer_full_inputs(market="asian_handicap"))["missing_inputs"])
        self.assertIn("corner_line", self._sport(market="corners", input_stats=soccer_full_inputs(market="corners"))["missing_inputs"])
        self.assertIn("card_line", self._sport(market="cards", input_stats=soccer_full_inputs(market="cards"))["missing_inputs"])
        self.assertIn("player_name", self._sport(market="anytime_goal_scorer", input_stats=soccer_full_inputs(market="anytime_goal_scorer"))["missing_inputs"])

    def test_soccer_btts_and_correct_score_work(self):
        btts = self._sport(market="both_teams_to_score", selection="BTTS Yes", odds_american=110, input_stats=soccer_full_inputs(market="both_teams_to_score", selection="BTTS Yes"))
        correct = self._sport(market="correct_score", selection="2-1", correct_score_selection="2-1", odds_american=700, input_stats=soccer_full_inputs(market="correct_score", selection="2-1", correct_score_selection="2-1"))
        self.assertEqual(btts["model_status"], "active")
        self.assertEqual(correct["model_status"], "active")
        self.assertIn(correct["risk"], {"high", "medium"})

    def test_soccer_first_half_total_uses_first_half_lambda_scaling(self):
        full = self._sport(market="total", selection="Over", total_line=2.5, input_stats=soccer_full_inputs(market="total", total_line=2.5, selection="Over"))
        first_half = self._sport(market="first_half_total", selection="Over", total_line=1.0, input_stats=soccer_full_inputs(market="first_half_total", total_line=1.0, selection="Over"))
        self.assertEqual(first_half["model_status"], "active")
        self.assertNotEqual(first_half["estimated_true_probability"], full["estimated_true_probability"])

    def test_soccer_player_prop_requires_and_complete_works(self):
        missing = self._sport(market="player_prop", input_stats=soccer_full_inputs(market="player_prop"))
        for field in ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status", "player_minutes_projection"]:
            self.assertIn(field, missing["missing_inputs"])
        complete = self._sport(
            market="player_prop",
            selection="Saka shots over",
            odds_american=110,
            input_stats=soccer_full_inputs(
                market="player_prop",
                selection="Saka shots over",
                player_name="Bukayo Saka",
                prop_type="shots",
                prop_line=2.5,
                player_projection=3.0,
                player_starting_status="confirmed",
                player_minutes_projection=84,
            ),
        )
        self.assertIn(complete["decision"], {"NO_BET", "CONFIRMED_BET"})
        self.assertIn("target_props", complete["full_board_preview"])

    def test_soccer_referee_data_cannot_create_bet_when_base_missing(self):
        response = self._sport(input_stats={"referee_name": "Test Ref", "referee_cards_per_match": 5.5})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["officiating_module_status"], "inactive_base_model")

    def test_soccer_referee_data_appears_when_provided(self):
        response = self._sport(input_stats=soccer_full_inputs(
            referee_name="Test Ref",
            referee_cards_per_match=5.5,
            referee_penalty_rate=0.18,
            official_sample_size=50,
            official_data_quality="strong",
            officiating_adjustment_probability_points=0.4,
        ))
        self.assertIn(response["officiating_module_status"], {"active_adjustment", "active_no_adjustment"})
        self.assertEqual(response["officiating_analysis"]["official_type"], "referee")

    def test_soccer_provider_failure_does_not_create_top_level_route_error(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertIsNone(response.get("error"))
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")

    def test_soccer_screenshot_analysis_passes_full_inputs_to_model(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["model_analysis"]["model_name"], "poisson_dixon_coles_bivariate_goal_model")

    def test_soccer_live_smoke_active_payload_reaches_active_model(self):
        response = self._screenshot(
            input_stats=soccer_live_smoke_inputs(),
            odds_american=100,
        )
        analysis = response["model_analysis"]
        self.assertTrue(response["ok"])
        self.assertEqual(analysis["model_name"], "poisson_dixon_coles_bivariate_goal_model")
        self.assertEqual(analysis["model_status"], "active")
        self.assertIsNotNone(analysis["final_probability"])
        self.assertEqual(analysis["missing_inputs"], [])
        self.assertNotEqual(analysis["decision"], "manual_review_required")
        if response["confirmed_bets"]:
            confirmed = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["confirmed_bets"]}
            no_bets = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["no_bets"]}
            self.assertFalse(confirmed & no_bets)

    def test_soccer_confirmed_bets_and_no_bets_are_mutually_exclusive(self):
        response = self._sport(odds_american=100)
        confirmed_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["confirmed_bets"]}
        no_bet_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_soccer_same_stats_keep_probability_stable_as_odds_change(self):
        responses = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probabilities = [responses[odds]["final_probability"] for odds in (-130, 100, 120)]
        implied = [responses[odds]["implied_probability"] for odds in (-130, 100, 120)]
        edges = [responses[odds]["edge_percent"] for odds in (-130, 100, 120)]
        self.assertLess(max(probabilities) - min(probabilities), 0.03)
        self.assertGreater(implied[0], implied[1])
        self.assertGreater(implied[1], implied[2])
        self.assertLess(edges[0], edges[1])
        self.assertLess(edges[1], edges[2])

    def test_soccer_adjustment_flags_are_exposed(self):
        response = self._sport()
        self.assertTrue(response["dixon_coles_adjustment_applied"])
        self.assertTrue(response["bivariate_poisson_adjustment_applied"])
        self.assertTrue(response["time_decay_applied"])

    def test_soccer_draw_no_bet_double_chance_handicap_team_total_and_total_work(self):
        cases = [
            self._sport(market="draw_no_bet", odds_american=-130, input_stats=soccer_full_inputs(market="draw_no_bet")),
            self._sport(market="double_chance", selection="1X", odds_american=-160, input_stats=soccer_full_inputs(market="double_chance", selection="1X")),
            self._sport(market="asian_handicap", line=-0.5, input_stats=soccer_full_inputs(market="asian_handicap", line=-0.5)),
            self._sport(market="total", selection="Over", total_line=2.5, input_stats=soccer_full_inputs(market="total", total_line=2.5, selection="Over")),
            self._sport(market="team_total", selection="Over Arsenal", team_total_line=1.5, input_stats=soccer_full_inputs(market="team_total", team_total_line=1.5, selection="Over Arsenal")),
        ]
        for response in cases:
            self.assertEqual(response["model_status"], "active")
            self.assertIsNotNone(response["estimated_true_probability"])

    def test_no_soccer_input_creates_500(self):
        bad_inputs = [
            None,
            [],
            "bad",
            {"team": "Arsenal"},
            soccer_full_inputs(team_expected_goals="bad"),
            soccer_full_inputs(lineup_status="unconfirmed"),
        ]
        for input_stats in bad_inputs:
            response = self._sport(input_stats=input_stats)
            self.assertIn("ok", response)
            self.assertNotEqual(response.get("error"), "sport_analysis_failed")
            self.assertIn("full_board_preview", response)


if __name__ == "__main__":
    unittest.main()
