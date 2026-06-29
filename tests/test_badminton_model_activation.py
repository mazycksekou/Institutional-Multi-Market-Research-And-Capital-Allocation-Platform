import asyncio
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "badminton_serve_return_rally_momentum_shuttle_monte_carlo_model"
ALIASES = ("badminton", "bwf", "world_badminton", "olympic_badminton", "badminton_singles", "badminton_doubles", "bwf_world_tour")


def badminton_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("badminton")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def badminton_inputs(**extra):
    ticket = registry.get_sport_model_config("badminton")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "badminton", "league": "BWF World Tour", "event_id": "Viktor Axelsen vs Lee Zii Jia",
        "event": "Viktor Axelsen vs Lee Zii Jia", "market": "match_winner", "selection": "Viktor Axelsen",
        "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "source_type": "unit_test",
        "screenshot_text": "Viktor Axelsen match winner +100 vs Lee Zii Jia", "visible_markets": ["match_winner"],
        "input_stats": badminton_inputs(),
    }
    data.update(extra)
    return data


class TestBadmintonModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "bwf", "league": "BWF World Tour",
            "event": "Viktor Axelsen vs Lee Zii Jia", "market": "match_winner",
            "selection": "Viktor Axelsen", "odds_american": 100, "book": "Manual",
            "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
            "screenshot_text": "Viktor Axelsen match winner +100 vs Lee Zii Jia",
            "visible_markets": ["match_winner"], "input_stats": badminton_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "badminton")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("badminton")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "badminton_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_badminton_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "badminton")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = badminton_inputs()
        stats.pop("player_serve_rating")
        stats.pop("serve_rating", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = badminton_alias_inputs(serve_rating="bad", return_rating="bad", rally_rating="text", shuttle_speed="bad")
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

    def test_negative_edge_creates_no_bet(self): self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(input_stats=badminton_inputs(book_count=1, fatigue_rating=0.80, injury_risk=0.38))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_public_sharp_market_movement_are_enrichment_only(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=badminton_inputs(public_betting_percent=99, sharp_money_percent=1, market_movement=9))["final_probability"]
        self.assertEqual(base, enriched)

    def test_enrichment_alone_cannot_confirm(self):
        response = self._sport(input_stats={"public_betting_percent": 95, "sharp_money_percent": 90, "market_movement": 7})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_moneyline_market_works(self): self.assert_active(self._sport(market="moneyline"))
    def test_game_winner_market_works(self): self.assert_active(self._sport(market="game_winner"))
    def test_set_winner_market_works(self): self.assert_active(self._sport(market="set_winner"))
    def test_correct_score_market_works(self): self.assert_active(self._sport(market="correct_score"))
    def test_game_handicap_market_works(self): self.assert_active(self._sport(market="game_handicap", input_stats=badminton_inputs(line=-1.5)))
    def test_point_handicap_market_works(self): self.assert_active(self._sport(market="point_handicap", input_stats=badminton_inputs(line=-4.5)))
    def test_total_games_market_works(self): self.assert_active(self._sport(market="total_games", selection="over", input_stats=badminton_inputs(line=2.5)))
    def test_total_points_market_works(self): self.assert_active(self._sport(market="total_points", selection="over", input_stats=badminton_inputs(line=78.5)))
    def test_first_game_winner_market_works(self): self.assert_active(self._sport(market="first_game_winner"))
    def test_second_game_winner_market_works(self): self.assert_active(self._sport(market="second_game_winner"))
    def test_third_game_winner_market_works(self): self.assert_active(self._sport(market="third_game_winner"))
    def test_alt_game_handicap_market_works(self): self.assert_active(self._sport(market="alt_game_handicap", input_stats=badminton_inputs(line=-2.5)))
    def test_alt_total_games_market_works(self): self.assert_active(self._sport(market="alt_total_games", selection="over", input_stats=badminton_inputs(line=2.5)))
    def test_alt_total_points_market_works(self): self.assert_active(self._sport(market="alt_total_points", selection="over", input_stats=badminton_inputs(line=82.5)))

    def test_player_total_points_prop_works(self): self.assert_active(self._sport(market="player_total_points", selection="Viktor Axelsen over", input_stats=badminton_inputs(line=42.5)))
    def test_player_aces_prop_works(self): self.assert_active(self._sport(market="player_aces", selection="Viktor Axelsen over", input_stats=badminton_inputs(line=0.5)))
    def test_player_service_points_won_prop_works(self): self.assert_active(self._sport(market="player_service_points_won", selection="Viktor Axelsen over", input_stats=badminton_inputs(line=25.5)))
    def test_player_return_points_won_prop_works(self): self.assert_active(self._sport(market="player_return_points_won", selection="Viktor Axelsen over", input_stats=badminton_inputs(line=17.5)))

    def test_calibration_outputs_exist(self):
        response = self._sport()
        self.assertEqual(response["format_calibration_applied"], "best_of_3")
        self.assertEqual(response["discipline_calibration_applied"], "singles")
        self.assertEqual(response["tournament_calibration_applied"], "tournament")
        self.assertTrue(response["serve_return_calibration_applied"])
        self.assertTrue(response["rally_style_calibration_applied"])
        self.assertTrue(response["deciding_game_calibration_applied"])

    def test_doubles_and_unknown_calibrations(self):
        self.assertEqual(self._sport(input_stats=badminton_inputs(singles_doubles="doubles"))["discipline_calibration_applied"], "doubles")
        self.assertEqual(self._sport(input_stats=badminton_inputs(best_of_games=5, match_format="custom"))["format_calibration_applied"], "unknown")
        self.assertEqual(self._sport(input_stats=badminton_inputs(tournament="Friendly Series", competition="Friendly"))["tournament_calibration_applied"], "unknown")

    def test_serve_return_and_rally_edges_affect_probability(self):
        base = self._sport()["final_probability"]
        weaker = self._sport(input_stats=badminton_inputs(player_serve_rating=78, player_return_rating=76, player_rally_rating=77, player_smash_rating=76))["final_probability"]
        self.assertLess(weaker, base)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_badminton_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("badminton_input_contract", response)
        self.assertIsNotNone(response["badminton_projected_total_points"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "format_calibration_applied", "discipline_calibration_applied", "tournament_calibration_applied", "serve_return_calibration_applied", "rally_style_calibration_applied", "deciding_game_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["badminton_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("badminton")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
