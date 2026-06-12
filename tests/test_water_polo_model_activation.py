import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot

MODEL_NAME = "water_polo_goalkeeper_power_play_shot_quality_monte_carlo_model"
ALIASES = ("water_polo", "waterpolo", "olympic_water_polo", "ncaa_water_polo", "world_aquatics_water_polo", "fina_water_polo", "mens_water_polo", "womens_water_polo")

def water_polo_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("water_polo")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data

def water_polo_inputs(**extra):
    ticket = registry.get_sport_model_config("water_polo")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)["input_stats"]
    normalized.update(extra)
    return normalized

def payload(**extra):
    data = {"sport": "water_polo", "league": "World Aquatics", "event_id": "Hungary vs Spain", "event": "Hungary vs Spain", "market": "match_winner", "selection": "Hungary", "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate", "source_type": "unit_test", "screenshot_text": "Hungary match winner +100 vs Spain", "visible_markets": ["match_winner"], "input_stats": water_polo_inputs()}
    data.update(extra); return data

class TestWaterPoloModelActivation(unittest.TestCase):
    def _sport(self, **extra): return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))
    def _screenshot(self, **extra):
        data = {"source_type": "chatgpt_parsed", "sport": "world_aquatics_water_polo", "league": "World Aquatics", "event": "Hungary vs Spain", "market": "match_winner", "selection": "Hungary", "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate", "screenshot_text": "Hungary match winner +100 vs Spain", "visible_markets": ["match_winner"], "input_stats": water_polo_alias_inputs()}
        data.update(extra); return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))
    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME); self.assertEqual(response["model_status"], "active"); self.assertEqual(response["league_calibration_applied"], "water_polo")

    def test_registry_entry_exists(self): self.assertEqual(registry.get_sport_model_config("water_polo")["model_used"], MODEL_NAME)
    def test_aliases_route_to_water_polo_model(self):
        for alias in ALIASES: self.assertEqual(registry.normalize_sport_key(alias), "water_polo")
    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())
    def test_missing_inputs_returns_inactive_missing_data(self): self.assertEqual(self._sport(input_stats={})["model_status"], "inactive_missing_data")
    def test_missing_single_required_field_blocks_activation(self): s = water_polo_inputs(); s.pop("goalkeeper_save_percentage", None); s.pop("gk_save_pct", None); self.assertEqual(self._sport(input_stats=s)["model_status"], "inactive_missing_data")
    def test_malformed_text_inputs_do_not_activate(self): self.assertNotEqual(self._screenshot(input_stats=water_polo_alias_inputs(team_power_rating="bad"))["model_analysis"]["model_status"], "active")
    def test_bad_odds_do_not_activate_from_default(self): self.assertNotEqual(self._sport(odds_american="not odds")["model_status"], "active")
    def test_odds_do_not_drive_final_probability(self): self.assertAlmostEqual(self._sport(odds_american=-140)["final_probability"], self._sport(odds_american=135)["final_probability"], places=6)
    def test_odds_change_only_market_outputs(self): self.assertNotEqual(self._sport(odds_american=-140)["implied_probability"], self._sport(odds_american=135)["implied_probability"])
    def test_negative_edge_creates_no_bet(self): self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")
    def test_low_confidence_creates_no_bet(self): self.assertEqual(self._sport(input_stats=water_polo_inputs(book_count=1, key_player_availability=0.65))["status"], "evaluated_no_bet_low_confidence")
    def test_public_sharp_market_movement_are_enrichment_only(self): self.assertEqual(self._sport()["final_probability"], self._sport(input_stats=water_polo_inputs(public_betting_percent=99, sharp_money_percent=1, market_movement=9))["final_probability"])
    def test_enrichment_alone_cannot_confirm(self): self.assertEqual(self._sport(input_stats={"public_betting_percent": 95, "sharp_money_percent": 90, "market_movement": 7})["confirmed_bets"], [])
    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_moneyline_market_works(self): self.assert_active(self._sport(market="moneyline"))
    def test_spread_market_works(self): self.assert_active(self._sport(market="spread", input_stats=water_polo_inputs(line=-1.5)))
    def test_handicap_market_works(self): self.assert_active(self._sport(market="handicap", input_stats=water_polo_inputs(line=-1.5)))
    def test_total_goals_market_works(self): self.assert_active(self._sport(market="total_goals", selection="over", input_stats=water_polo_inputs(line=24.5)))
    def test_team_total_goals_market_works(self): self.assert_active(self._sport(market="team_total_goals", selection="over", input_stats=water_polo_inputs(line=12.5)))
    def test_first_half_winner_market_works(self): self.assert_active(self._sport(market="first_half_winner"))
    def test_first_half_spread_market_works(self): self.assert_active(self._sport(market="first_half_spread", input_stats=water_polo_inputs(line=-0.5)))
    def test_first_half_total_market_works(self): self.assert_active(self._sport(market="first_half_total", selection="over", input_stats=water_polo_inputs(line=12.0)))
    def test_quarter_winner_market_works(self): self.assert_active(self._sport(market="quarter_winner"))
    def test_quarter_spread_market_works(self): self.assert_active(self._sport(market="quarter_spread", input_stats=water_polo_inputs(line=-0.5)))
    def test_quarter_total_market_works(self): self.assert_active(self._sport(market="quarter_total", selection="over", input_stats=water_polo_inputs(line=6.0)))
    def test_winning_margin_market_works(self): self.assert_active(self._sport(market="winning_margin"))
    def test_alt_spread_market_works(self): self.assert_active(self._sport(market="alt_spread", input_stats=water_polo_inputs(line=-2.5)))
    def test_alt_total_goals_market_works(self): self.assert_active(self._sport(market="alt_total_goals", selection="over", input_stats=water_polo_inputs(line=25.5)))
    def test_alt_team_total_goals_market_works(self): self.assert_active(self._sport(market="alt_team_total_goals", selection="over", input_stats=water_polo_inputs(line=13.5)))
    def test_player_goals_prop_works(self): self.assert_active(self._sport(market="player_goals", selection="Denes Varga over", input_stats=water_polo_inputs(line=1.5)))
    def test_player_assists_prop_works(self): self.assert_active(self._sport(market="player_assists", selection="Denes Varga over", input_stats=water_polo_inputs(line=1.5)))
    def test_player_shots_prop_works(self): self.assert_active(self._sport(market="player_shots", selection="Denes Varga over", input_stats=water_polo_inputs(line=5.5)))
    def test_player_saves_prop_works(self): self.assert_active(self._sport(market="player_saves", selection="Goalie over", input_stats=water_polo_inputs(line=0.5, player_saves_projection=1.2)))
    def test_player_points_prop_works(self): self.assert_active(self._sport(market="player_points", selection="Denes Varga over", input_stats=water_polo_inputs(line=3.5)))
    def test_anytime_goal_scorer_prop_works(self): self.assert_active(self._sport(market="anytime_goal_scorer"))
    def test_first_goal_scorer_prop_works(self): self.assert_active(self._sport(market="first_goal_scorer"))
    def test_calibration_outputs_exist(self):
        r = self._sport(); self.assertIn(r["gender_calibration_applied"], {"mens", "womens", "unknown"}); self.assertIn(r["competition_calibration_applied"], {"ncaa", "olympic", "world_aquatics", "professional", "unknown"}); self.assertTrue(r["goalkeeper_calibration_applied"]); self.assertTrue(r["power_play_calibration_applied"]); self.assertTrue(r["exclusion_calibration_applied"]); self.assertTrue(r["pace_calibration_applied"])
    def test_no_confirmed_no_bet_same_selection_overlap(self):
        r = self._sport(); c = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in r["confirmed_bets"]}; n = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in r["full_board_preview"]["no_bets"]}; self.assertFalse(c & n)
    def test_full_board_output_includes_water_polo_fields(self): self.assertIsNotNone(self._sport()["water_polo_projected_total_goals"])
    def test_logbook_fields_exist(self): self.assertIn("confidence", self._sport()["logbook_ready_rows"][0])
    def test_input_contract_contains_required_groups(self): self.assertIn("required_core_inputs", self._sport()["water_polo_input_contract"])
    def test_local_payload_contract_has_no_missing_inputs(self):
        t = registry.get_sport_model_config("water_polo")["screenshot_alias_test_payload"]; n = registry.normalize_sport_inputs_for_model(t["sport"], t["market"], t["selection"], t["input_stats"], t); self.assertEqual(n["missing_inputs_after_normalization"], [])
    def test_screenshot_alias_path_activates(self): self.assertEqual(self._screenshot()["model_analysis"]["model_status"], "active")

if __name__ == "__main__":
    unittest.main()
