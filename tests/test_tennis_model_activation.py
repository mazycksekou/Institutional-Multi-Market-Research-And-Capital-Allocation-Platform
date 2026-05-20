import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


TENNIS_MISSING_INPUTS = [
    "player", "opponent", "selection", "tournament", "match_date", "surface", "best_of_sets",
    "player_ranking", "opponent_ranking", "player_elo", "opponent_elo", "player_surface_elo", "opponent_surface_elo",
    "player_hold_percent", "opponent_hold_percent", "player_break_percent", "opponent_break_percent",
    "player_first_serve_in_percent", "opponent_first_serve_in_percent",
    "player_first_serve_points_won_percent", "opponent_first_serve_points_won_percent",
    "player_second_serve_points_won_percent", "opponent_second_serve_points_won_percent",
    "player_return_points_won_percent", "opponent_return_points_won_percent",
    "player_ace_rate", "opponent_ace_rate", "player_double_fault_rate", "opponent_double_fault_rate",
    "player_recent_form_wins", "opponent_recent_form_wins", "player_recent_form_losses", "opponent_recent_form_losses",
    "player_fatigue_index", "opponent_fatigue_index", "player_injury_status", "opponent_injury_status",
]


def tennis_full_inputs(**extra):
    data = {
        "player": "Iga Swiatek",
        "opponent": "Aryna Sabalenka",
        "selection": "Iga Swiatek",
        "market": "moneyline",
        "league": "tennis_wta",
        "tournament": "French Open",
        "match_date": "2026-06-04",
        "surface": "clay",
        "best_of_sets": 3,
        "player_ranking": 1,
        "opponent_ranking": 2,
        "player_elo": 2190,
        "opponent_elo": 2100,
        "player_surface_elo": 2240,
        "opponent_surface_elo": 2075,
        "player_hold_percent": 78,
        "opponent_hold_percent": 74,
        "player_break_percent": 43,
        "opponent_break_percent": 36,
        "player_first_serve_in_percent": 66,
        "opponent_first_serve_in_percent": 61,
        "player_first_serve_points_won_percent": 71,
        "opponent_first_serve_points_won_percent": 69,
        "player_second_serve_points_won_percent": 55,
        "opponent_second_serve_points_won_percent": 51,
        "player_return_points_won_percent": 45,
        "opponent_return_points_won_percent": 40,
        "player_ace_rate": 5.0,
        "opponent_ace_rate": 7.5,
        "player_double_fault_rate": 2.5,
        "opponent_double_fault_rate": 4.0,
        "player_recent_form_wins": 8,
        "opponent_recent_form_wins": 6,
        "player_recent_form_losses": 1,
        "opponent_recent_form_losses": 3,
        "player_fatigue_index": 0.22,
        "opponent_fatigue_index": 0.34,
        "player_injury_status": "healthy",
        "opponent_injury_status": "healthy",
        "best_available_odds": 100,
        "book_count": 8,
        "current_odds": 100,
        "consensus_odds": 100,
        "player_surface_win_percent": 86,
        "opponent_surface_win_percent": 73,
        "player_tiebreak_win_percent": 58,
        "opponent_tiebreak_win_percent": 52,
        "player_rest_days": 2,
        "opponent_rest_days": 1,
    }
    data.update(extra)
    return data


def tennis_live_alias_inputs(**extra):
    data = tennis_full_inputs(
        player="Novak Djokovic",
        opponent="Carlos Alcaraz",
        selection="Novak Djokovic",
        league="ATP",
        tournament="ATP Finals",
        player_recent_win_percent=80,
        opponent_recent_win_percent=60,
        player_fatigue_rating=2.2,
        opponent_fatigue_rating=3.4,
        player_days_rest=2,
        opponent_days_rest=1,
    )
    for field in [
        "player_recent_form_wins",
        "opponent_recent_form_wins",
        "player_recent_form_losses",
        "opponent_recent_form_losses",
        "player_fatigue_index",
        "opponent_fatigue_index",
        "player_rest_days",
        "opponent_rest_days",
    ]:
        data.pop(field, None)
    data.update(extra)
    return data


def tennis_exact_live_alias_only_inputs(**extra):
    data = {
        "player": "Novak Djokovic",
        "opponent": "Carlos Alcaraz",
        "selection": "Novak Djokovic",
        "market": "moneyline",
        "league": "ATP",
        "tournament": "Wimbledon",
        "match_date": "2026-05-20",
        "surface": "grass",
        "best_of_sets": 3,
        "player_ranking": 2,
        "opponent_ranking": 3,
        "player_elo": 2200,
        "opponent_elo": 2075,
        "player_surface_elo": 2200,
        "opponent_surface_elo": 2075,
        "player_recent_win_percent": 70,
        "opponent_recent_win_percent": 60,
        "player_fatigue_rating": 15,
        "opponent_fatigue_rating": 22,
        "player_days_rest": 3,
        "opponent_days_rest": 2,
        "player_serve_hold_percent": 86,
        "opponent_serve_hold_percent": 82,
        "player_break_percent": 28,
        "opponent_break_percent": 24,
        "player_first_serve_percent": 65,
        "opponent_first_serve_percent": 63,
        "player_surface_win_percent": 78,
        "opponent_surface_win_percent": 70,
        "player_injury_status": "healthy",
        "opponent_injury_status": "healthy",
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "wta",
        "league": "tennis_wta",
        "market": "moneyline",
        "event_id": "Swiatek vs Sabalenka",
        "selection": "Iga Swiatek",
        "odds_american": -130,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": tennis_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestTennisModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "tennis_wta",
            "league": "tennis_wta",
            "event": "Swiatek vs Sabalenka",
            "teams": ["Iga Swiatek", "Aryna Sabalenka"],
            "market": "moneyline",
            "selection": "Iga Swiatek",
            "odds_american": -130,
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": tennis_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_tennis_missing_inputs_returns_partial_mode_and_exact_missing_inputs(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], TENNIS_MISSING_INPUTS)

    def test_tennis_missing_inputs_returns_no_confirmed_bets_and_zero_stake(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertIn("confidence", response["logbook_ready_rows"][0])

    def test_tennis_full_moneyline_inputs_activate_model(self):
        response = self._sport()
        self.assertEqual(response["model_name"], "elo_serve_return_markov_tennis_model")
        self.assertEqual(response["model_status"], "active")
        self.assertFalse(response["partial_model_mode"])

    def test_tennis_full_moneyline_inputs_return_probability_and_edge(self):
        response = self._sport()
        self.assertIsNotNone(response["estimated_true_probability"])
        self.assertIsNotNone(response["edge"])
        self.assertTrue(response["markov_model_applied"])

    def test_tennis_negative_edge_returns_evaluated_no_bet(self):
        response = self._sport(odds_american=-400)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet")

    def test_tennis_positive_edge_below_threshold_returns_edge_too_small(self):
        response = self._sport(odds_american=-230)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["status"], "evaluated_no_bet_edge_too_small")

    def test_tennis_positive_edge_with_confidence_passing_returns_confirmed_bet(self):
        response = self._sport(odds_american=100)
        self.assertGreaterEqual(response["edge"], 2.0)
        self.assertGreaterEqual(response["confidence"], 65)
        self.assertIsInstance(response["confidence"], (int, float))
        self.assertTrue(response["confirmed_bets"])
        self.assertEqual(response["decision"], "CONFIRMED_BET")
        self.assertEqual(response["status"], "confirmed_bet")
        self.assertGreater(response["suggested_stake"], 0)
        self.assertEqual(response["logbook_ready_rows"][0]["confidence"], response["confidence"])
        self.assertGreaterEqual(response["logbook_ready_rows"][0]["confidence"], 65)
        self.assertEqual(response["full_board_preview"]["confirmed_bets"][0]["confidence"], response["confidence"])
        confirmed_key = (
            response["sport"],
            response["event_id"] if "event_id" in response else "Swiatek vs Sabalenka",
            response["market"],
            response["confirmed_bets"][0]["selection"],
        )
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        self.assertNotIn(confirmed_key, no_bet_keys)

    def test_tennis_intentional_low_confidence_returns_numeric_low_confidence(self):
        response = self._sport(
            odds_american=100,
            input_stats=tennis_full_inputs(
                player_injury_status="questionable",
                player_retirement_risk=0.35,
                player_fatigue_index=0.91,
                book_count=3,
            ),
        )
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertIsInstance(response["confidence"], (int, float))
        self.assertLess(response["confidence"], 65)
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")
        self.assertIn("low confidence", [bet["reason"] for bet in response["no_bets"]])
        self.assertEqual(response["logbook_ready_rows"][0]["confidence"], response["confidence"])

    def test_tennis_best_of_3_and_best_of_5_are_handled_separately(self):
        best3 = self._sport(input_stats=tennis_full_inputs(best_of_sets=3))
        best5 = self._sport(input_stats=tennis_full_inputs(best_of_sets=5))
        self.assertNotEqual(best3["estimated_true_probability"], best5["estimated_true_probability"])

    def test_tennis_first_set_moneyline_does_not_reuse_full_match_probability(self):
        full = self._sport()
        first_set = self._sport(market="first_set_moneyline", input_stats=tennis_full_inputs(market="first_set_moneyline"))
        self.assertEqual(first_set["model_status"], "active")
        self.assertNotEqual(first_set["estimated_true_probability"], full["estimated_true_probability"])

    def test_tennis_market_specific_required_inputs(self):
        self.assertIn("line", self._sport(market="set_handicap", input_stats=tennis_full_inputs(market="set_handicap"))["missing_inputs"])
        self.assertIn("line", self._sport(market="game_handicap", input_stats=tennis_full_inputs(market="game_handicap"))["missing_inputs"])
        self.assertIn("total_line", self._sport(market="total_games", selection="Over", input_stats=tennis_full_inputs(market="total_games"))["missing_inputs"])
        self.assertIn("total_line", self._sport(market="first_set_total_games", selection="Over", input_stats=tennis_full_inputs(market="first_set_total_games"))["missing_inputs"])
        self.assertIn("correct_score_selection", self._sport(market="correct_score", input_stats=tennis_full_inputs(market="correct_score"))["missing_inputs"])

    def test_tennis_market_outputs_work(self):
        set_handicap = self._sport(market="set_handicap", line=-1.5, input_stats=tennis_full_inputs(market="set_handicap", line=-1.5))
        game_handicap = self._sport(market="game_handicap", line=-3.5, input_stats=tennis_full_inputs(market="game_handicap", line=-3.5))
        total_games = self._sport(market="total_games", selection="Over", total_line=21.5, input_stats=tennis_full_inputs(market="total_games", total_line=21.5, selection="Over"))
        first_total = self._sport(market="first_set_total_games", selection="Over", total_line=9.5, input_stats=tennis_full_inputs(market="first_set_total_games", total_line=9.5, selection="Over"))
        for response in [set_handicap, game_handicap, total_games, first_total]:
            self.assertEqual(response["model_status"], "active")

    def test_tennis_correct_score_works_and_is_high_risk(self):
        response = self._sport(market="correct_score", correct_score_selection="2-0", odds_american=220, input_stats=tennis_full_inputs(market="correct_score", correct_score_selection="2-0"))
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["risk"], "high")

    def test_tennis_player_prop_requires_and_complete_works(self):
        missing = self._sport(market="player_prop", input_stats=tennis_full_inputs(market="player_prop"))
        for field in ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status"]:
            self.assertIn(field, missing["missing_inputs"])
        complete = self._sport(
            market="aces",
            selection="Swiatek aces over",
            odds_american=110,
            input_stats=tennis_full_inputs(market="aces", selection="Swiatek aces over", player_name="Iga Swiatek", prop_line=3.5, player_projection=4.3),
        )
        self.assertIn(complete["decision"], {"NO_BET", "CONFIRMED_BET"})
        self.assertIn("target_props", complete["full_board_preview"])

    def test_tennis_provider_failure_does_not_create_top_level_route_error(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertIsNone(response.get("error"))
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")

    def test_tennis_screenshot_analysis_passes_full_inputs_to_model(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["model_analysis"]["sport"], "tennis")
        self.assertEqual(response["model_analysis"]["model_name"], "elo_serve_return_markov_tennis_model")

    def test_tennis_live_screenshot_fixture_promotes_confidence_and_decision(self):
        response = self._screenshot(
            sport="tennis",
            league="ATP",
            event="Novak Djokovic vs Carlos Alcaraz",
            teams=["Novak Djokovic", "Carlos Alcaraz"],
            market="moneyline",
            selection="Novak Djokovic",
            odds_american=100,
            screenshot_text="Novak Djokovic vs Carlos Alcaraz moneyline Djokovic +100",
            risk_profile="moderate",
            bankroll=1000,
            unit_size=25,
            input_stats=tennis_full_inputs(
                player="Novak Djokovic",
                opponent="Carlos Alcaraz",
                selection="Novak Djokovic",
                league="ATP",
                tournament="ATP Finals",
            ),
        )
        self.assertIsNotNone(response["confidence"])
        self.assertIsInstance(response["confidence"], (int, float))
        if response["confidence"] < 65:
            self.assertEqual(response["decision"], "NO_BET")
            self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")
            self.assertEqual(response["suggested_stake"], 0)
            self.assertIn("low confidence", [bet["reason"] for bet in response["no_bets"]])
        else:
            self.assertEqual(response["decision"], "CONFIRMED_BET")
            self.assertEqual(response["status"], "confirmed_bet")
            self.assertGreater(response["suggested_stake"], 0)
        self.assertEqual(response["logbook_ready_rows"][0]["confidence"], response["confidence"])
        self.assertEqual(response["full_board_preview"]["logbook_ready_rows"][0]["confidence"], response["confidence"])
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_tennis_live_screenshot_fixture_confidence_65_6_confirms_at_moderate_gate(self):
        required = set(__import__("multi_sport_model_registry").TENNIS_INPUT_CONTRACT["required_core_inputs"])
        input_stats = {
            key: value
            for key, value in tennis_full_inputs(
                player="Novak Djokovic",
                opponent="Carlos Alcaraz",
                selection="Novak Djokovic",
                league="ATP",
                tournament="ATP Finals",
                book_count=8,
            ).items()
            if key in required or key in {"book_count", "market"}
        }
        response = self._screenshot(
            sport="tennis",
            league="ATP",
            event="Novak Djokovic vs Carlos Alcaraz",
            teams=["Novak Djokovic", "Carlos Alcaraz"],
            market="moneyline",
            selection="Novak Djokovic",
            odds_american=100,
            screenshot_text="Novak Djokovic vs Carlos Alcaraz moneyline Djokovic +100",
            risk_profile="moderate",
            bankroll=1000,
            unit_size=25,
            input_stats=input_stats,
        )
        row = response["logbook_ready_rows"][0]
        self.assertTrue(response["ok"])
        self.assertEqual(row["selection"], "Novak Djokovic")
        self.assertGreaterEqual(row["confidence"], 65)
        self.assertLess(row["confidence"], 66)
        self.assertEqual(row["decision"], "CONFIRMED_BET")
        self.assertEqual(row["status"], "confirmed_bet")
        self.assertGreater(row.get("stake") or row.get("suggested_stake"), 0)
        self.assertGreaterEqual(len(response["full_board_preview"]["confirmed_bets"]), 1)
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["confirmed_bets"]
        }
        board_no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        top_no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["no_bets"]
        }
        self.assertFalse(confirmed_keys & board_no_bet_keys)
        self.assertFalse(confirmed_keys & top_no_bet_keys)

    def test_tennis_live_screenshot_alias_payload_activates_and_confirms(self):
        response = self._screenshot(
            sport="tennis",
            league="ATP",
            event="Novak Djokovic vs Carlos Alcaraz",
            teams=["Novak Djokovic", "Carlos Alcaraz"],
            market="moneyline",
            selection="Novak Djokovic",
            odds_american=100,
            screenshot_text="Novak Djokovic vs Carlos Alcaraz moneyline Djokovic +100",
            risk_profile="moderate",
            bankroll=1000,
            unit_size=25,
            input_stats=tennis_live_alias_inputs(book_count=8),
        )
        row = response["logbook_ready_rows"][0]
        self.assertTrue(response["ok"])
        self.assertEqual(response["model_analysis"]["model_status"], "active")
        self.assertIsNotNone(response["model_analysis"]["final_probability"])
        self.assertIsInstance(row["confidence"], (int, float))
        self.assertGreaterEqual(row["confidence"], 65)
        self.assertEqual(row["decision"], "CONFIRMED_BET")
        self.assertEqual(row["status"], "confirmed_bet")
        self.assertGreater(row.get("stake") or row.get("suggested_stake"), 0)
        self.assertGreaterEqual(len(response["full_board_preview"]["confirmed_bets"]), 1)
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_tennis_exact_live_alias_only_screenshot_payload_activates_and_confirms(self):
        response = self._screenshot(
            sport="tennis",
            league="ATP",
            event="Novak Djokovic vs Carlos Alcaraz",
            teams=["Novak Djokovic", "Carlos Alcaraz"],
            market="moneyline",
            selection="Novak Djokovic",
            odds_american=100,
            screenshot_text="Novak Djokovic vs Carlos Alcaraz moneyline Djokovic +100",
            risk_profile="moderate",
            bankroll=1000,
            unit_size=25,
            input_stats=tennis_exact_live_alias_only_inputs(),
        )
        row = response["logbook_ready_rows"][0]
        self.assertTrue(response["ok"])
        self.assertEqual(response["model_analysis"]["model_status"], "active")
        self.assertIsNotNone(response["model_analysis"]["final_probability"])
        self.assertIsInstance(row["confidence"], (int, float))
        self.assertGreaterEqual(row["confidence"], 65)
        self.assertEqual(row["decision"], "CONFIRMED_BET")
        self.assertEqual(row["status"], "confirmed_bet")
        self.assertGreater(row.get("stake") or row.get("suggested_stake"), 0)
        self.assertGreater(response["suggested_stake"], 0)
        self.assertGreaterEqual(len(response["full_board_preview"]["confirmed_bets"]), 1)
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["full_board_preview"]["no_bets"]
        }
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_tennis_true_missing_core_inputs_still_inactive_with_zero_stake(self):
        response = self._screenshot(
            sport="tennis",
            league="ATP",
            event="Novak Djokovic vs Carlos Alcaraz",
            teams=["Novak Djokovic", "Carlos Alcaraz"],
            market="moneyline",
            selection="Novak Djokovic",
            odds_american=100,
            risk_profile="moderate",
            bankroll=1000,
            unit_size=25,
            input_stats={"player": "Novak Djokovic"},
        )
        self.assertEqual(response["model_analysis"]["model_status"], "inactive_missing_data")
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["confirmed_bets"], [])

    def test_tennis_confirmed_bets_and_no_bets_are_mutually_exclusive(self):
        response = self._sport(odds_american=100)
        confirmed_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["confirmed_bets"]}
        no_bet_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_tennis_same_stats_keep_probability_stable_as_odds_change(self):
        minus_130 = self._sport(odds_american=-130)
        plus_100 = self._sport(odds_american=100)
        plus_120 = self._sport(odds_american=120)
        probabilities = [r["final_probability"] for r in [minus_130, plus_100, plus_120]]
        self.assertLess(max(probabilities) - min(probabilities), 0.03)
        self.assertGreater(minus_130["implied_probability"], plus_100["implied_probability"])
        self.assertGreater(plus_100["implied_probability"], plus_120["implied_probability"])
        self.assertLess(minus_130["edge"], plus_100["edge"])
        self.assertLess(plus_100["edge"], plus_120["edge"])

    def test_tennis_adjustment_flags_are_exposed(self):
        response = self._sport()
        self.assertTrue(response["markov_model_applied"])
        self.assertTrue(response["surface_adjustment_applied"])
        self.assertTrue(response["fatigue_adjustment_applied"])
        self.assertTrue(response["injury_adjustment_applied"])

    def test_tennis_double_faults_missing_input_does_not_crash(self):
        response = self._sport(market="double_faults", input_stats=tennis_full_inputs(market="double_faults"))
        self.assertTrue(response["ok"])
        self.assertIn("player_name", response["missing_inputs"])

    def test_no_tennis_input_creates_500(self):
        bad_payloads = [
            {"input_stats": None},
            {"input_stats": "not json"},
            {"input_stats": {"player_elo": "bad", "opponent_elo": object()}},
        ]
        for payload in bad_payloads:
            response = self._sport(**payload)
            self.assertTrue(response["ok"])
            self.assertEqual(response["confirmed_bets"], [])


if __name__ == "__main__":
    unittest.main()
