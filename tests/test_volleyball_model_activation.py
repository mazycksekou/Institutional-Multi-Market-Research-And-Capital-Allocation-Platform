import asyncio
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "volleyball_sideout_attack_block_serve_monte_carlo_model"
ALIASES = ("volleyball", "indoor_volleyball", "beach_volleyball", "ncaa_volleyball", "mens_volleyball", "womens_volleyball", "fivb", "vnl", "avp", "olympic_volleyball")


def volleyball_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("volleyball")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def volleyball_inputs(**extra):
    ticket = registry.get_sport_model_config("volleyball")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(
        sport=ticket["sport"],
        market=ticket["market"],
        selection=ticket["selection"],
        input_stats=ticket["input_stats"],
        ticket=ticket,
    )["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "volleyball",
        "league": "NCAA",
        "event_id": "Nebraska vs Wisconsin",
        "event": "Nebraska vs Wisconsin",
        "market": "match_winner",
        "selection": "Nebraska",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Nebraska match winner +100 vs Wisconsin",
        "visible_markets": ["match_winner"],
        "input_stats": volleyball_inputs(),
    }
    data.update(extra)
    return data


class TestVolleyballModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "vnl",
            "league": "NCAA",
            "event": "Nebraska vs Wisconsin",
            "market": "match_winner",
            "selection": "Nebraska",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Nebraska match winner +100 vs Wisconsin",
            "visible_markets": ["match_winner"],
            "input_stats": volleyball_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "volleyball")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("volleyball")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "volleyball_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_volleyball_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "volleyball")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = volleyball_inputs()
        stats.pop("team_sideout_rate")
        stats.pop("team_sideout_pct", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = volleyball_alias_inputs(team_attack="bad", team_sideout_pct="bad", team_serve="text", team_set_win_pct="bad")
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_bad_odds_do_not_activate_from_default(self):
        self.assertEqual(self._sport(odds_american="not odds")["model_status"], "inactive_missing_data")

    def test_odds_do_not_drive_final_probability(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-140, 100, 135)}
        probs = [result["final_probability"] for result in results.values()]
        self.assertLess(max(probs) - min(probs), 0.000001)

    def test_odds_change_only_market_outputs(self):
        low = self._sport(odds_american=-140)
        high = self._sport(odds_american=135)
        self.assertEqual(low["final_probability"], high["final_probability"])
        self.assertNotEqual(low["implied_probability"], high["implied_probability"])
        self.assertLess(low["edge_percent"], high["edge_percent"])

    def test_negative_edge_creates_no_bet(self): self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(input_stats=volleyball_inputs(book_count=1, team_injury_availability_rating=0.70, key_player_availability=0.68))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_public_sharp_market_movement_are_enrichment_only(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=volleyball_inputs(public_betting_percent=99, sharp_money_percent=1, market_movement=9))["final_probability"]
        self.assertEqual(base, enriched)

    def test_enrichment_alone_cannot_confirm(self):
        response = self._sport(input_stats={"public_betting_percent": 95, "sharp_money_percent": 90, "market_movement": 7})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_moneyline_market_works(self): self.assert_active(self._sport(market="moneyline"))
    def test_set_winner_market_works(self): self.assert_active(self._sport(market="set_winner"))
    def test_correct_score_market_works(self): self.assert_active(self._sport(market="correct_score"))
    def test_set_handicap_market_works(self): self.assert_active(self._sport(market="set_handicap", input_stats=volleyball_inputs(line=-1.5)))
    def test_point_spread_market_works(self): self.assert_active(self._sport(market="point_spread", input_stats=volleyball_inputs(line=-5.5)))
    def test_total_sets_market_works(self): self.assert_active(self._sport(market="total_sets", selection="over", input_stats=volleyball_inputs(line=4.5)))
    def test_total_points_market_works(self): self.assert_active(self._sport(market="total_points", selection="over", input_stats=volleyball_inputs(line=184.5)))
    def test_team_total_points_market_works(self): self.assert_active(self._sport(market="team_total_points", selection="Nebraska over", input_stats=volleyball_inputs(line=92.5)))
    def test_first_set_winner_market_works(self): self.assert_active(self._sport(market="first_set_winner"))
    def test_second_set_winner_market_works(self): self.assert_active(self._sport(market="second_set_winner"))
    def test_third_set_winner_market_works(self): self.assert_active(self._sport(market="third_set_winner"))
    def test_fourth_set_winner_market_works(self): self.assert_active(self._sport(market="fourth_set_winner"))
    def test_fifth_set_winner_market_works(self): self.assert_active(self._sport(market="fifth_set_winner"))
    def test_alt_set_handicap_market_works(self): self.assert_active(self._sport(market="alt_set_handicap", input_stats=volleyball_inputs(line=-2.5)))
    def test_alt_total_sets_market_works(self): self.assert_active(self._sport(market="alt_total_sets", selection="over", input_stats=volleyball_inputs(line=5.5)))
    def test_alt_total_points_market_works(self): self.assert_active(self._sport(market="alt_total_points", selection="over", input_stats=volleyball_inputs(line=190.5)))

    def test_player_kills_prop_works(self): self.assert_active(self._sport(market="player_kills", selection="Merritt Beason over", input_stats=volleyball_inputs(line=16.5)))
    def test_player_aces_prop_works(self): self.assert_active(self._sport(market="player_aces", selection="Merritt Beason over", input_stats=volleyball_inputs(line=0.5)))
    def test_player_blocks_prop_works(self): self.assert_active(self._sport(market="player_blocks", selection="Merritt Beason over", input_stats=volleyball_inputs(line=1.5)))
    def test_player_digs_prop_works(self): self.assert_active(self._sport(market="player_digs", selection="Merritt Beason over", input_stats=volleyball_inputs(line=8.5)))
    def test_player_assists_prop_works(self): self.assert_active(self._sport(market="player_assists", selection="Merritt Beason over", input_stats=volleyball_inputs(line=0.5)))
    def test_player_points_prop_works(self): self.assert_active(self._sport(market="player_points", selection="Merritt Beason over", input_stats=volleyball_inputs(line=20.5)))

    def test_calibration_outputs_exist(self):
        response = self._sport()
        self.assertEqual(response["format_calibration_applied"], "best_of_5")
        self.assertEqual(response["court_calibration_applied"], "indoor")
        self.assertEqual(response["gender_calibration_applied"], "womens")
        self.assertTrue(response["sideout_calibration_applied"])
        self.assertTrue(response["serve_receive_calibration_applied"])
        self.assertTrue(response["deciding_set_calibration_applied"])

    def test_best_of_3_and_unknown_calibrations(self):
        self.assertEqual(self._sport(input_stats=volleyball_inputs(best_of_sets=3, match_format="best_of_3"))["format_calibration_applied"], "best_of_3")
        self.assertEqual(self._sport(input_stats=volleyball_inputs(best_of_sets=7, match_format="custom"))["format_calibration_applied"], "unknown")

    def test_beach_and_mens_calibrations(self):
        response = self._sport(input_stats=volleyball_inputs(court_type="beach", gender_format="mens"))
        self.assertEqual(response["court_calibration_applied"], "beach")
        self.assertEqual(response["gender_calibration_applied"], "mens")

    def test_sideout_serve_block_edges_affect_probability(self):
        base = self._sport()["final_probability"]
        weaker = self._sport(input_stats=volleyball_inputs(team_sideout_rate=0.50, team_serve_rating=75, team_block_rating=74))["final_probability"]
        self.assertLess(weaker, base)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_volleyball_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("volleyball_input_contract", response)
        self.assertIsNotNone(response["volleyball_projected_total_points"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "format_calibration_applied", "court_calibration_applied", "gender_calibration_applied", "sideout_calibration_applied", "serve_receive_calibration_applied", "deciding_set_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["volleyball_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("volleyball")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
