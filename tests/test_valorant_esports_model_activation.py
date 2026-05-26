import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def valorant_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("valorant")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def valorant_inputs(**extra):
    payload = registry.get_sport_model_config("valorant")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(
        sport=payload["sport"],
        market=payload["market"],
        selection=payload["selection"],
        input_stats=payload["input_stats"],
        ticket=payload,
    )["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "valorant",
        "league": "VCT",
        "event_id": "Sentinels vs Fnatic",
        "event": "Sentinels vs Fnatic",
        "teams": ["Sentinels", "Fnatic"],
        "market": "match_winner",
        "selection": "Sentinels",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Sentinels match winner +100 vs Fnatic",
        "visible_markets": ["match_winner"],
        "input_stats": valorant_inputs(),
    }
    data.update(extra)
    return data


class TestValorantEsportsModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "valorant",
            "league": "VCT",
            "event": "Sentinels vs Fnatic",
            "teams": ["Sentinels", "Fnatic"],
            "market": "match_winner",
            "selection": "Sentinels",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Sentinels match winner +100 vs Fnatic",
            "visible_markets": ["match_winner"],
            "input_stats": valorant_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "valorant_agent_composition_economy_map_pool_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "valorant")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("valorant")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], "valorant_agent_composition_economy_map_pool_monte_carlo_model")
        self.assertEqual(config["input_normalizer"], "valorant_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_valorant_model(self):
        for alias in ("valorant", "val", "riot_valorant", "esports_valorant", "vct", "valorant_champions_tour"):
            self.assertEqual(registry.normalize_sport_key(alias), "valorant")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], "valorant_agent_composition_economy_map_pool_monte_carlo_model")

    def test_active_payload_confirms_model_active(self):
        self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = valorant_alias_inputs()
        for key in ("team_elo_rating", "team_win_pct", "team_round_win_pct", "team_attack_pct", "team_adr_value"):
            malformed[key] = "bad text"
        response = self._screenshot(input_stats=malformed)
        analysis = response["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_odds_stability_at_three_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [result["final_probability"] for result in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_negative_edge_creates_no_bet(self):
        self.assertEqual(self._sport(odds_american=-500)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(
            market="player_kills",
            selection="over",
            input_stats=valorant_inputs(match_format="bo1", lan_event=False, online_event=True, substitute_risk=0.20, roster_stability=0.65, book_count=1),
        )
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_social_public_data_alone_cannot_confirm(self):
        response = self._sport(input_stats={"social_sentiment": 90, "public_betting_percent": 75, "sharp_money_percent": 65})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_map_winner_market_works(self): self.assert_active(self._sport(market="map_winner"))
    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_map_handicap_market_works(self): self.assert_active(self._sport(market="map_handicap", input_stats=valorant_inputs(line=-1.5)))
    def test_total_maps_market_works(self): self.assert_active(self._sport(market="total_maps", selection="over", input_stats=valorant_inputs(total_line=2.5)))
    def test_total_rounds_market_works(self): self.assert_active(self._sport(market="total_rounds", selection="over", input_stats=valorant_inputs(total_line=43.5)))
    def test_team_total_rounds_market_works(self): self.assert_active(self._sport(market="team_total_rounds", selection="over", input_stats=valorant_inputs(total_line=22.5)))
    def test_pistol_round_market_works(self): self.assert_active(self._sport(market="pistol_round_winner"))
    def test_player_kills_prop_works(self): self.assert_active(self._sport(market="player_kills", selection="over"))
    def test_player_assists_prop_works(self): self.assert_active(self._sport(market="player_assists", selection="over"))
    def test_player_deaths_prop_works(self): self.assert_active(self._sport(market="player_deaths", selection="under"))
    def test_player_acs_prop_works(self): self.assert_active(self._sport(market="player_acs", selection="over"))
    def test_player_adr_prop_works(self): self.assert_active(self._sport(market="player_adr", selection="over"))
    def test_player_kda_prop_works(self): self.assert_active(self._sport(market="player_kda", selection="over"))
    def test_player_first_bloods_prop_works(self): self.assert_active(self._sport(market="player_first_bloods", selection="over"))

    def test_bo1_calibration_works(self):
        self.assertEqual(self._sport(input_stats=valorant_inputs(match_format="bo1", best_of_maps=1))["match_format_calibration_applied"], "bo1")

    def test_bo3_calibration_works(self):
        self.assertEqual(self._sport()["match_format_calibration_applied"], "bo3")

    def test_bo5_calibration_works(self):
        self.assertEqual(self._sport(input_stats=valorant_inputs(match_format="bo5", best_of_maps=5))["match_format_calibration_applied"], "bo5")

    def test_lan_calibration_works(self):
        self.assertEqual(self._sport()["event_environment_calibration_applied"], "lan")

    def test_online_calibration_works(self):
        response = self._sport(input_stats=valorant_inputs(lan_event=False, online_event=True))
        self.assertEqual(response["event_environment_calibration_applied"], "online")

    def test_map_calibration_works(self):
        self.assertEqual(self._sport(input_stats=valorant_inputs(map_name="Bind"))["map_calibration_applied"], "Bind")

    def test_agent_composition_calibration_works(self):
        self.assertTrue(self._sport()["agent_composition_calibration_applied"])

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_valorant_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("valorant_input_contract", response)
        self.assertIsNotNone(response["valorant_match_probability"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "match_format_calibration_applied", "event_environment_calibration_applied", "map_calibration_applied", "agent_composition_calibration_applied"):
            self.assertIn(field, row)

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
