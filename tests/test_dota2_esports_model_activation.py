import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def dota2_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("dota2")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def dota2_inputs(**extra):
    payload = registry.get_sport_model_config("dota2")["screenshot_alias_test_payload"]
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
        "sport": "dota2",
        "league": "The International",
        "event_id": "Team Liquid vs Gaimin Gladiators",
        "event": "Team Liquid vs Gaimin Gladiators",
        "teams": ["Team Liquid", "Gaimin Gladiators"],
        "market": "match_winner",
        "selection": "Team Liquid",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Team Liquid match winner +100 vs Gaimin Gladiators",
        "visible_markets": ["match_winner"],
        "input_stats": dota2_inputs(),
    }
    data.update(extra)
    return data


class TestDota2EsportsModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "dota2",
            "league": "The International",
            "event": "Team Liquid vs Gaimin Gladiators",
            "teams": ["Team Liquid", "Gaimin Gladiators"],
            "market": "match_winner",
            "selection": "Team Liquid",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Team Liquid match winner +100 vs Gaimin Gladiators",
            "visible_markets": ["match_winner"],
            "input_stats": dota2_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "dota2_draft_lane_objective_roshan_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "dota2")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("dota2")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], "dota2_draft_lane_objective_roshan_monte_carlo_model")
        self.assertEqual(config["input_normalizer"], "dota2_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_dota_2_model(self):
        for alias in ("dota2", "dota_2", "dota", "esports_dota2", "dota_pro_circuit", "dpc", "the_international", "ti"):
            self.assertEqual(registry.normalize_sport_key(alias), "dota2")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], "dota2_draft_lane_objective_roshan_monte_carlo_model")

    def test_active_payload_confirms_model_active(self):
        self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = dota2_alias_inputs()
        for key in ("team_elo_rating", "team_win_pct", "team_gd10", "team_draft_score", "team_kills_per_game"):
            malformed[key] = "bad text"
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_odds_stability_at_three_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [result["final_probability"] for result in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_negative_edge_creates_no_bet(self):
        self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(
            market="player_kills",
            selection="over",
            input_stats=dota2_inputs(match_format="bo1", lan_event=False, online_event=True, substitute_risk=0.20, roster_stability=0.65, book_count=1),
        )
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_social_public_data_alone_cannot_confirm(self):
        response = self._sport(input_stats={"social_sentiment": 90, "public_betting_percent": 75, "sharp_money_percent": 65})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_game_winner_market_works(self): self.assert_active(self._sport(market="game_winner"))
    def test_map_handicap_market_works(self): self.assert_active(self._sport(market="map_handicap", input_stats=dota2_inputs(line=-1.5)))
    def test_total_maps_market_works(self): self.assert_active(self._sport(market="total_maps", selection="over", input_stats=dota2_inputs(total_line=2.5)))
    def test_total_kills_market_works(self): self.assert_active(self._sport(market="total_kills", selection="over", input_stats=dota2_inputs(total_line=29.5)))
    def test_team_total_kills_market_works(self): self.assert_active(self._sport(market="team_total_kills", selection="over", input_stats=dota2_inputs(total_line=15.5)))
    def test_kill_handicap_market_works(self): self.assert_active(self._sport(market="kill_handicap", input_stats=dota2_inputs(line=-3.5)))
    def test_first_blood_market_works(self): self.assert_active(self._sport(market="first_blood"))
    def test_first_tower_market_works(self): self.assert_active(self._sport(market="first_tower"))
    def test_first_roshan_market_works(self): self.assert_active(self._sport(market="first_roshan"))
    def test_game_duration_market_works(self): self.assert_active(self._sport(market="game_duration", selection="over", input_stats=dota2_inputs(total_line=38.5)))
    def test_player_kills_prop_works(self): self.assert_active(self._sport(market="player_kills", selection="over"))
    def test_player_assists_prop_works(self): self.assert_active(self._sport(market="player_assists", selection="over"))
    def test_player_deaths_prop_works(self): self.assert_active(self._sport(market="player_deaths", selection="under"))
    def test_player_kda_prop_works(self): self.assert_active(self._sport(market="player_kda", selection="over"))
    def test_player_gpm_prop_works(self): self.assert_active(self._sport(market="player_gpm", selection="over"))
    def test_player_xpm_prop_works(self): self.assert_active(self._sport(market="player_xpm", selection="over"))
    def test_player_net_worth_prop_works(self): self.assert_active(self._sport(market="player_net_worth", selection="over"))

    def test_bo1_calibration_works(self):
        self.assertEqual(self._sport(input_stats=dota2_inputs(match_format="bo1", best_of_maps=1))["match_format_calibration_applied"], "bo1")

    def test_bo3_calibration_works(self):
        self.assertEqual(self._sport()["match_format_calibration_applied"], "bo3")

    def test_bo5_calibration_works(self):
        self.assertEqual(self._sport(input_stats=dota2_inputs(match_format="bo5", best_of_maps=5))["match_format_calibration_applied"], "bo5")

    def test_region_calibration_works(self):
        self.assertEqual(self._sport()["region_calibration_applied"], "western_europe")

    def test_patch_calibration_works(self):
        self.assertEqual(self._sport(input_stats=dota2_inputs(patch_version="14.11"))["patch_calibration_applied"], "14.11")

    def test_draft_calibration_works(self):
        self.assertTrue(self._sport()["draft_calibration_applied"])

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_league_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("dota2_input_contract", response)
        self.assertIsNotNone(response["dota2_match_probability"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "match_format_calibration_applied", "region_calibration_applied", "patch_calibration_applied", "draft_calibration_applied"):
            self.assertIn(field, row)

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()

