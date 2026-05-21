import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


GOLF_MISSING_INPUTS = [
    "player", "field_size", "event", "course", "player_world_rank", "player_sg_total",
    "player_sg_off_tee", "player_sg_approach", "player_sg_around_green", "player_sg_putting",
    "player_recent_form_rank", "player_recent_scoring_average", "course_fit_score",
    "course_history_score", "field_strength", "cut_line_projection", "weather_wind_rating",
    "course_difficulty_rating",
]


def golf_full_inputs(**extra):
    data = {
        "player": "Scottie Scheffler",
        "field_size": 120,
        "event": "The Players Championship",
        "course": "TPC Sawgrass",
        "market": "top_10",
        "selection": "Scottie Scheffler",
        "player_world_rank": 1,
        "player_sg_total": 2.4,
        "player_sg_off_tee": 0.8,
        "player_sg_approach": 1.2,
        "player_sg_around_green": 0.2,
        "player_sg_putting": 0.2,
        "player_recent_form_rank": 3,
        "player_recent_scoring_average": 68.9,
        "course_fit_score": 90,
        "course_history_score": 82,
        "field_strength": 88,
        "cut_line_projection": 88,
        "weather_wind_rating": 25,
        "course_difficulty_rating": 74,
        "book_count": 8,
        "opponent": "Rory McIlroy",
        "opponent_world_rank": 2,
        "opponent_sg_total": 1.8,
        "opponent_sg_off_tee": 0.9,
        "opponent_sg_approach": 0.6,
        "opponent_sg_around_green": 0.1,
        "opponent_sg_putting": 0.2,
        "opponent_recent_form_rank": 8,
        "opponent_recent_scoring_average": 69.4,
        "opponent_course_fit_score": 82,
        "opponent_course_history_score": 78,
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "golf",
        "league": "pga",
        "market": "top_10",
        "event_id": "The Players Championship",
        "selection": "Scottie Scheffler",
        "odds_american": 100,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": golf_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestGolfModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "golf",
            "league": "pga",
            "event": "The Players Championship",
            "market": "top_10",
            "selection": "Scottie Scheffler",
            "odds_american": 100,
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": golf_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["ok"])
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], GOLF_MISSING_INPUTS)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["logbook_ready_rows"][0]["decision"], "NO_BET")
        self.assertEqual(response["logbook_ready_rows"][0]["stake"], 0)

    def test_bad_text_input_safety(self):
        for payload in [{"input_stats": None}, {"input_stats": "golf ticket text"}, {"odds_american": "bad"}]:
            with self.subTest(payload=payload):
                response = self._sport(**payload)
                self.assertTrue(response["ok"])
                self.assertEqual(response["confirmed_bets"], [])
                self.assertEqual(response["suggested_stake"], 0)
                self.assertEqual(response["logbook_ready_rows"][0]["decision"], "NO_BET")

    def test_top_10_confirmed_capable(self):
        response = self._sport(market="top_10", odds_american=100, input_stats=golf_full_inputs(market="top_10"))
        self.assertEqual(response["model_name"], "strokes_gained_course_fit_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["status"], "confirmed_bet")
        self.assertTrue(response["confirmed_bets"])
        self.assertGreater(response["suggested_stake"], 0)

    def test_top_20_market_active(self):
        response = self._sport(market="top_20", odds_american=-160, input_stats=golf_full_inputs(market="top_20"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["final_probability"])

    def test_outright_winner_active(self):
        response = self._sport(market="outright_winner", odds_american=1200, input_stats=golf_full_inputs(market="outright_winner"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["outright_win_probability"])

    def test_make_cut_active(self):
        response = self._sport(market="make_cut", odds_american=-180, input_stats=golf_full_inputs(market="make_cut"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["make_cut_probability"])

    def test_miss_cut_active(self):
        response = self._sport(market="miss_cut", odds_american=500, input_stats=golf_full_inputs(market="miss_cut"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["miss_cut_probability"])

    def test_tournament_matchup_active(self):
        response = self._sport(market="tournament_matchup", odds_american=100, input_stats=golf_full_inputs(market="tournament_matchup"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["final_probability"])

    def test_round_matchup_active(self):
        response = self._sport(market="round_matchup", odds_american=100, input_stats=golf_full_inputs(market="round_matchup"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["final_probability"])

    def test_three_ball_active(self):
        response = self._sport(market="three_ball", odds_american=150, input_stats=golf_full_inputs(market="three_ball"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["final_probability"])

    def test_first_round_leader_active(self):
        response = self._sport(market="first_round_leader", odds_american=10000, input_stats=golf_full_inputs(market="first_round_leader"))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["final_probability"])

    def test_finishing_position_active(self):
        response = self._sport(market="finishing_position", line=10, odds_american=100, input_stats=golf_full_inputs(market="finishing_position", line=10))
        self.assertEqual(response["model_status"], "active")
        self.assertIsNotNone(response["final_probability"])

    def test_birdies_prop_active(self):
        response = self._sport(market="birdies_prop", selection="Scottie birdies over", line=3.5, odds_american=100, input_stats=golf_full_inputs(market="birdies_prop", line=3.5, selection="Scottie birdies over"))
        self.assertEqual(response["model_status"], "active")
        self.assertTrue(response["full_board_preview"]["target_props"])

    def test_fairways_hit_prop_active(self):
        response = self._sport(market="fairways_hit_prop", selection="Scottie fairways over", line=8.5, odds_american=100, input_stats=golf_full_inputs(market="fairways_hit_prop", line=8.5, selection="Scottie fairways over"))
        self.assertEqual(response["model_status"], "active")
        self.assertTrue(response["full_board_preview"]["target_props"])

    def test_greens_in_regulation_prop_active(self):
        response = self._sport(market="greens_in_regulation_prop", selection="Scottie GIR over", line=12.5, odds_american=100, input_stats=golf_full_inputs(market="greens_in_regulation_prop", line=12.5, selection="Scottie GIR over"))
        self.assertEqual(response["model_status"], "active")
        self.assertTrue(response["full_board_preview"]["target_props"])

    def test_putts_prop_active(self):
        response = self._sport(market="putts_prop", selection="Scottie putts under", line=29.5, odds_american=100, input_stats=golf_full_inputs(market="putts_prop", line=29.5, selection="Scottie putts under"))
        self.assertEqual(response["model_status"], "active")
        self.assertTrue(response["full_board_preview"]["target_props"])

    def test_round_score_prop_active(self):
        response = self._sport(market="round_score_prop", selection="Scottie score under", line=70.5, odds_american=100, input_stats=golf_full_inputs(market="round_score_prop", line=70.5, selection="Scottie score under"))
        self.assertEqual(response["model_status"], "active")
        self.assertTrue(response["full_board_preview"]["target_props"])

    def test_negative_edge_evaluated_no_bet(self):
        response = self._sport(market="top_10", odds_american=-500, input_stats=golf_full_inputs(market="top_10"))
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["status"], "evaluated_no_bet")
        self.assertEqual(response["confirmed_bets"], [])

    def test_edge_too_small_evaluated_no_bet(self):
        response = self._sport(market="top_10", odds_american=-300, input_stats=golf_full_inputs(market="top_10"))
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["status"], "evaluated_no_bet_edge_too_small")
        self.assertEqual(response["suggested_stake"], 0)

    def test_low_confidence_no_bet(self):
        response = self._sport(
            market="first_round_leader",
            odds_american=10000,
            input_stats=golf_full_inputs(market="first_round_leader", weather_wind_rating=95),
        )
        self.assertLess(response["confidence"], 65)
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")
        self.assertEqual(response["confirmed_bets"], [])

    def test_odds_stability_across_prices(self):
        minus_130 = self._sport(odds_american=-130)
        plus_100 = self._sport(odds_american=100)
        plus_120 = self._sport(odds_american=120)
        probabilities = [result["final_probability"] for result in [minus_130, plus_100, plus_120]]
        raw_probabilities = [result["raw_model_probability"] for result in [minus_130, plus_100, plus_120]]
        self.assertLess(max(probabilities) - min(probabilities), 0.03)
        self.assertLess(max(raw_probabilities) - min(raw_probabilities), 0.000001)
        self.assertLess(minus_130["edge"], plus_100["edge"])
        self.assertLess(plus_100["edge"], plus_120["edge"])

    def test_provider_failure_safety(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")
        self.assertEqual(response["model_analysis"]["model_status"], "active")

    def test_weather_course_social_only_cannot_create_bets(self):
        response = self._sport(input_stats={"weather_wind_rating": 90, "course_fit_score": 95, "social_sentiment": "strong"})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_screenshot_analysis_live_alias_path(self):
        response = self._screenshot(
            sport="golf",
            market="top_10",
            selection="Scottie Scheffler",
            odds_american=100,
            input_stats={
                "golfer_name": "Scottie Scheffler",
                "players_in_field": 120,
                "tournament": "The Players Championship",
                "course_name": "TPC Sawgrass",
                "owgr_rank": 1,
                "sg_total": 2.4,
                "sg_off_tee": 0.8,
                "sg_approach": 1.2,
                "sg_around_green": 0.2,
                "sg_putting": 0.2,
                "recent_form_rank": 3,
                "recent_scoring_average": 68.9,
                "fit_score": 90,
                "history_score": 82,
                "field_strength_rating": 88,
                "projected_cut_probability": 0.88,
                "wind_rating": 25,
                "difficulty_rating": 74,
            },
        )
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["model_analysis"]["model_status"], "active")
        self.assertEqual(response["model_analysis"]["missing_inputs"], [])
        self.assertIsNotNone(response["model_analysis"]["final_probability"])
        self.assertEqual(response["model_analysis"]["implied_probability"], 0.5)
        self.assertNotEqual(response["model_analysis"]["status"], "manual_review_required")

    def test_confirmed_no_bet_same_selection_mutual_exclusion(self):
        response = self._sport(market="top_10", odds_american=100, input_stats=golf_full_inputs(market="top_10"))
        confirmed_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["confirmed_bets"]}
        no_bet_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_logbook_rows_include_required_decision_fields(self):
        response = self._sport(market="top_10", odds_american=100, input_stats=golf_full_inputs(market="top_10"))
        row = response["logbook_ready_rows"][0]
        for field in ["confidence", "model_status", "decision", "stake", "suggested_stake"]:
            self.assertIn(field, row)


if __name__ == "__main__":
    unittest.main()
