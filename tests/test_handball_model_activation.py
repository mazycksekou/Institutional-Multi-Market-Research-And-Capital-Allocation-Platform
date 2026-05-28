import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "handball_fastbreak_goalkeeper_efficiency_monte_carlo_model"
ALIASES = ("handball", "team_handball", "european_handball", "olympic_handball", "ehf", "ihf", "handball_bundesliga", "champions_league_handball")


def handball_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("handball")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def handball_inputs(**extra):
    ticket = registry.get_sport_model_config("handball")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "handball", "league": "EHF Champions League", "event_id": "Kiel vs Barcelona",
        "event": "Kiel vs Barcelona", "market": "match_winner", "selection": "Kiel",
        "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "source_type": "unit_test",
        "screenshot_text": "Kiel match winner +100 vs Barcelona", "visible_markets": ["match_winner"],
        "input_stats": handball_inputs(),
    }
    data.update(extra)
    return data


class TestHandballModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "ehf", "league": "EHF Champions League",
            "event": "Kiel vs Barcelona", "market": "match_winner", "selection": "Kiel",
            "odds_american": 100, "book": "Manual", "bankroll": 1000, "unit_size": 25,
            "risk_profile": "moderate", "screenshot_text": "Kiel match winner +100 vs Barcelona",
            "visible_markets": ["match_winner"], "input_stats": handball_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "handball")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("handball")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "handball_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_handball_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "handball")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = handball_inputs()
        stats.pop("goalkeeper_save_percentage")
        stats.pop("gk_save_pct", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = handball_alias_inputs(team_gf="bad", gk_save_pct="bad", team_fastbreak_pct="text", ref_penalty_rate="bad")
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
        response = self._sport(input_stats=handball_inputs(book_count=1, team_injury_availability_rating=0.70, key_player_availability=0.68, referee_penalty_rate=10.0))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_public_sharp_market_movement_are_enrichment_only(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=handball_inputs(public_betting_percent=99, sharp_money_percent=1, market_movement=9))["final_probability"]
        self.assertEqual(base, enriched)

    def test_enrichment_alone_cannot_confirm(self):
        response = self._sport(input_stats={"public_betting_percent": 95, "sharp_money_percent": 90, "market_movement": 7})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self): self.assert_active(self._sport(market="match_winner"))
    def test_moneyline_market_works(self): self.assert_active(self._sport(market="moneyline"))
    def test_draw_no_bet_market_works(self): self.assert_active(self._sport(market="draw_no_bet"))
    def test_double_chance_market_works(self): self.assert_active(self._sport(market="double_chance"))
    def test_spread_market_works(self): self.assert_active(self._sport(market="spread", input_stats=handball_inputs(line=-2.5)))
    def test_handicap_market_works(self): self.assert_active(self._sport(market="handicap", input_stats=handball_inputs(line=-1.5)))
    def test_total_goals_market_works(self): self.assert_active(self._sport(market="total_goals", selection="over", input_stats=handball_inputs(line=58.5)))
    def test_team_total_goals_market_works(self): self.assert_active(self._sport(market="team_total_goals", selection="Kiel over", input_stats=handball_inputs(line=29.5)))
    def test_first_half_winner_market_works(self): self.assert_active(self._sport(market="first_half_winner"))
    def test_first_half_spread_market_works(self): self.assert_active(self._sport(market="first_half_spread", input_stats=handball_inputs(line=-1.5)))
    def test_first_half_total_market_works(self): self.assert_active(self._sport(market="first_half_total", selection="over", input_stats=handball_inputs(line=29.5)))
    def test_second_half_winner_market_works(self): self.assert_active(self._sport(market="second_half_winner"))
    def test_second_half_spread_market_works(self): self.assert_active(self._sport(market="second_half_spread", input_stats=handball_inputs(line=-1.5)))
    def test_second_half_total_market_works(self): self.assert_active(self._sport(market="second_half_total", selection="over", input_stats=handball_inputs(line=29.5)))
    def test_winning_margin_market_works(self): self.assert_active(self._sport(market="winning_margin"))
    def test_correct_score_market_works(self): self.assert_active(self._sport(market="correct_score"))
    def test_alt_spread_market_works(self): self.assert_active(self._sport(market="alt_spread", input_stats=handball_inputs(line=-3.5)))
    def test_alt_total_goals_market_works(self): self.assert_active(self._sport(market="alt_total_goals", selection="over", input_stats=handball_inputs(line=60.5)))
    def test_alt_team_total_goals_market_works(self): self.assert_active(self._sport(market="alt_team_total_goals", selection="Kiel over", input_stats=handball_inputs(line=31.5)))

    def test_player_goals_prop_works(self): self.assert_active(self._sport(market="player_goals", selection="Sander Sagosen over", input_stats=handball_inputs(line=5.5)))
    def test_player_assists_prop_works(self): self.assert_active(self._sport(market="player_assists", selection="Sander Sagosen over", input_stats=handball_inputs(line=3.5)))
    def test_player_saves_prop_works(self): self.assert_active(self._sport(market="player_saves", selection="Goalkeeper over", input_stats=handball_inputs(line=0.5, player_saves_projection=1.2)))
    def test_player_shots_prop_works(self): self.assert_active(self._sport(market="player_shots", selection="Sander Sagosen over", input_stats=handball_inputs(line=8.5)))
    def test_player_points_prop_works(self): self.assert_active(self._sport(market="player_points", selection="Sander Sagosen over", input_stats=handball_inputs(line=9.5)))
    def test_anytime_goal_scorer_prop_works(self): self.assert_active(self._sport(market="anytime_goal_scorer", selection="Sander Sagosen yes"))
    def test_first_goal_scorer_prop_works(self): self.assert_active(self._sport(market="first_goal_scorer", selection="Sander Sagosen yes"))

    def test_calibration_outputs_exist(self):
        response = self._sport()
        self.assertEqual(response["competition_calibration_applied"], "league")
        self.assertTrue(response["pace_calibration_applied"])
        self.assertTrue(response["goalkeeper_calibration_applied"])
        self.assertTrue(response["fastbreak_calibration_applied"])
        self.assertTrue(response["discipline_calibration_applied"])

    def test_cup_and_international_calibrations(self):
        self.assertEqual(self._sport(input_stats=handball_inputs(competition="German Cup"))["competition_calibration_applied"], "cup")
        self.assertEqual(self._sport(input_stats=handball_inputs(competition="IHF World Championship"))["competition_calibration_applied"], "international")

    def test_unknown_competition_calibration(self):
        self.assertEqual(self._sport(input_stats=handball_inputs(competition="Friendly Series"))["competition_calibration_applied"], "unknown")

    def test_goalkeeper_fastbreak_discipline_edges_affect_probability(self):
        base = self._sport()["final_probability"]
        weaker = self._sport(input_stats=handball_inputs(goalkeeper_save_percentage=0.25, team_fastbreak_rate=0.10, team_two_minute_suspension_rate=5.0))["final_probability"]
        self.assertLess(weaker, base)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_handball_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("handball_input_contract", response)
        self.assertIsNotNone(response["handball_projected_total_goals"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "competition_calibration_applied", "pace_calibration_applied", "goalkeeper_calibration_applied", "fastbreak_calibration_applied", "discipline_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["handball_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("handball")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
