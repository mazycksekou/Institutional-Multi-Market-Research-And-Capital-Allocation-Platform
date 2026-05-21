import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def wnba_inputs(**extra):
    data = {
        "home_team": "Liberty", "away_team": "Aces", "team": "Liberty", "opponent": "Aces",
        "home_offensive_rating": 108.5, "home_defensive_rating": 96.2,
        "away_offensive_rating": 103.1, "away_defensive_rating": 101.8,
        "home_pace": 79.4, "away_pace": 77.8, "home_effective_fg_pct": 52.8,
        "away_effective_fg_pct": 49.6, "home_turnover_rate": 13.1, "away_turnover_rate": 14.4,
        "home_rebound_rate": 51.5, "away_rebound_rate": 48.7, "home_free_throw_rate": 25.5,
        "away_free_throw_rate": 22.1, "home_injury_adjustment": 0.2, "away_injury_adjustment": -0.6,
        "home_rest_days": 3, "away_rest_days": 2, "home_travel_fatigue": 0.1, "away_travel_fatigue": 0.8,
        "book_count": 8, "player": "Breanna Stewart", "player_team": "Liberty",
        "player_minutes_projection": 33, "player_usage_rate": 27, "player_points_projection": 22.5,
        "player_rebounds_projection": 9.1, "player_assists_projection": 4.2, "player_pra_projection": 35.8,
        "player_threes_projection": 2.4, "player_steals_projection": 1.2, "player_blocks_projection": 1.4,
        "player_turnovers_projection": 2.5, "line": 20.5,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {
        "sport": "wnba", "league": "WNBA", "event_id": "Aces at Liberty", "market": "moneyline",
        "selection": "Liberty", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "input_stats": wnba_inputs(),
    }
    data.update(extra)
    return data


def alias_inputs(**extra):
    data = {
        "game": "Aces at Liberty", "home": "Liberty", "away": "Aces", "team_name": "Liberty",
        "opponent_name": "Aces", "favorite": "Liberty", "home_off_rating": 108.5,
        "home_def_rating": 96.2, "away_off_rating": 103.1, "away_def_rating": 101.8,
        "home_pace": 79.4, "away_pace": 77.8, "home_efg": 52.8, "away_efg": 49.6,
        "home_tov": 13.1, "away_tov": 14.4, "home_oreb": 51.5, "away_oreb": 48.7,
        "home_ft_rate": 25.5, "away_ft_rate": 22.1, "home_injury_adjustment": 0.2,
        "away_injury_adjustment": -0.6, "home_rest_days": 3, "away_rest_days": 2,
        "home_travel_fatigue": 0.1, "away_travel_fatigue": 0.8, "book_count": 8,
    }
    data.update(extra)
    return data


class TestWnbaModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "wnba", "league": "WNBA",
            "event": "Aces at Liberty", "teams": ["Aces", "Liberty"], "market": "moneyline",
            "selection": "Liberty", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
            "risk_profile": "moderate", "input_stats": alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "wnba_possession_rating_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "wnba")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_bad_text_input_safety(self):
        for bad in (None, "ticket text", {"odds_american": "bad"}):
            response = self._sport(input_stats=bad if bad != {"odds_american": "bad"} else wnba_inputs(), odds_american="bad")
            self.assertEqual(response["confirmed_bets"], [])
            self.assertEqual(response["suggested_stake"], 0)

    def test_moneyline_confirmed_capable(self):
        response = self._sport()
        self.assert_active(response)
        self.assertTrue(response["confirmed_bets"])

    def test_spread_active(self):
        self.assert_active(self._sport(market="spread", line=-2.5, input_stats=wnba_inputs(line=-2.5)))

    def test_total_active(self):
        self.assert_active(self._sport(market="total", selection="over", total_line=150.5, input_stats=wnba_inputs(total_line=150.5)))

    def test_team_total_active(self):
        self.assert_active(self._sport(market="team_total", selection="over", total_line=76.5, input_stats=wnba_inputs(total_line=76.5)))

    def test_first_half_active(self):
        self.assert_active(self._sport(market="first_half_moneyline"))

    def test_first_quarter_active(self):
        self.assert_active(self._sport(market="first_quarter_moneyline"))

    def test_player_points_prop_active(self):
        self.assert_active(self._sport(market="player_points", selection="over", line=20.5, input_stats=wnba_inputs(line=20.5)))

    def test_player_pra_prop_active(self):
        self.assert_active(self._sport(market="player_pra", selection="over", line=33.5, input_stats=wnba_inputs(line=33.5)))

    def test_player_threes_prop_active(self):
        self.assert_active(self._sport(market="player_threes", selection="over", line=1.5, input_stats=wnba_inputs(line=1.5)))

    def test_negative_edge_evaluated_no_bet(self):
        self.assertEqual(self._sport(odds_american=-250)["status"], "evaluated_no_bet")

    def test_edge_too_small_evaluated_no_bet(self):
        self.assertEqual(self._sport(odds_american=-160)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_no_bet(self):
        response = self._sport(market="player_points", selection="over", line=20.5, input_stats=wnba_inputs(player_minutes_projection=10, line=20.5))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_odds_stability_across_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [r["final_probability"] for r in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_provider_failure_safety(self):
        with patch("providers.odds_provider_router.enrich_ticket", side_effect=RuntimeError("boom")):
            self.assertTrue(self._screenshot()["ok"])

    def test_officiating_only_safety_cannot_create_bets(self):
        response = self._sport(input_stats={"referee_name": "Ref A"})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_social_crowd_only_safety_cannot_create_bets(self):
        response = self._sport(input_stats={"social_sentiment": 90, "crowd_consensus": 80})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_screenshot_analysis_alias_path(self):
        response = self._screenshot()
        self.assertEqual(response["model_analysis"]["model_status"], "active")
        self.assertEqual(response["model_analysis"]["missing_inputs_after_normalization"], [])

    def test_confirmed_no_bet_same_selection_mutual_exclusion(self):
        response = self._sport()
        confirmed = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["confirmed_bets"]}
        no_bets = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_logbook_rows_include_required_fields(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake"):
            self.assertIn(field, row)

    def test_direct_versus_screenshot_normalization_parity(self):
        direct = self._sport()
        screenshot = self._screenshot()["model_analysis"]
        self.assertEqual(direct["model_status"], "active")
        self.assertEqual(screenshot["model_status"], "active")


if __name__ == "__main__":
    unittest.main()
