import asyncio
import unittest
from unittest.mock import patch

from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def ncaawb_inputs(**extra):
    data = {
        "home_team": "South Carolina", "away_team": "UConn", "team": "South Carolina", "opponent": "UConn",
        "home_offensive_rating": 114.0, "home_defensive_rating": 88.0, "away_offensive_rating": 108.0,
        "away_defensive_rating": 94.5, "home_pace": 72.2, "away_pace": 70.4, "home_effective_fg_pct": 53.5,
        "away_effective_fg_pct": 49.8, "home_turnover_rate": 12.5, "away_turnover_rate": 14.0,
        "home_rebound_rate": 56.0, "away_rebound_rate": 50.1, "home_free_throw_rate": 28.0,
        "away_free_throw_rate": 24.4, "home_rest_days": 4, "away_rest_days": 3, "home_travel_fatigue": 0.0,
        "away_travel_fatigue": 0.3, "home_rank": 1, "away_rank": 7, "home_strength_rating": 31.0,
        "away_strength_rating": 23.0, "home_conference_strength": 8.8, "away_conference_strength": 8.1,
        "home_experience_rating": 6.8, "away_experience_rating": 6.0, "home_three_point_rate": 36.5,
        "away_three_point_rate": 33.2, "home_free_throw_pct": 75.5, "away_free_throw_pct": 72.0,
        "book_count": 8, "player": "South Carolina Forward", "player_team": "South Carolina",
        "player_minutes_projection": 31, "player_usage_rate": 26, "player_points_projection": 19.5,
        "player_rebounds_projection": 10.2, "player_assists_projection": 3.1, "player_pra_projection": 32.8,
        "player_threes_projection": 1.8, "player_steals_projection": 1.0, "player_blocks_projection": 1.7,
        "player_turnovers_projection": 2.1, "line": 17.5,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {"sport": "ncaawb", "league": "NCAAWB", "event_id": "UConn vs South Carolina", "market": "moneyline",
            "selection": "South Carolina", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
            "risk_profile": "moderate", "input_stats": ncaawb_inputs()}
    data.update(extra)
    return data


def alias_inputs(**extra):
    data = {
        "matchup": "UConn vs South Carolina", "home": "South Carolina", "away": "UConn",
        "team_name": "South Carolina", "opponent_name": "UConn", "pick": "South Carolina",
        "home_off_rating": 114.0, "home_def_rating": 88.0, "away_off_rating": 108.0,
        "away_def_rating": 94.5, "home_pace": 72.2, "away_pace": 70.4, "home_efg": 53.5,
        "away_efg": 49.8, "home_tov": 12.5, "away_tov": 14.0, "home_oreb": 56.0,
        "away_oreb": 50.1, "home_ft_rate": 28.0, "away_ft_rate": 24.4, "home_rest_days": 4,
        "away_rest_days": 3, "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.3,
        "home_ap_rank": 1, "away_ap_rank": 7, "home_net_rating": 31.0, "away_net_rating": 23.0,
        "home_conference_rating": 8.8, "away_conference_rating": 8.1, "home_experience": 6.8,
        "away_experience": 6.0, "home_3p_rate": 36.5, "away_3p_rate": 33.2,
        "home_ft_pct": 75.5, "away_ft_pct": 72.0, "book_count": 8,
    }
    data.update(extra)
    return data


class TestWomensCollegeBasketballModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {"source_type": "chatgpt_parsed", "sport": "ncaawb", "league": "NCAAWB",
                "event": "UConn vs South Carolina", "teams": ["UConn", "South Carolina"], "market": "moneyline",
                "selection": "South Carolina", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
                "risk_profile": "moderate", "input_stats": alias_inputs()}
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "womens_college_basketball_possession_variance_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "ncaawb")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self): self.assertEqual(self._sport(input_stats={})["confirmed_bets"], [])
    def test_bad_text_input_safety(self): self.assertEqual(self._sport(input_stats="bad")["confirmed_bets"], [])
    def test_moneyline_confirmed_capable(self): self.assertTrue(self._sport()["confirmed_bets"])
    def test_spread_active(self): self.assert_active(self._sport(market="spread", line=-4.5, input_stats=ncaawb_inputs(line=-4.5)))
    def test_total_active(self): self.assert_active(self._sport(market="total", selection="over", total_line=142.5, input_stats=ncaawb_inputs(total_line=142.5)))
    def test_team_total_active(self): self.assert_active(self._sport(market="team_total", selection="over", total_line=75.5, input_stats=ncaawb_inputs(total_line=75.5)))
    def test_first_half_active(self): self.assert_active(self._sport(market="first_half_moneyline"))
    def test_first_quarter_active(self): self.assert_active(self._sport(market="first_quarter_moneyline"))
    def test_player_points_prop_active(self): self.assert_active(self._sport(market="player_points", selection="over", line=17.5, input_stats=ncaawb_inputs(line=17.5)))
    def test_player_pra_prop_active(self): self.assert_active(self._sport(market="player_pra", selection="over", line=30.5, input_stats=ncaawb_inputs(line=30.5)))
    def test_player_threes_prop_active(self): self.assert_active(self._sport(market="player_threes", selection="over", line=1.5, input_stats=ncaawb_inputs(line=1.5)))
    def test_negative_edge_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-400)["status"], "evaluated_no_bet")
    def test_edge_too_small_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-220)["status"], "evaluated_no_bet_edge_too_small")
    def test_low_confidence_no_bet(self): self.assertEqual(self._sport(market="player_points", selection="over", line=17.5, input_stats=ncaawb_inputs(player_minutes_projection=10))["status"], "evaluated_no_bet_low_confidence")
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
    def test_womens_college_calibration_label(self): self.assertEqual(self._sport()["league_calibration_applied"], "ncaawb")


if __name__ == "__main__":
    unittest.main()
