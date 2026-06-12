import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "rugby_set_piece_territory_expected_points_monte_carlo_model"


def rugby_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("rugby")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def rugby_inputs(**extra):
    ticket = registry.get_sport_model_config("rugby")["screenshot_alias_test_payload"]
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
        "sport": "rugby",
        "league": "Six Nations",
        "event_id": "Ireland vs France",
        "event": "Ireland vs France",
        "market": "match_winner",
        "selection": "Ireland",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Ireland match winner +100 vs France",
        "visible_markets": ["match_winner"],
        "input_stats": rugby_inputs(),
    }
    data.update(extra)
    return data


class TestRugbyModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "rugby_union",
            "league": "Six Nations",
            "event": "Ireland vs France",
            "market": "match_winner",
            "selection": "Ireland",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Ireland match winner +100 vs France",
            "visible_markets": ["match_winner"],
            "input_stats": rugby_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "rugby")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("rugby")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "rugby_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_rugby_model(self):
        for alias in ("rugby", "rugby_union", "rugby_league", "nrl", "super_rugby", "six_nations", "premiership_rugby", "united_rugby_championship", "rugby_world_cup", "top_14"):
            self.assertEqual(registry.normalize_sport_key(alias), "rugby")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = rugby_alias_inputs(team_power_rating="bad", team_set_piece="bad", team_territory="not numeric", team_penalties="bad")
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_odds_stability_at_three_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [result["final_probability"] for result in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_negative_edge_creates_no_bet(self): self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(input_stats=rugby_inputs(book_count=1, rain_probability=0.75, wind_speed=38, weather_risk=0.80, key_player_availability=0.55))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_social_public_data_alone_cannot_confirm(self):
        response = self._sport(input_stats={"social_sentiment": 90, "public_betting_percent": 78, "sharp_money_percent": 64})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_spread_market_works(self): self.assert_active(self._sport(market="spread", input_stats=rugby_inputs(line=-3.5)))
    def test_total_points_market_works(self): self.assert_active(self._sport(market="total_points", selection="over", input_stats=rugby_inputs(line=47.5)))
    def test_team_total_market_works(self): self.assert_active(self._sport(market="team_total_points", selection="over", input_stats=rugby_inputs(line=24.5)))
    def test_first_half_market_works(self): self.assert_active(self._sport(market="first_half_winner"))
    def test_second_half_market_works(self): self.assert_active(self._sport(market="second_half_spread", input_stats=rugby_inputs(line=-1.5)))
    def test_winning_margin_market_works(self): self.assert_active(self._sport(market="winning_margin", input_stats=rugby_inputs(line=7.5)))
    def test_draw_no_bet_market_works(self): self.assert_active(self._sport(market="draw_no_bet"))
    def test_anytime_try_scorer_prop_works(self): self.assert_active(self._sport(market="anytime_try_scorer", selection="James Lowe"))
    def test_first_try_scorer_prop_works(self): self.assert_active(self._sport(market="first_try_scorer", selection="James Lowe"))
    def test_player_points_prop_works(self): self.assert_active(self._sport(market="player_points", selection="James Lowe over", input_stats=rugby_inputs(line=4.5)))
    def test_player_tackles_prop_works(self): self.assert_active(self._sport(market="player_tackles", selection="James Lowe over", input_stats=rugby_inputs(line=7.5)))
    def test_player_kicking_points_prop_works(self): self.assert_active(self._sport(market="player_kicking_points", selection="James Lowe over", input_stats=rugby_inputs(line=0.5, player_kicking_points_projection=1.2)))

    def test_rugby_union_calibration_works(self): self.assertEqual(self._sport()["code_variant_calibration_applied"], "rugby_union")
    def test_rugby_league_calibration_works(self): self.assertEqual(self._sport(input_stats=rugby_inputs(code_variant="rugby_league"))["code_variant_calibration_applied"], "rugby_league")
    def test_weather_calibration_works(self): self.assertEqual(self._sport(input_stats=rugby_inputs(rain_probability=0.65, weather_risk=0.65))["weather_calibration_applied"], "wet")
    def test_referee_calibration_works(self): self.assertTrue(self._sport()["referee_calibration_applied"])

    def test_set_piece_fields_affect_output(self):
        base = self._sport()["rugby_set_piece_edge_score"]
        changed = self._sport(input_stats=rugby_inputs(team_set_piece_rating=78))["rugby_set_piece_edge_score"]
        self.assertNotEqual(base, changed)

    def test_territory_fields_affect_output(self):
        base = self._sport()["rugby_territory_edge_score"]
        changed = self._sport(input_stats=rugby_inputs(team_territory_rating=76))["rugby_territory_edge_score"]
        self.assertNotEqual(base, changed)

    def test_discipline_card_risk_can_force_no_bet(self):
        response = self._sport(input_stats=rugby_inputs(team_yellow_card_rate=0.80, team_red_card_rate=0.22))
        self.assertIn("discipline/card risk", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_key_player_availability_affects_output(self):
        base = self._sport()["rugby_projected_margin"]
        changed = self._sport(input_stats=rugby_inputs(key_player_availability=0.55))["rugby_projected_margin"]
        self.assertNotEqual(base, changed)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_rugby_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("rugby_input_contract", response)
        self.assertIsNotNone(response["rugby_projected_total"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "code_variant_calibration_applied", "competition_calibration_applied", "weather_calibration_applied", "referee_calibration_applied"):
            self.assertIn(field, row)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("rugby")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
