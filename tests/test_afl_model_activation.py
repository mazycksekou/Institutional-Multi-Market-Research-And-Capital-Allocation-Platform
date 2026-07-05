import asyncio
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "afl_clearance_inside50_scoring_shot_monte_carlo_model"
ALIASES = (
    "afl", "australian_rules", "aussie_rules", "australian_football",
    "australian_rules_football", "afl_football", "australian_football_league",
)


def afl_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("afl")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def afl_inputs(**extra):
    ticket = registry.get_sport_model_config("afl")["screenshot_alias_test_payload"]
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
        "sport": "afl",
        "league": "AFL",
        "event_id": "Collingwood vs Carlton",
        "event": "Collingwood vs Carlton",
        "market": "match_winner",
        "selection": "Collingwood",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Collingwood match winner +100 vs Carlton",
        "visible_markets": ["match_winner"],
        "input_stats": afl_inputs(),
    }
    data.update(extra)
    return data


class TestAFLModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "aussie_rules",
            "league": "AFL",
            "event": "Collingwood vs Carlton",
            "market": "match_winner",
            "selection": "Collingwood",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Collingwood match winner +100 vs Carlton",
            "visible_markets": ["match_winner"],
            "input_stats": afl_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "afl")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("afl")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "afl_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_afl_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "afl")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = afl_inputs()
        stats.pop("team_clearance_rate")
        stats.pop("team_clearances", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = afl_alias_inputs(team_power_rating="bad", team_clearances="bad", team_inside50s="text", team_ruck="bad")
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_bad_odds_do_not_activate_from_default(self):
        response = self._sport(odds_american="not odds")
        self.assertEqual(response["model_status"], "inactive_missing_data")

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
        response = self._sport(input_stats=afl_inputs(book_count=1, weather_risk=0.80, rain_probability=0.75, wind_speed=34, key_player_availability=0.55, team_ruck_rating=60))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_social_public_sharp_data_alone_cannot_confirm(self):
        response = self._sport(input_stats={"social_sentiment": 90, "public_betting_percent": 78, "sharp_money_percent": 64})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_enrichment_fields_do_not_change_true_probability(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=afl_inputs(public_betting_percent=99, sharp_money_percent=1, social_sentiment=-90, market_movement=9))["final_probability"]
        self.assertEqual(base, enriched)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_moneyline_market_works(self): self.assert_active(self._sport(market="moneyline"))
    def test_spread_market_works(self): self.assert_active(self._sport(market="spread", input_stats=afl_inputs(line=-8.5)))
    def test_handicap_market_works(self): self.assert_active(self._sport(market="handicap", input_stats=afl_inputs(line=-8.5)))
    def test_total_points_market_works(self): self.assert_active(self._sport(market="total_points", selection="over", input_stats=afl_inputs(line=170.5)))
    def test_team_total_points_market_works(self): self.assert_active(self._sport(market="team_total_points", selection="over", input_stats=afl_inputs(line=86.5)))
    def test_first_half_winner_market_works(self): self.assert_active(self._sport(market="first_half_winner"))
    def test_first_half_spread_market_works(self): self.assert_active(self._sport(market="first_half_spread", input_stats=afl_inputs(line=-4.5)))
    def test_first_half_total_market_works(self): self.assert_active(self._sport(market="first_half_total", selection="over", input_stats=afl_inputs(line=84.5)))
    def test_quarter_winner_market_works(self): self.assert_active(self._sport(market="quarter_winner"))
    def test_quarter_spread_market_works(self): self.assert_active(self._sport(market="quarter_spread", input_stats=afl_inputs(line=-2.5)))
    def test_quarter_total_market_works(self): self.assert_active(self._sport(market="quarter_total", selection="over", input_stats=afl_inputs(line=42.5)))
    def test_winning_margin_market_works(self): self.assert_active(self._sport(market="winning_margin", input_stats=afl_inputs(line=12.5)))
    def test_exact_margin_market_works(self): self.assert_active(self._sport(market="exact_margin", input_stats=afl_inputs(line=12.5)))
    def test_alt_spread_market_works(self): self.assert_active(self._sport(market="alt_spread", input_stats=afl_inputs(line=-14.5)))
    def test_alt_total_points_market_works(self): self.assert_active(self._sport(market="alt_total_points", selection="over", input_stats=afl_inputs(line=176.5)))
    def test_alt_team_total_points_market_works(self): self.assert_active(self._sport(market="alt_team_total_points", selection="over", input_stats=afl_inputs(line=91.5)))

    def test_player_goals_prop_works(self): self.assert_active(self._sport(market="player_goals", selection="Nick Daicos over", input_stats=afl_inputs(line=0.5)))
    def test_player_disposals_prop_works(self): self.assert_active(self._sport(market="player_disposals", selection="Nick Daicos over", input_stats=afl_inputs(line=27.5)))
    def test_player_marks_prop_works(self): self.assert_active(self._sport(market="player_marks", selection="Nick Daicos over", input_stats=afl_inputs(line=4.5)))
    def test_player_tackles_prop_works(self): self.assert_active(self._sport(market="player_tackles", selection="Nick Daicos over", input_stats=afl_inputs(line=4.5)))
    def test_player_hitouts_prop_works(self): self.assert_active(self._sport(market="player_hitouts", selection="Ruck over", input_stats=afl_inputs(line=18.5, player_hitouts_projection=24.0)))
    def test_player_fantasy_points_prop_works(self): self.assert_active(self._sport(market="player_fantasy_points", selection="Nick Daicos over", input_stats=afl_inputs(line=99.5)))
    def test_anytime_goal_scorer_prop_works(self): self.assert_active(self._sport(market="anytime_goal_scorer", selection="Nick Daicos"))
    def test_first_goal_scorer_prop_works(self): self.assert_active(self._sport(market="first_goal_scorer", selection="Nick Daicos"))

    def test_venue_calibration_field_works(self): self.assertEqual(self._sport()["venue_calibration_applied"], "venue")
    def test_weather_calibration_wet_works(self): self.assertEqual(self._sport(input_stats=afl_inputs(rain_probability=0.70, ground_condition="wet"))["weather_calibration_applied"], "wet")
    def test_weather_calibration_windy_works(self): self.assertEqual(self._sport(input_stats=afl_inputs(wind_speed=34, rain_probability=0.05, ground_condition="firm"))["weather_calibration_applied"], "windy")
    def test_weather_calibration_mixed_works(self): self.assertEqual(self._sport(input_stats=afl_inputs(wind_speed=34, rain_probability=0.70, ground_condition="wet"))["weather_calibration_applied"], "mixed")
    def test_ground_calibration_works(self): self.assertEqual(self._sport()["ground_calibration_applied"], "firm")
    def test_heavy_ground_calibration_works(self): self.assertEqual(self._sport(input_stats=afl_inputs(ground_condition="heavy"))["ground_calibration_applied"], "heavy")
    def test_clearance_calibration_works(self): self.assertTrue(self._sport()["clearance_calibration_applied"])
    def test_inside50_calibration_works(self): self.assertTrue(self._sport()["inside50_calibration_applied"])
    def test_ruck_calibration_works(self): self.assertTrue(self._sport()["ruck_calibration_applied"])

    def test_clearance_fields_affect_output(self):
        base = self._sport()["afl_clearance_edge_score"]
        changed = self._sport(input_stats=afl_inputs(team_clearance_rate=33.0))["afl_clearance_edge_score"]
        self.assertNotEqual(base, changed)

    def test_inside50_fields_affect_output(self):
        base = self._sport()["afl_inside50_edge_score"]
        changed = self._sport(input_stats=afl_inputs(team_inside50_rate=48.0))["afl_inside50_edge_score"]
        self.assertNotEqual(base, changed)

    def test_ruck_fields_affect_output(self):
        base = self._sport()["afl_ruck_edge_score"]
        changed = self._sport(input_stats=afl_inputs(team_ruck_rating=70))["afl_ruck_edge_score"]
        self.assertNotEqual(base, changed)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_afl_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("afl_input_contract", response)
        self.assertIsNotNone(response["afl_projected_total"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "venue_calibration_applied", "weather_calibration_applied", "ground_calibration_applied", "clearance_calibration_applied", "inside50_calibration_applied", "ruck_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["afl_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_input_contract_contains_required_afl_fields(self):
        contract = self._sport()["afl_input_contract"]
        required = set(contract["required_core_inputs"])
        for field in ("team_clearance_rate", "team_inside50_rate", "team_ruck_rating", "umpire_free_kick_rate"):
            self.assertIn(field, required)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("afl")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
