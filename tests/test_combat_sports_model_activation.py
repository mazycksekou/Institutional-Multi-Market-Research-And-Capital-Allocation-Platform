import asyncio
import unittest
from unittest.mock import patch

from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
)


COMBAT_MISSING_INPUTS = [
    "fighter", "opponent", "fight_date", "promotion", "weight_class", "scheduled_rounds",
    "fighter_moneyline", "fighter_elo", "opponent_elo", "fighter_recent_win_percent", "opponent_recent_win_percent",
    "fighter_finish_rate", "opponent_finish_rate", "fighter_ko_tko_rate", "opponent_ko_tko_rate",
    "fighter_submission_rate", "opponent_submission_rate", "fighter_decision_rate", "opponent_decision_rate",
    "fighter_strikes_landed_per_min", "opponent_strikes_landed_per_min",
    "fighter_strikes_absorbed_per_min", "opponent_strikes_absorbed_per_min",
    "fighter_striking_accuracy", "opponent_striking_accuracy", "fighter_striking_defense", "opponent_striking_defense",
    "fighter_takedown_average", "opponent_takedown_average", "fighter_takedown_accuracy", "opponent_takedown_accuracy",
    "fighter_takedown_defense", "opponent_takedown_defense", "fighter_submission_average", "opponent_submission_average",
    "fighter_age", "opponent_age", "fighter_reach", "opponent_reach", "fighter_height", "opponent_height",
    "fighter_stance", "opponent_stance", "fighter_days_rest", "opponent_days_rest",
    "fighter_injury_status", "opponent_injury_status",
]


def combat_full_inputs(**extra):
    data = {
        "fighter": "Islam Makhachev",
        "opponent": "Charles Oliveira",
        "selection": "Islam Makhachev",
        "fight_date": "2026-07-10",
        "promotion": "UFC",
        "weight_class": "Lightweight",
        "scheduled_rounds": 5,
        "fighter_moneyline": 100,
        "fighter_elo": 1860,
        "opponent_elo": 1775,
        "fighter_recent_win_percent": 85,
        "opponent_recent_win_percent": 70,
        "fighter_finish_rate": 62,
        "opponent_finish_rate": 70,
        "fighter_ko_tko_rate": 18,
        "opponent_ko_tko_rate": 35,
        "fighter_submission_rate": 42,
        "opponent_submission_rate": 30,
        "fighter_decision_rate": 40,
        "opponent_decision_rate": 35,
        "fighter_strikes_landed_per_min": 3.2,
        "opponent_strikes_landed_per_min": 3.5,
        "fighter_strikes_absorbed_per_min": 1.8,
        "opponent_strikes_absorbed_per_min": 3.1,
        "fighter_striking_accuracy": 58,
        "opponent_striking_accuracy": 52,
        "fighter_striking_defense": 64,
        "opponent_striking_defense": 53,
        "fighter_takedown_average": 3.4,
        "opponent_takedown_average": 2.2,
        "fighter_takedown_accuracy": 61,
        "opponent_takedown_accuracy": 44,
        "fighter_takedown_defense": 88,
        "opponent_takedown_defense": 57,
        "fighter_submission_average": 1.1,
        "opponent_submission_average": 0.8,
        "fighter_age": 34,
        "opponent_age": 36,
        "fighter_reach": 70,
        "opponent_reach": 74,
        "fighter_height": 70,
        "opponent_height": 70,
        "fighter_stance": "southpaw",
        "opponent_stance": "orthodox",
        "fighter_days_rest": 180,
        "opponent_days_rest": 160,
        "fighter_injury_status": "healthy",
        "opponent_injury_status": "healthy",
        "best_available_odds": 100,
        "book_count": 8,
        "cardio_rating": 78,
        "pace_rating": 72,
        "chin_durability": 76,
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "ufc",
        "league": "UFC",
        "market": "moneyline",
        "event_id": "Islam Makhachev vs Charles Oliveira",
        "selection": "Islam Makhachev",
        "odds_american": -130,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "input_stats": combat_full_inputs(),
    }
    payload.update(extra)
    return payload


class TestCombatSportsModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "ufc",
            "league": "UFC",
            "event": "Islam Makhachev vs Charles Oliveira",
            "teams": ["Islam Makhachev", "Charles Oliveira"],
            "market": "moneyline",
            "selection": "Islam Makhachev",
            "odds_american": -130,
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "input_stats": combat_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_missing_input_safety_returns_no_500_no_confirmed_bets_and_zero_stake(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["ok"])
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["missing_inputs"], COMBAT_MISSING_INPUTS)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["logbook_ready_rows"][0]["stake"], 0)
        self.assertEqual(response["logbook_ready_rows"][0]["decision"], "NO_BET")

    def test_bad_or_text_inputs_return_safe_no_bet_rows(self):
        bad_payloads = [
            {"input_stats": None},
            {"input_stats": "text betting slip"},
            {"input_stats": {"fighter_elo": "bad", "referee_profile": "early stoppages"}},
            {"odds_american": "not odds"},
        ]
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                response = self._sport(**payload)
                self.assertTrue(response["ok"])
                self.assertEqual(response["confirmed_bets"], [])
                self.assertEqual(response["suggested_stake"], 0)
                self.assertEqual(response["logbook_ready_rows"][0]["stake"], 0)
                self.assertEqual(response["logbook_ready_rows"][0]["decision"], "NO_BET")

    def test_negative_edge_returns_evaluated_no_bet(self):
        response = self._sport(odds_american=-300)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["status"], "evaluated_no_bet")
        self.assertEqual(response["confirmed_bets"], [])

    def test_edge_too_small_returns_evaluated_no_bet_edge_too_small(self):
        response = self._sport(odds_american=-160)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.0)
        self.assertEqual(response["status"], "evaluated_no_bet_edge_too_small")
        self.assertEqual(response["suggested_stake"], 0)

    def test_low_confidence_returns_evaluated_no_bet_low_confidence(self):
        response = self._sport(input_stats=combat_full_inputs(short_notice=True, weight_cut_risk=True, fighter_injury_status="questionable", fighter_days_rest=410))
        self.assertLess(response["confidence"], 65)
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")
        self.assertEqual(response["confirmed_bets"], [])

    def test_positive_edge_with_confidence_passing_returns_confirmed_bet(self):
        response = self._sport(odds_american=100)
        self.assertGreaterEqual(response["edge"], 2.0)
        self.assertGreaterEqual(response["confidence"], 65)
        self.assertEqual(response["decision"], "CONFIRMED_BET")
        self.assertEqual(response["status"], "confirmed_bet")
        self.assertGreater(response["suggested_stake"], 0)

    def test_moneyline_market_active(self):
        response = self._sport()
        self.assertEqual(response["model_name"], "fighter_striking_grappling_finish_model")
        self.assertEqual(response["model_status"], "active")
        self.assertIn("fighter_win_probability", response)

    def test_method_and_finish_markets_are_active(self):
        for market in ["method_of_victory", "fighter_by_ko_tko", "fighter_by_submission", "fighter_by_decision"]:
            response = self._sport(market=market, odds_american=1000, input_stats=combat_full_inputs(market=market))
            self.assertEqual(response["model_status"], "active")
            self.assertIsNotNone(response["estimated_true_probability"])

    def test_distance_markets_are_active(self):
        for market in ["fight_goes_distance", "fight_does_not_go_distance"]:
            response = self._sport(market=market, odds_american=100, input_stats=combat_full_inputs(market=market))
            self.assertEqual(response["model_status"], "active")
            self.assertIsNotNone(response["goes_distance_probability"])

    def test_over_under_rounds_and_round_markets_are_active(self):
        for market in ["over_rounds", "under_rounds", "round_group", "exact_round"]:
            response = self._sport(market=market, line=2.5, odds_american=120, input_stats=combat_full_inputs(market=market, line=2.5))
            self.assertEqual(response["model_status"], "active")
            self.assertIsNotNone(response["estimated_true_probability"])

    def test_prop_markets_are_active(self):
        for market in ["knockdown_prop", "takedown_prop", "significant_strikes_prop", "submission_attempt_prop"]:
            response = self._sport(market=market, line=1.5, odds_american=100, input_stats=combat_full_inputs(market=market, line=1.5))
            self.assertEqual(response["model_status"], "active")
            self.assertIn("target_props", response["full_board_preview"])
            self.assertTrue(response["full_board_preview"]["target_props"])

    def test_provider_failure_does_not_break_route(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("provider down")):
            response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertEqual(response["provider_enrichment"]["provider_status"], "error")
        self.assertEqual(response["model_analysis"]["model_status"], "active")

    def test_referee_judge_data_cannot_create_confirmed_bet_without_base_inputs(self):
        response = self._sport(input_stats={"referee_profile": "early stoppages", "judge_profile": "favorite friendly"})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["officiating_module_status"], "inactive_base_model")

    def test_social_crowd_data_cannot_create_confirmed_bet_without_base_inputs(self):
        response = self._sport(input_stats={"social_sentiment": "strong", "crowd_consensus": 90})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["model_status"], "inactive_missing_data")

    def test_screenshot_flow_works(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertEqual(response["model_analysis"]["model_name"], "fighter_striking_grappling_finish_model")
        self.assertEqual(response["model_analysis"]["model_status"], "active")

    def test_live_smoke_screenshot_alias_inputs_activate_combat_model(self):
        response = self._screenshot(
            sport="ufc",
            market="moneyline",
            selection="Jon Jones",
            odds_american=100,
            event="Jon Jones vs Stipe Miocic",
            teams=["Jon Jones", "Stipe Miocic"],
            input_stats={
                "fighter_name": "Jon Jones",
                "opponent_name": "Stipe Miocic",
                "fighter_strikes_landed_per_min": 4.3,
                "opponent_strikes_landed_per_min": 3.8,
                "fighter_takedown_average": 1.9,
                "fighter_submission_average": 0.5,
                "fighter_reach": 84.5,
                "fighter_height": 76,
                "fighter_recent_win_percent": 80,
                "opponent_recent_win_percent": 60,
            },
        )
        model = response["model_analysis"]
        self.assertTrue(response["ok"])
        self.assertEqual(model["sport"], "mma_mixed_martial_arts")
        self.assertEqual(model["model_name"], "fighter_striking_grappling_finish_model")
        self.assertEqual(model["model_status"], "active")
        self.assertEqual(model["missing_inputs"], [])
        self.assertFalse(response["partial_model_mode"])
        self.assertIsNotNone(model["final_probability"])
        self.assertEqual(model["implied_probability"], 0.5)
        self.assertNotEqual(model["status"], "manual_review_required")
        if model["decision"] == "NO_BET":
            self.assertEqual(response["stake"], 0)
        else:
            self.assertGreater(response["stake"], 0)
        confirmed_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bet_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["no_bets"]}
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_odds_stability_across_prices(self):
        minus_130 = self._sport(odds_american=-130)
        plus_100 = self._sport(odds_american=100)
        plus_120 = self._sport(odds_american=120)
        probabilities = [result["final_probability"] for result in [minus_130, plus_100, plus_120]]
        self.assertLess(max(probabilities) - min(probabilities), 0.03)
        self.assertGreater(minus_130["implied_probability"], plus_100["implied_probability"])
        self.assertGreater(plus_100["implied_probability"], plus_120["implied_probability"])
        self.assertLess(minus_130["edge"], plus_100["edge"])
        self.assertLess(plus_100["edge"], plus_120["edge"])

    def test_offered_odds_do_not_drive_combat_final_probability(self):
        results = {
            -130: self._sport(odds_american=-130),
            100: self._sport(odds_american=100),
            120: self._sport(odds_american=120),
        }
        final_probabilities = [result["final_probability"] for result in results.values()]
        raw_probabilities = [result["raw_model_probability"] for result in results.values()]
        calibrated_probabilities = [result["calibrated_model_probability"] for result in results.values()]
        self.assertLess(max(final_probabilities) - min(final_probabilities), 0.03)
        self.assertLess(max(raw_probabilities) - min(raw_probabilities), 0.000001)
        self.assertLess(max(calibrated_probabilities) - min(calibrated_probabilities), 0.000001)
        self.assertIsNone(results[-130]["market_anchor_probability"])
        self.assertLess(results[-130]["edge"], results[100]["edge"])
        self.assertLess(results[100]["edge"], results[120]["edge"])

        for response in results.values():
            confirmed_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["confirmed_bets"]}
            no_bet_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
            self.assertFalse(confirmed_keys & no_bet_keys)

    def test_input_stats_market_odds_fields_do_not_drive_final_probability(self):
        short_price_inputs = combat_full_inputs(
            fighter_moneyline=-180,
            opponent_moneyline=150,
            current_odds=-180,
            best_available_odds=-170,
            opening_odds=-160,
        )
        plus_price_inputs = combat_full_inputs(
            fighter_moneyline=140,
            opponent_moneyline=-165,
            current_odds=120,
            best_available_odds=130,
            opening_odds=100,
        )
        short_price = self._sport(odds_american=-130, input_stats=short_price_inputs)
        plus_price = self._sport(odds_american=-130, input_stats=plus_price_inputs)

        stable_probability_fields = [
            "raw_model_probability",
            "calibrated_model_probability",
            "final_probability",
            "fighter_win_probability",
            "opponent_win_probability",
            "ko_tko_probability",
            "submission_probability",
            "decision_probability",
            "goes_distance_probability",
            "does_not_go_distance_probability",
            "over_rounds_probability",
            "under_rounds_probability",
        ]
        for field in stable_probability_fields:
            self.assertAlmostEqual(short_price[field], plus_price[field], places=8, msg=field)
        self.assertEqual(short_price["implied_probability"], plus_price["implied_probability"])
        self.assertEqual(short_price["edge_percent"], plus_price["edge_percent"])
        self.assertEqual(short_price["decision"], plus_price["decision"])

    def test_confirmed_bets_and_no_bets_are_mutually_exclusive_for_same_selection(self):
        response = self._sport(odds_american=100)
        confirmed_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["confirmed_bets"]}
        no_bet_keys = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_full_board_response_contains_required_sections(self):
        response = self._sport()
        for field in [
            "confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets",
            "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs",
            "manual_review_required", "logbook_ready_rows",
        ]:
            self.assertIn(field, response)


if __name__ == "__main__":
    unittest.main()
