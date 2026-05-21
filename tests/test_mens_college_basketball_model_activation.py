import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def ncaab_inputs(**extra):
    data = {
        "home_team": "Duke", "away_team": "North Carolina", "team": "Duke", "opponent": "North Carolina",
        "home_offensive_rating": 116.0, "home_defensive_rating": 94.5, "away_offensive_rating": 111.0,
        "away_defensive_rating": 99.0, "home_pace": 70.5, "away_pace": 69.1, "home_effective_fg_pct": 54.0,
        "away_effective_fg_pct": 50.4, "home_turnover_rate": 13.0, "away_turnover_rate": 15.2,
        "home_rebound_rate": 53.0, "away_rebound_rate": 49.5, "home_free_throw_rate": 31.0,
        "away_free_throw_rate": 27.5, "home_rest_days": 5, "away_rest_days": 3, "home_travel_fatigue": 0.0,
        "away_travel_fatigue": 0.4, "home_rank": 4, "away_rank": 16, "home_strength_rating": 28.5,
        "away_strength_rating": 20.0, "home_conference_strength": 8.5, "away_conference_strength": 7.8,
        "home_experience_rating": 6.2, "away_experience_rating": 5.1, "home_three_point_rate": 38.5,
        "away_three_point_rate": 34.1, "home_free_throw_pct": 76.0, "away_free_throw_pct": 71.5,
        "book_count": 8, "player": "Duke Guard", "player_team": "Duke", "player_minutes_projection": 32,
        "player_usage_rate": 25, "player_points_projection": 18.5, "player_rebounds_projection": 5.2,
        "player_assists_projection": 4.8, "player_pra_projection": 28.5, "player_threes_projection": 2.6,
        "player_steals_projection": 1.1, "player_blocks_projection": 0.3, "player_turnovers_projection": 2.2,
        "line": 16.5,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {"sport": "ncaab", "league": "NCAAB", "event_id": "Duke vs North Carolina", "market": "moneyline",
            "selection": "Duke", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
            "risk_profile": "moderate", "input_stats": ncaab_inputs()}
    data.update(extra)
    return data


def alias_inputs(**extra):
    data = {
        "matchup": "Duke vs North Carolina", "home": "Duke", "away": "North Carolina", "team_name": "Duke",
        "opponent_name": "North Carolina", "pick": "Duke", "home_off_rating": 116.0, "home_def_rating": 94.5,
        "away_off_rating": 111.0, "away_def_rating": 99.0, "home_pace": 70.5, "away_pace": 69.1,
        "home_efg": 54.0, "away_efg": 50.4, "home_tov": 13.0, "away_tov": 15.2, "home_oreb": 53.0,
        "away_oreb": 49.5, "home_ft_rate": 31.0, "away_ft_rate": 27.5, "home_rest_days": 5,
        "away_rest_days": 3, "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.4, "home_ap_rank": 4,
        "away_ap_rank": 16, "home_kenpom_rating": 28.5, "away_kenpom_rating": 20.0,
        "home_conference_rating": 8.5, "away_conference_rating": 7.8, "home_experience": 6.2,
        "away_experience": 5.1, "home_3p_rate": 38.5, "away_3p_rate": 34.1, "home_ft_pct": 76.0,
        "away_ft_pct": 71.5, "book_count": 8,
    }
    data.update(extra)
    return data


class TestMensCollegeBasketballModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {"source_type": "chatgpt_parsed", "sport": "ncaab", "league": "NCAAB",
                "event": "Duke vs North Carolina", "teams": ["North Carolina", "Duke"], "market": "moneyline",
                "selection": "Duke", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
                "risk_profile": "moderate", "input_stats": alias_inputs()}
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "mens_college_basketball_possession_variance_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "ncaab")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self): self.assertEqual(self._sport(input_stats={})["confirmed_bets"], [])
    def test_bad_text_input_safety(self): self.assertEqual(self._sport(input_stats="bad")["confirmed_bets"], [])
    def test_moneyline_confirmed_capable(self): self.assertTrue(self._sport()["confirmed_bets"])
    def test_spread_active(self): self.assert_active(self._sport(market="spread", line=-3.5, input_stats=ncaab_inputs(line=-3.5)))
    def test_total_active(self): self.assert_active(self._sport(market="total", selection="over", total_line=144.5, input_stats=ncaab_inputs(total_line=144.5)))
    def test_team_total_active(self): self.assert_active(self._sport(market="team_total", selection="over", total_line=74.5, input_stats=ncaab_inputs(total_line=74.5)))
    def test_first_half_active(self): self.assert_active(self._sport(market="first_half_moneyline"))
    def test_first_quarter_active(self): self.assert_active(self._sport(market="first_quarter_moneyline"))
    def test_player_points_prop_active(self): self.assert_active(self._sport(market="player_points", selection="over", line=16.5, input_stats=ncaab_inputs(line=16.5)))
    def test_player_pra_prop_active(self): self.assert_active(self._sport(market="player_pra", selection="over", line=26.5, input_stats=ncaab_inputs(line=26.5)))
    def test_player_threes_prop_active(self): self.assert_active(self._sport(market="player_threes", selection="over", line=1.5, input_stats=ncaab_inputs(line=1.5)))
    def test_negative_edge_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-350)["status"], "evaluated_no_bet")
    def test_edge_too_small_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-200)["status"], "evaluated_no_bet_edge_too_small")
    def test_low_confidence_no_bet(self): self.assertEqual(self._sport(market="player_points", selection="over", line=16.5, input_stats=ncaab_inputs(player_minutes_projection=10))["status"], "evaluated_no_bet_low_confidence")
    def test_odds_stability_across_prices(self):
        results = {o: self._sport(odds_american=o) for o in (-130, 100, 120)}
        self.assertLess(max(r["final_probability"] for r in results.values()) - min(r["final_probability"] for r in results.values()), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])
    def test_provider_failure_safety(self):
        with patch("providers.odds_provider_router.enrich_ticket", side_effect=RuntimeError("boom")):
            self.assertTrue(self._screenshot()["ok"])
    def test_officiating_only_safety_cannot_create_bets(self): self.assertEqual(self._sport(input_stats={"referee_name": "Ref"})["confirmed_bets"], [])
    def test_social_crowd_only_safety_cannot_create_bets(self): self.assertEqual(self._sport(input_stats={"social_sentiment": 90})["confirmed_bets"], [])
    def test_screenshot_analysis_alias_path(self): self.assertEqual(self._screenshot()["model_analysis"]["model_status"], "active")
    def test_confirmed_no_bet_same_selection_mutual_exclusion(self):
        r = self._sport(); c = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in r["confirmed_bets"]}; n = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in r["full_board_preview"]["no_bets"]}; self.assertFalse(c & n)
    def test_logbook_rows_include_required_fields(self):
        row = self._sport()["logbook_ready_rows"][0]
        for f in ("confidence", "model_status", "decision", "stake", "suggested_stake"): self.assertIn(f, row)
    def test_direct_versus_screenshot_normalization_parity(self): self.assertEqual(self._screenshot()["model_analysis"]["model_status"], self._sport()["model_status"])
    def test_mens_college_calibration_label(self): self.assertEqual(self._sport()["league_calibration_applied"], "ncaab")


if __name__ == "__main__":
    unittest.main()
