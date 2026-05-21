import asyncio
import unittest
from copy import deepcopy
from unittest.mock import patch

from main import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def cfb_inputs(**extra):
    data = {
        "home_team": "Ohio State", "away_team": "Michigan", "team": "Ohio State", "opponent": "Michigan",
        "home_offensive_epa_per_play": 0.23, "away_offensive_epa_per_play": 0.15,
        "home_defensive_epa_per_play": -0.08, "away_defensive_epa_per_play": -0.02,
        "home_success_rate": 0.49, "away_success_rate": 0.44,
        "home_defensive_success_rate_allowed": 0.37, "away_defensive_success_rate_allowed": 0.41,
        "home_explosiveness": 0.18, "away_explosiveness": 0.14,
        "home_explosiveness_allowed": 0.10, "away_explosiveness_allowed": 0.13,
        "home_pace_seconds_per_play": 25.4, "away_pace_seconds_per_play": 27.6,
        "home_plays_per_game": 73, "away_plays_per_game": 69,
        "home_points_per_drive": 2.95, "away_points_per_drive": 2.45,
        "home_points_allowed_per_drive": 1.55, "away_points_allowed_per_drive": 1.92,
        "home_red_zone_td_rate": 0.68, "away_red_zone_td_rate": 0.58,
        "home_red_zone_td_rate_allowed": 0.44, "away_red_zone_td_rate_allowed": 0.52,
        "home_turnover_margin": 0.6, "away_turnover_margin": 0.1,
        "home_havoc_rate": 19.0, "away_havoc_rate": 16.0,
        "home_havoc_allowed": 12.0, "away_havoc_allowed": 15.0,
        "home_qb_rating": 88.0, "away_qb_rating": 79.0,
        "home_qb_injury_adjustment": 0.0, "away_qb_injury_adjustment": -0.5,
        "home_offensive_line_rating": 86.0, "away_offensive_line_rating": 78.0,
        "home_defensive_line_rating": 88.0, "away_defensive_line_rating": 80.0,
        "home_special_teams_rating": 74.0, "away_special_teams_rating": 70.0,
        "home_field_advantage": 3.0, "neutral_site": False, "weather_wind_mph": 6,
        "weather_precipitation": "none", "home_rest_days": 7, "away_rest_days": 6,
        "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.6,
        "home_strength_of_schedule": 8.6, "away_strength_of_schedule": 8.1,
        "home_rank": 2, "away_rank": 8, "home_power_rating": 29.5,
        "away_power_rating": 21.0, "home_conference_strength": 9.0,
        "away_conference_strength": 8.4, "book_count": 8,
        "player": "Marvin Harrison Jr.", "player_team": "Ohio State", "player_position": "WR",
        "player_snap_share": 0.86, "player_usage_rate": 0.28,
        "player_pass_attempts_projection": 34, "player_passing_yards_projection": 285,
        "player_passing_tds_projection": 2.4, "player_interceptions_projection": 0.6,
        "player_rush_attempts_projection": 9, "player_rushing_yards_projection": 52,
        "player_rushing_tds_projection": 0.6, "player_targets_projection": 11,
        "player_receptions_projection": 7.2, "player_receiving_yards_projection": 96,
        "player_anytime_td_probability": 0.48, "line": 80.5,
    }
    data.update(extra)
    return data


def alias_inputs(**extra):
    data = {
        "game": "Ohio State vs Michigan", "home": "Ohio State", "away": "Michigan",
        "team_name": "Ohio State", "opponent_name": "Michigan", "favorite": "Ohio State",
        "home_epa_off": 0.23, "away_epa_off": 0.15, "home_epa_def": -0.08, "away_epa_def": -0.02,
        "home_sr": 0.49, "away_sr": 0.44, "home_def_sr_allowed": 0.37, "away_def_sr_allowed": 0.41,
        "home_explosive_rate": 0.18, "away_explosive_rate": 0.14,
        "home_explosive_allowed": 0.10, "away_explosive_allowed": 0.13,
        "home_pace": 25.4, "away_pace": 27.6, "home_plays_per_game": 73, "away_plays_per_game": 69,
        "home_ppd": 2.95, "away_ppd": 2.45, "home_ppd_allowed": 1.55, "away_ppd_allowed": 1.92,
        "home_rz_td": 0.68, "away_rz_td": 0.58, "home_rz_td_allowed": 0.44, "away_rz_td_allowed": 0.52,
        "home_turnover_margin": 0.6, "away_turnover_margin": 0.1, "home_havoc_rate": 19.0,
        "away_havoc_rate": 16.0, "home_havoc_allowed": 12.0, "away_havoc_allowed": 15.0,
        "home_qb": 88.0, "away_qb": 79.0, "home_qb_injury": 0.0, "away_qb_injury": -0.5,
        "home_ol": 86.0, "away_ol": 78.0, "home_dl": 88.0, "away_dl": 80.0,
        "home_st": 74.0, "away_st": 70.0, "home_field_advantage": 3.0,
        "neutral_site": False, "wind_mph": 6, "precipitation": "none", "home_rest_days": 7,
        "away_rest_days": 6, "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.6,
        "home_strength_of_schedule": 8.6, "away_strength_of_schedule": 8.1,
        "home_ap_rank": 2, "away_ap_rank": 8, "home_sp_rating": 29.5,
        "away_sp_rating": 21.0, "home_conference_rating": 9.0, "away_conference_rating": 8.4,
        "book_count": 8,
    }
    data.update(extra)
    return data


def payload(**extra):
    data = {
        "sport": "ncaaf", "league": "NCAAF", "event_id": "Ohio State vs Michigan",
        "market": "moneyline", "selection": "Ohio State", "odds_american": 100,
        "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate", "input_stats": cfb_inputs(),
    }
    data.update(extra)
    return data


class TestCollegeFootballModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed", "sport": "ncaaf", "league": "NCAAF",
            "event": "Ohio State vs Michigan", "teams": ["Michigan", "Ohio State"],
            "market": "moneyline", "selection": "Ohio State", "odds_american": 100,
            "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
            "screenshot_text": "Ohio State moneyline +100 vs Michigan", "input_stats": alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], "college_football_epa_drive_rating_monte_carlo_model")
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "ncaaf")
        self.assertIsNotNone(response["final_probability"])

    def test_missing_input_safety(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["partial_model_mode"])

    def test_bad_text_input_safety(self):
        for bad in (None, "ticket text"):
            response = self._sport(input_stats=bad)
            self.assertEqual(response["confirmed_bets"], [])
            self.assertEqual(response["suggested_stake"], 0)
        response = self._sport(odds_american="bad")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_moneyline_confirmed_capable(self): self.assertTrue(self._sport()["confirmed_bets"])
    def test_spread_active(self): self.assert_active(self._sport(market="spread", line=-3.5, input_stats=cfb_inputs(line=-3.5)))
    def test_total_active(self): self.assert_active(self._sport(market="total", selection="over", total_line=55.5, input_stats=cfb_inputs(total_line=55.5)))
    def test_team_total_active(self): self.assert_active(self._sport(market="team_total", selection="over", total_line=28.5, input_stats=cfb_inputs(total_line=28.5)))
    def test_first_half_active(self): self.assert_active(self._sport(market="first_half_moneyline"))
    def test_first_quarter_active(self): self.assert_active(self._sport(market="first_quarter_moneyline"))
    def test_player_passing_yards_prop_active(self): self.assert_active(self._sport(market="player_passing_yards", selection="over", line=260.5, input_stats=cfb_inputs(line=260.5)))
    def test_player_rushing_yards_prop_active(self): self.assert_active(self._sport(market="player_rushing_yards", selection="over", line=43.5, input_stats=cfb_inputs(line=43.5)))
    def test_player_receiving_yards_prop_active(self): self.assert_active(self._sport(market="player_receiving_yards", selection="over", line=82.5, input_stats=cfb_inputs(line=82.5)))
    def test_anytime_td_prop_active(self): self.assert_active(self._sport(market="player_anytime_td", selection="Marvin Harrison Jr.", line=0.5, input_stats=cfb_inputs(line=0.5)))
    def test_negative_edge_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-250)["status"], "evaluated_no_bet")
    def test_edge_too_small_evaluated_no_bet(self): self.assertEqual(self._sport(odds_american=-210)["status"], "evaluated_no_bet_edge_too_small")

    def test_low_confidence_no_bet(self):
        response = self._sport(market="player_passing_yards", selection="over", line=260.5, input_stats=cfb_inputs(player_snap_share=0.2, book_count=1, weather_wind_mph=25, weather_precipitation="rain", line=260.5))
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

    def test_officiating_only_safety_cannot_create_bets(self):
        response = self._sport(input_stats={"referee_crew": "Crew A"})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_social_crowd_only_safety_cannot_create_bets(self):
        response = self._sport(input_stats={"social_sentiment": 90, "crowd_consensus": 80})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_weather_only_safety_cannot_create_bets(self):
        response = self._sport(input_stats={"weather_wind_mph": 25, "weather_precipitation": "rain"})
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
        self.assertIsNotNone(direct["final_probability"])
        self.assertIsNotNone(screenshot["final_probability"])

    def test_league_calibration_label(self):
        self.assertEqual(self._sport()["league_calibration_applied"], "ncaaf")


if __name__ == "__main__":
    unittest.main()
