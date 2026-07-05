import asyncio
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "lacrosse_faceoff_possession_shot_quality_monte_carlo_model"
ALIASES = (
    "lacrosse", "lax", "mens_lacrosse", "womens_lacrosse", "college_lacrosse",
    "ncaa_lacrosse", "pll", "premier_lacrosse_league", "nll", "national_lacrosse_league",
)


def lacrosse_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("lacrosse")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def lacrosse_inputs(**extra):
    ticket = registry.get_sport_model_config("lacrosse")["screenshot_alias_test_payload"]
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
        "sport": "lacrosse",
        "league": "PLL",
        "event_id": "Atlas vs Whipsnakes",
        "event": "Atlas vs Whipsnakes",
        "market": "match_winner",
        "selection": "Atlas",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Atlas match winner +100 vs Whipsnakes",
        "visible_markets": ["match_winner"],
        "input_stats": lacrosse_inputs(),
    }
    data.update(extra)
    return data


class TestLacrosseModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "pll",
            "league": "PLL",
            "event": "Atlas vs Whipsnakes",
            "market": "match_winner",
            "selection": "Atlas",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Atlas match winner +100 vs Whipsnakes",
            "visible_markets": ["match_winner"],
            "input_stats": lacrosse_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "lacrosse")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("lacrosse")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "lacrosse_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_lacrosse_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "lacrosse")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = lacrosse_inputs()
        stats.pop("team_faceoff_win_rate")
        stats.pop("team_faceoff_pct", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = lacrosse_alias_inputs(team_power_rating="bad", team_faceoff_pct="bad", team_shot_quality="text", goalie_score="bad")
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
        response = self._sport(input_stats=lacrosse_inputs(book_count=1, weather_risk=0.80, wind_speed=32, key_player_availability=0.55, goalie_rating=60))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_social_public_sharp_data_alone_cannot_confirm(self):
        response = self._sport(input_stats={"social_sentiment": 90, "public_betting_percent": 78, "sharp_money_percent": 64})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_enrichment_fields_do_not_change_true_probability(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=lacrosse_inputs(public_betting_percent=99, sharp_money_percent=1, social_sentiment=-90, market_movement=9))["final_probability"]
        self.assertEqual(base, enriched)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_moneyline_market_works(self): self.assert_active(self._sport(market="moneyline"))
    def test_spread_market_works(self): self.assert_active(self._sport(market="spread", input_stats=lacrosse_inputs(line=-1.5)))
    def test_handicap_market_works(self): self.assert_active(self._sport(market="handicap", input_stats=lacrosse_inputs(line=-1.5)))
    def test_total_goals_market_works(self): self.assert_active(self._sport(market="total_goals", selection="over", input_stats=lacrosse_inputs(line=24.5)))
    def test_team_total_goals_market_works(self): self.assert_active(self._sport(market="team_total_goals", selection="over", input_stats=lacrosse_inputs(line=12.5)))
    def test_first_half_winner_market_works(self): self.assert_active(self._sport(market="first_half_winner"))
    def test_first_half_spread_market_works(self): self.assert_active(self._sport(market="first_half_spread", input_stats=lacrosse_inputs(line=-0.5)))
    def test_first_half_total_market_works(self): self.assert_active(self._sport(market="first_half_total", selection="over", input_stats=lacrosse_inputs(line=12.0)))
    def test_second_half_winner_market_works(self): self.assert_active(self._sport(market="second_half_winner"))
    def test_second_half_spread_market_works(self): self.assert_active(self._sport(market="second_half_spread", input_stats=lacrosse_inputs(line=-0.5)))
    def test_second_half_total_market_works(self): self.assert_active(self._sport(market="second_half_total", selection="over", input_stats=lacrosse_inputs(line=12.0)))
    def test_quarter_winner_market_works(self): self.assert_active(self._sport(market="quarter_winner"))
    def test_quarter_spread_market_works(self): self.assert_active(self._sport(market="quarter_spread", input_stats=lacrosse_inputs(line=-0.5)))
    def test_quarter_total_market_works(self): self.assert_active(self._sport(market="quarter_total", selection="over", input_stats=lacrosse_inputs(line=6.0)))
    def test_winning_margin_market_works(self): self.assert_active(self._sport(market="winning_margin", input_stats=lacrosse_inputs(line=2.5)))
    def test_alt_spread_market_works(self): self.assert_active(self._sport(market="alt_spread", input_stats=lacrosse_inputs(line=-2.5)))
    def test_alt_total_goals_market_works(self): self.assert_active(self._sport(market="alt_total_goals", selection="over", input_stats=lacrosse_inputs(line=25.5)))
    def test_alt_team_total_goals_market_works(self): self.assert_active(self._sport(market="alt_team_total_goals", selection="over", input_stats=lacrosse_inputs(line=13.5)))

    def test_player_goals_prop_works(self): self.assert_active(self._sport(market="player_goals", selection="Jeff Teat over", input_stats=lacrosse_inputs(line=1.5)))
    def test_player_assists_prop_works(self): self.assert_active(self._sport(market="player_assists", selection="Jeff Teat over", input_stats=lacrosse_inputs(line=1.5)))
    def test_player_points_prop_works(self): self.assert_active(self._sport(market="player_points", selection="Jeff Teat over", input_stats=lacrosse_inputs(line=3.5)))
    def test_player_shots_prop_works(self): self.assert_active(self._sport(market="player_shots", selection="Jeff Teat over", input_stats=lacrosse_inputs(line=7.5)))
    def test_player_shots_on_goal_prop_works(self): self.assert_active(self._sport(market="player_shots_on_goal", selection="Jeff Teat over", input_stats=lacrosse_inputs(line=4.5)))
    def test_player_saves_prop_works(self): self.assert_active(self._sport(market="player_saves", selection="Atlas goalie over", input_stats=lacrosse_inputs(line=10.5, player_saves_projection=12.0)))
    def test_player_ground_balls_prop_works(self): self.assert_active(self._sport(market="player_ground_balls", selection="Jeff Teat over", input_stats=lacrosse_inputs(line=1.5)))
    def test_player_faceoff_wins_prop_works(self): self.assert_active(self._sport(market="player_faceoff_wins", selection="Atlas FOGO over", input_stats=lacrosse_inputs(line=10.5, player_faceoff_wins_projection=13.0)))
    def test_anytime_goal_scorer_prop_works(self): self.assert_active(self._sport(market="anytime_goal_scorer", selection="Jeff Teat"))
    def test_first_goal_scorer_prop_works(self): self.assert_active(self._sport(market="first_goal_scorer", selection="Jeff Teat"))

    def test_format_calibration_field_works(self): self.assertEqual(self._sport()["format_calibration_applied"], "field")
    def test_box_format_calibration_works(self): self.assertEqual(self._sport(input_stats=lacrosse_inputs(indoor_outdoor="box", league="NLL", competition="NLL"))["format_calibration_applied"], "box")
    def test_gender_calibration_field_works(self): self.assertEqual(self._sport()["gender_calibration_applied"], "mens")
    def test_womens_gender_calibration_works(self): self.assertEqual(self._sport(input_stats=lacrosse_inputs(gender_format="womens"))["gender_calibration_applied"], "womens")
    def test_competition_calibration_works(self): self.assertEqual(self._sport()["competition_calibration_applied"], "pll")
    def test_weather_calibration_works(self): self.assertEqual(self._sport(input_stats=lacrosse_inputs(weather_risk=0.70, field_condition="wet"))["weather_calibration_applied"], "wet")
    def test_faceoff_calibration_works(self): self.assertTrue(self._sport()["faceoff_calibration_applied"])
    def test_goalie_calibration_works(self): self.assertTrue(self._sport()["goalie_calibration_applied"])

    def test_faceoff_fields_affect_output(self):
        base = self._sport()["lacrosse_faceoff_edge_score"]
        changed = self._sport(input_stats=lacrosse_inputs(team_faceoff_win_rate=0.45))["lacrosse_faceoff_edge_score"]
        self.assertNotEqual(base, changed)

    def test_shot_quality_fields_affect_output(self):
        base = self._sport()["lacrosse_shot_quality_edge_score"]
        changed = self._sport(input_stats=lacrosse_inputs(team_shot_quality_rating=75))["lacrosse_shot_quality_edge_score"]
        self.assertNotEqual(base, changed)

    def test_goalie_fields_affect_output(self):
        base = self._sport()["lacrosse_goalie_edge_score"]
        changed = self._sport(input_stats=lacrosse_inputs(goalie_rating=70))["lacrosse_goalie_edge_score"]
        self.assertNotEqual(base, changed)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_lacrosse_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("lacrosse_input_contract", response)
        self.assertIsNotNone(response["lacrosse_projected_total"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "format_calibration_applied", "gender_calibration_applied", "competition_calibration_applied", "weather_calibration_applied", "faceoff_calibration_applied", "goalie_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["lacrosse_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("lacrosse")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
