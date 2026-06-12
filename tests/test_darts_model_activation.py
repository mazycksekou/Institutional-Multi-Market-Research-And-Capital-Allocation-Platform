import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "darts_checkout_scoring_pressure_leg_set_monte_carlo_model"
ALIASES = ("darts", "pdc", "wdf", "professional_darts", "premier_league_darts", "world_darts_championship", "darts_match")


def darts_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("darts")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def darts_inputs(**extra):
    ticket = registry.get_sport_model_config("darts")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "darts",
        "league": "PDC",
        "event_id": "Luke Littler vs Luke Humphries",
        "event": "Luke Littler vs Luke Humphries",
        "market": "match_winner",
        "selection": "Luke Littler",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Luke Littler match winner +100 vs Luke Humphries",
        "visible_markets": ["match_winner", "leg_handicap", "player_total_180s"],
        "input_stats": darts_inputs(),
    }
    data.update(extra)
    return data


class TestDartsModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "premier_league_darts",
            "league": "PDC",
            "event": "Luke Littler vs Luke Humphries",
            "market": "match_winner",
            "selection": "Luke Littler",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Luke Littler match winner +100 vs Luke Humphries",
            "visible_markets": ["match_winner", "leg_handicap", "player_total_180s"],
            "input_stats": darts_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "darts")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("darts")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "darts_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_darts_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "darts")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self):
        self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = darts_inputs()
        stats.pop("player_three_dart_average")
        stats.pop("three_dart_average", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = darts_alias_inputs(three_dart_average="bad", opp_three_dart_average="bad", checkout_pct="text", player_180s_proj="oops")
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_bad_odds_do_not_activate_from_default(self):
        self.assertEqual(self._sport(odds_american="not odds")["model_status"], "inactive_missing_data")

    def test_odds_do_not_drive_final_probability(self):
        probs = [self._sport(odds_american=odds)["final_probability"] for odds in (-140, 100, 135)]
        self.assertLess(max(probs) - min(probs), 0.000001)

    def test_odds_change_only_market_outputs(self):
        low = self._sport(odds_american=-140)
        high = self._sport(odds_american=135)
        self.assertEqual(low["final_probability"], high["final_probability"])
        self.assertNotEqual(low["implied_probability"], high["implied_probability"])
        self.assertLess(low["edge_percent"], high["edge_percent"])

    def test_negative_edge_creates_no_bet(self):
        self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(input_stats=darts_inputs(book_count=1, fatigue_rating=0.85, injury_risk=0.42))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_public_sharp_market_movement_are_enrichment_only(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=darts_inputs(public_betting_percent=99, sharp_money_percent=1, market_movement=9))["final_probability"]
        self.assertEqual(base, enriched)

    def test_enrichment_alone_cannot_confirm(self):
        response = self._sport(input_stats={"public_betting_percent": 95, "sharp_money_percent": 90, "market_movement": 7})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self):
        self.assert_active(self._sport(market="match_winner"))

    def test_moneyline_market_works(self):
        self.assert_active(self._sport(market="moneyline"))

    def test_leg_winner_market_works(self):
        self.assert_active(self._sport(market="leg_winner"))

    def test_set_winner_market_works(self):
        self.assert_active(self._sport(market="set_winner", input_stats=darts_inputs(best_of_sets=5, first_to_sets=3, match_format="best_of_5_sets")))

    def test_correct_score_market_works(self):
        self.assert_active(self._sport(market="correct_score", selection="6-4"))

    def test_set_handicap_market_works(self):
        self.assert_active(self._sport(market="set_handicap", input_stats=darts_inputs(line=-1.5, best_of_sets=5, first_to_sets=3, match_format="best_of_5_sets")))

    def test_leg_handicap_market_works(self):
        self.assert_active(self._sport(market="leg_handicap", input_stats=darts_inputs(line=-1.5)))

    def test_total_legs_market_works(self):
        self.assert_active(self._sport(market="total_legs", selection="over", input_stats=darts_inputs(line=9.5)))

    def test_total_sets_market_works(self):
        self.assert_active(self._sport(market="total_sets", selection="over", input_stats=darts_inputs(line=4.5, best_of_sets=7, first_to_sets=4, match_format="best_of_7_sets")))

    def test_player_total_180s_prop_works(self):
        self.assert_active(self._sport(market="player_total_180s", selection="Luke Littler over", input_stats=darts_inputs(line=4.5, player_prop_line=4.5)))

    def test_most_180s_prop_works(self):
        self.assert_active(self._sport(market="most_180s", selection="Luke Littler"))

    def test_highest_checkout_prop_works(self):
        self.assert_active(self._sport(market="highest_checkout", selection="Luke Littler"))

    def test_checkout_over_under_prop_works(self):
        self.assert_active(self._sport(market="checkout_over_under", selection="over", input_stats=darts_inputs(line=99.5, player_prop_line=99.5)))

    def test_player_checkout_percentage_prop_works(self):
        self.assert_active(self._sport(market="player_checkout_percentage", selection="Luke Littler over", input_stats=darts_inputs(line=0.40, player_prop_line=0.40)))

    def test_first_leg_winner_market_works(self):
        self.assert_active(self._sport(market="first_leg_winner"))

    def test_final_set_winner_market_works(self):
        self.assert_active(self._sport(market="final_set_winner", input_stats=darts_inputs(best_of_sets=7, first_to_sets=4, match_format="best_of_7_sets")))

    def test_nine_dart_finish_market_works(self):
        self.assert_active(self._sport(market="nine_dart_finish", selection="yes"))

    def test_alt_leg_handicap_market_works(self):
        self.assert_active(self._sport(market="alt_leg_handicap", input_stats=darts_inputs(line=-2.5)))

    def test_alt_total_legs_market_works(self):
        self.assert_active(self._sport(market="alt_total_legs", selection="over", input_stats=darts_inputs(line=10.5)))

    def test_alt_total_sets_market_works(self):
        self.assert_active(self._sport(market="alt_total_sets", selection="over", input_stats=darts_inputs(line=5.5, best_of_sets=9, first_to_sets=5, match_format="best_of_9_sets")))

    def test_calibration_outputs_exist(self):
        response = self._sport()
        self.assertEqual(response["format_calibration_applied"], "legs")
        self.assertEqual(response["competition_calibration_applied"], "premier_league")
        self.assertTrue(response["checkout_calibration_applied"])
        self.assertTrue(response["scoring_power_calibration_applied"])
        self.assertTrue(response["pressure_calibration_applied"])
        self.assertTrue(response["throw_advantage_calibration_applied"])

    def test_set_and_unknown_format_calibrations(self):
        self.assertEqual(registry._darts_format_calibration(darts_inputs(best_of_sets=7, best_of_legs=None, best_of_legs_value=None, legs=None, race_to_legs=None, first_to_legs=None, first_to_sets=4, format="sets", sets_format="best_of_7_sets", legs_format=None, match_format="best_of_7_sets")), "sets")
        self.assertEqual(registry._darts_format_calibration(darts_inputs(best_of_sets=5, best_of_legs=11, best_of_legs_value=11, legs=11, first_to_sets=3, first_to_legs=6, race_to_legs=6, format="hybrid", match_format="hybrid")), "mixed")
        self.assertEqual(registry._darts_format_calibration(darts_inputs(match_format="custom_exhibition", format="custom", best_of_sets=None, best_of_legs=None, best_of_legs_value=None, legs=None, race_to_legs=None, first_to_legs=None, first_to_sets=None, sets_format=None, legs_format=None)), "unknown")
        self.assertEqual(registry._darts_competition_calibration(darts_inputs(competition="Legends Exhibition", tournament="Legends Exhibition", league=None, stage=None)), "unknown")

    def test_checkout_scoring_and_pressure_edges_affect_probability(self):
        base = self._sport()["final_probability"]
        weaker = self._sport(input_stats=darts_inputs(player_three_dart_average=95.0, player_checkout_percentage=0.34, player_pressure_rating=78, player_clutch_rating=79))["final_probability"]
        self.assertLess(weaker, base)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_darts_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("darts_input_contract", response)
        self.assertIsNotNone(response["darts_projected_legs"])
        self.assertIsNotNone(response["darts_projected_total_180s"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "format_calibration_applied", "competition_calibration_applied", "checkout_calibration_applied", "scoring_power_calibration_applied", "pressure_calibration_applied", "throw_advantage_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["darts_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("darts")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
