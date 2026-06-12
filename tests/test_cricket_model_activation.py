import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def cricket_inputs(**extra):
    data = {
        "team": "Mumbai Indians", "opponent": "Chennai Super Kings",
        "home_team": "Mumbai Indians", "away_team": "Chennai Super Kings",
        "batting_team": "Mumbai Indians", "bowling_team": "Chennai Super Kings",
        "format": "ipl", "venue": "Wankhede Stadium", "pitch_type": "balanced",
        "weather_conditions": "humid", "toss_winner": "Mumbai Indians", "toss_decision": "bowl",
        "team_batting_rating": 86, "opponent_batting_rating": 82,
        "team_bowling_rating": 84, "opponent_bowling_rating": 80,
        "team_fielding_rating": 82, "opponent_fielding_rating": 78,
        "team_recent_form_rating": 84, "opponent_recent_form_rating": 77,
        "team_powerplay_run_rate": 9.2, "opponent_powerplay_run_rate": 8.5,
        "team_middle_overs_run_rate": 8.4, "opponent_middle_overs_run_rate": 7.8,
        "team_death_overs_run_rate": 11.2, "opponent_death_overs_run_rate": 10.1,
        "team_wicket_loss_rate": 0.24, "opponent_wicket_loss_rate": 0.28,
        "team_wicket_taking_rate": 0.31, "opponent_wicket_taking_rate": 0.27,
        "team_boundary_rate": 0.19, "opponent_boundary_rate": 0.17,
        "team_dot_ball_rate": 0.34, "opponent_dot_ball_rate": 0.37,
        "team_chase_rating": 88, "opponent_chase_rating": 80,
        "team_defend_total_rating": 82, "opponent_defend_total_rating": 79,
        "venue_average_score": 174, "venue_chase_win_rate": 0.56,
        "pitch_spin_assist": 0.48, "pitch_pace_assist": 0.52,
        "dew_factor": 0.35, "wind_factor": 0.12, "book_count": 8,
        "player": "Rohit Sharma", "player_team": "Mumbai Indians", "player_role": "batter",
        "batting_position": 1, "player_batting_average": 31.5, "player_strike_rate": 142,
        "player_recent_runs_average": 36, "player_boundary_rate": 0.17, "player_six_rate": 0.06,
        "player_fifty_rate": 0.24, "player_hundred_rate": 0.04, "player_duck_rate": 0.08,
        "player_bowling_average": 0, "player_economy_rate": 0, "player_strike_rate_bowling": 0,
        "player_recent_wickets_average": 0, "player_overs_projection": 2.0,
        "player_balls_faced_projection": 24, "player_runs_projection": 34.5,
        "player_wickets_projection": 1.4, "player_sixes_projection": 1.6,
        "player_fours_projection": 3.2, "line": 24.5,
    }
    data.update(extra)
    return data


def cricket_alias_inputs(**extra):
    data = {
        "match": "Mumbai Indians vs Chennai Super Kings", "team_name": "Mumbai Indians",
        "opponent_name": "Chennai Super Kings", "home": "Mumbai Indians", "away": "Chennai Super Kings",
        "batting": "Mumbai Indians", "bowling": "Chennai Super Kings", "format": "ipl",
        "ground": "Wankhede Stadium", "surface": "balanced", "weather": "humid",
        "toss": "Mumbai Indians", "decision": "bowl", "team_bat_rating": 86,
        "opp_bat_rating": 82, "team_bowl_rating": 84, "opp_bowl_rating": 80,
        "team_field_rating": 82, "opp_field_rating": 78, "team_form": 84, "opp_form": 77,
        "team_pp_rr": 9.2, "opp_pp_rr": 8.5, "team_middle_rr": 8.4, "opp_middle_rr": 7.8,
        "team_death_rr": 11.2, "opp_death_rr": 10.1, "team_wicket_loss": 0.24,
        "opp_wicket_loss": 0.28, "team_wicket_rate": 0.31, "opp_wicket_rate": 0.27,
        "team_boundary_pct": 0.19, "opp_boundary_pct": 0.17, "team_dot_pct": 0.34,
        "opp_dot_pct": 0.37, "team_chase": 88, "opp_chase": 80, "team_defend": 82,
        "opp_defend": 79, "venue_avg_score": 174, "chase_win_pct": 0.56,
        "spin_assist": 0.48, "pace_assist": 0.52, "dew": 0.35, "wind": 0.12,
        "player_name": "Rohit Sharma", "player_team": "Mumbai Indians", "role": "batter",
        "bat_pos": 1, "batting_avg": 31.5, "batting_strike_rate": 142, "recent_runs": 36,
        "boundary_rate": 0.17, "six_rate": 0.06, "fifty_rate": 0.24, "hundred_rate": 0.04,
        "duck_rate": 0.08, "bowling_avg": 0, "economy": 0, "bowling_strike_rate": 0,
        "recent_wickets": 0, "overs_proj": 2.0, "balls_faced_proj": 24, "runs_proj": 34.5,
        "wickets_proj": 1.4, "sixes_proj": 1.6, "fours_proj": 3.2, "book_count": 8,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {
        "sport": "cricket", "league": "IPL", "event_id": "Mumbai Indians vs Chennai Super Kings",
        "event": "Mumbai Indians vs Chennai Super Kings", "teams": ["Mumbai Indians", "Chennai Super Kings"],
        "market": "match_winner", "selection": "Mumbai Indians", "odds_american": 100,
        "book": "Manual", "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "source_type": "unit_test", "screenshot_text": "Mumbai Indians match winner +100",
        "visible_markets": ["match_winner"], "input_stats": cricket_inputs(),
    }
    data.update(extra)
    return data


class TestCricketModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "cricket", "league": "IPL",
            "event": "Mumbai Indians vs Chennai Super Kings", "teams": ["Mumbai Indians", "Chennai Super Kings"],
            "market": "match_winner", "selection": "Mumbai Indians", "odds_american": 100,
            "book": "Manual", "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
            "screenshot_text": "Mumbai Indians match winner +100 vs Chennai Super Kings",
            "visible_markets": ["match_winner"], "input_stats": cricket_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "cricket_run_rate_wicket_resource_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "cricket")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["partial_model_mode"])

    def test_bad_text_input_safety_with_valid_envelope(self):
        response = self._sport(input_stats="bad cricket text")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertNotEqual(response["decision"], "CONFIRMED_BET")

    def test_moneyline_confirmed_capable(self):
        self.assertTrue(self._sport(market="moneyline")["confirmed_bets"])

    def test_match_winner_active(self): self.assert_active(self._sport(market="match_winner"))
    def test_total_runs_active(self): self.assert_active(self._sport(market="total_runs", selection="over", total_runs_line=330.5, input_stats=cricket_inputs(total_runs_line=330.5)))
    def test_team_total_runs_active(self): self.assert_active(self._sport(market="team_total_runs", selection="over", team_total_runs_line=160.5, input_stats=cricket_inputs(team_total_runs_line=160.5)))
    def test_first_innings_winner_active(self): self.assert_active(self._sport(market="first_innings_winner"))
    def test_first_innings_total_active(self): self.assert_active(self._sport(market="first_innings_total", selection="over", total_runs_line=164.5, input_stats=cricket_inputs(total_runs_line=164.5)))
    def test_powerplay_total_active(self): self.assert_active(self._sport(market="powerplay_total", selection="over", total_runs_line=51.5, input_stats=cricket_inputs(total_runs_line=51.5)))
    def test_top_batter_active(self): self.assert_active(self._sport(market="top_batter", selection="Rohit Sharma", line=0.5, input_stats=cricket_inputs(line=0.5)))
    def test_top_bowler_active(self): self.assert_active(self._sport(market="top_bowler", selection="Rohit Sharma", line=0.5, input_stats=cricket_inputs(line=0.5)))
    def test_player_runs_prop_active(self): self.assert_active(self._sport(market="player_runs", selection="over", line=24.5, input_stats=cricket_inputs(line=24.5)))
    def test_player_wickets_prop_active(self): self.assert_active(self._sport(market="player_wickets", selection="over", line=0.5, input_stats=cricket_inputs(line=0.5)))
    def test_player_sixes_prop_active(self): self.assert_active(self._sport(market="player_sixes", selection="over", line=0.5, input_stats=cricket_inputs(line=0.5)))
    def test_player_fours_prop_active(self): self.assert_active(self._sport(market="player_fours", selection="over", line=2.5, input_stats=cricket_inputs(line=2.5)))
    def test_negative_edge_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-400)["status"], "evaluated_no_bet")
    def test_edge_too_small_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-180)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_no_bet(self):
        response = self._sport(market="player_runs", selection="over", line=24.5, input_stats=cricket_inputs(line=24.5, player_balls_faced_projection=5, book_count=1, lineup_confirmed=False, wind_factor=0.6))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_odds_stability_across_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [r["final_probability"] for r in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_provider_failure_safety(self):
        with patch("screenshot_intake.enrich_ticket", side_effect=RuntimeError("boom")):
            self.assertTrue(self._screenshot()["ok"])

    def test_weather_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"weather": "rain", "wind": 0.6})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_toss_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"toss": "Mumbai Indians", "decision": "bowl"})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_pitch_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"surface": "spin", "spin_assist": 0.8, "pace_assist": 0.2})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_social_crowd_only_safety_cannot_create_confirmed_bet(self):
        response = self._sport(input_stats={"social_sentiment": 95, "crowd_consensus": 90})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_screenshot_analysis_alias_path(self):
        response = self._screenshot()
        analysis = response["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])

    def test_direct_versus_screenshot_normalization_parity(self):
        direct = self._sport()
        screenshot = self._screenshot()["model_analysis"]
        self.assertEqual(direct["model_status"], "active")
        self.assertEqual(screenshot["model_status"], "active")
        self.assertIsNotNone(direct["final_probability"])
        self.assertIsNotNone(screenshot["final_probability"])

    def test_confirmed_no_bet_same_selection_mutual_exclusion(self):
        response = self._sport()
        confirmed = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["confirmed_bets"]}
        no_bets = {(b.get("sport"), b.get("event"), b.get("market"), b.get("selection")) for b in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_logbook_rows_include_required_fields(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake"):
            self.assertIn(field, row)

    def test_league_calibration_label(self):
        self.assertEqual(self._sport()["league_calibration_applied"], "cricket")

    def test_format_calibration_present_for_ipl_payload(self):
        self.assertEqual(self._sport()["format_calibration_applied"], "ipl")

    def test_malformed_text_numeric_fields_cannot_activate_from_defaults(self):
        malformed = deepcopy(cricket_alias_inputs())
        for key in ("team_bat_rating", "opp_bowl_rating", "team_pp_rr", "opp_pp_rr", "venue_avg_score", "chase_win_pct"):
            malformed[key] = "bad text"
        response = self._screenshot(input_stats=malformed)
        analysis = response["model_analysis"]
        self.assertEqual(analysis["confirmed_bets"], [])
        self.assertNotEqual(analysis["decision"], "CONFIRMED_BET")
        self.assertTrue(analysis["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
