import unittest

from fastapi.testclient import TestClient

from automation_scheduler.hockey_availability_context import evaluate_hockey_availability_context
from automation_scheduler.hockey_data_availability import evaluate_hockey_data_availability
from automation_scheduler.hockey_goalie_impact import evaluate_hockey_goalie_impact
from automation_scheduler.hockey_impact_calibration import evaluate_hockey_impact_calibration
from automation_scheduler.hockey_impact_readiness import build_hockey_impact_readiness
from automation_scheduler.hockey_impact_red_team import evaluate_hockey_impact_red_team
from automation_scheduler.hockey_impact_report import build_hockey_impact_diagnostics
from automation_scheduler.hockey_incentive_context import evaluate_hockey_incentive_context
from automation_scheduler.hockey_line_pair_context import evaluate_hockey_line_pair_context
from automation_scheduler.hockey_market_relevance import evaluate_hockey_market_relevance
from automation_scheduler.hockey_matchup_context import evaluate_hockey_matchup_context
from automation_scheduler.hockey_possession_impact import evaluate_hockey_possession_impact
from automation_scheduler.hockey_skater_impact import evaluate_hockey_skater_impact
from automation_scheduler.hockey_special_teams_context import evaluate_hockey_special_teams_context
from automation_scheduler.hockey_transition_context import evaluate_hockey_transition_context
from automation_scheduler.response_compactor import compact_hockey_impact_diagnostics_response, redact_and_limit_payload
from tests.support.action_imports import app


def _team_context(**extra):
    row = {
        "team": "sample_home",
        "opponent": "sample_away",
        "goals_for_per_game": 3.2,
        "goals_against_per_game": 2.8,
        "shots_for_per_game": 32.4,
        "shots_against_per_game": 29.2,
        "shot_attempts_for_per_game": 61.0,
        "shot_attempts_against_per_game": 54.0,
        "unblocked_attempts_for_per_game": 45.0,
        "unblocked_attempts_against_per_game": 39.0,
        "shot_share": 0.53,
        "expected_goals_for_per_game": 3.35,
        "expected_goals_against_per_game": 2.62,
        "xg_share": 0.56,
        "high_danger_chances_for": 12.0,
        "high_danger_chances_against": 8.0,
        "high_danger_xg_for": 1.22,
        "high_danger_xg_against": 0.74,
        "rush_chances_for": 6.0,
        "rush_chances_against": 3.0,
        "rebound_chances_for": 4.0,
        "rebound_chances_against": 2.0,
        "slot_shots_for": 8.0,
        "first_period_shot_rate": 11.0,
        "first_period_xg_rate": 0.84,
        "pace_proxy": 62.0,
        "games_sample_size": 30,
    }
    row.update(extra)
    return row


def _skater_context(**extra):
    row = {
        "role": "WINGER",
        "individual_expected_goals": 0.42,
        "individual_shot_attempts": 7.2,
        "shots_on_goal_rate": 3.4,
        "high_danger_attempt_rate": 1.1,
        "primary_points_rate": 0.8,
        "individual_assists_rate": 0.45,
        "primary_shot_assist_rate": 1.4,
        "power_play_time_on_ice": 2.8,
        "even_strength_time_on_ice": 14.0,
        "line_xg_share": 0.54,
        "shot_volume_stability": 0.74,
    }
    row.update(extra)
    return row


def _goalie_context(**extra):
    row = {
        "confirmed_starter": True,
        "save_percentage": 0.914,
        "recent_save_percentage": 0.918,
        "expected_goals_against": 2.7,
        "goals_saved_above_expected_proxy": 8.5,
        "high_danger_save_percentage": 0.835,
        "rebound_control_proxy": 0.66,
        "workload_recent_starts": 4,
        "shots_faced_recent": 31,
        "rest_days": 2,
        "team_defensive_xg_against": 2.7,
        "team_high_danger_against": 8.0,
        "opponent_shot_volume": 32,
        "opponent_xg": 3.1,
    }
    row.update(extra)
    return row


def _line_context(**extra):
    row = {
        "confirmed_lines": True,
        "confirmed_pairs": True,
        "line_xg_share": 0.55,
        "line_shot_share": 0.54,
        "line_high_danger_share": 0.56,
        "line_time_on_ice": 13.5,
        "line_continuity": 0.8,
        "defensive_pair_xg_share": 0.53,
        "defensive_pair_shot_share": 0.52,
        "defensive_pair_time_on_ice": 20.0,
        "defensive_pair_continuity": 0.76,
        "home_last_change": True,
    }
    row.update(extra)
    return row


def _special_context(**extra):
    row = {
        "power_play_percentage": 0.24,
        "penalty_kill_percentage": 0.82,
        "power_play_xg_rate": 0.82,
        "penalty_kill_xg_against_rate": 0.54,
        "power_play_shot_rate": 6.8,
        "penalty_kill_shot_against_rate": 4.8,
        "opponent_penalty_rate": 3.4,
        "power_play_unit_role": 1.0,
        "special_teams_time_on_ice": 3.4,
    }
    row.update(extra)
    return row


def _transition_context(**extra):
    row = {
        "controlled_entry_rate": 0.48,
        "controlled_entry_success_rate": 0.62,
        "controlled_exit_rate": 0.55,
        "failed_exit_rate": 0.12,
        "rush_chances_for": 6.0,
        "rush_chances_against": 3.0,
        "odd_man_rushes_for": 2.0,
        "forecheck_pressure_rate": 0.52,
        "puck_retrieval_rate": 0.58,
        "neutral_zone_turnover_rate": 0.08,
    }
    row.update(extra)
    return row


def _availability_context(**extra):
    row = {
        "skater_injury_status": "healthy",
        "goalie_injury_status": "healthy",
        "confirmed_goalie": True,
        "confirmed_lines": True,
        "rest_days": 2,
        "back_to_back": False,
        "three_in_four": False,
    }
    row.update(extra)
    return row


class TestHockeyDataAvailability(unittest.TestCase):
    def test_001_nhl_tier_0_returns_data_insufficient(self):
        result = evaluate_hockey_data_availability("icehockey_nhl")
        self.assertEqual(result["data_tier"], 0)
        self.assertEqual(result["status"], "DATA_INSUFFICIENT")

    def test_002_missing_tracking_data_does_not_fail(self):
        result = evaluate_hockey_data_availability("icehockey_nhl", team_context={"team": "A", "shots_for_per_game": 31})
        self.assertFalse(result["tracking_level_allowed"])
        self.assertTrue(result["tracking_not_required"])

    def test_003_missing_zone_entry_exit_data_does_not_fail(self):
        result = build_hockey_impact_diagnostics(team_context=_team_context(), calibration_context={"matched_outcomes_count": 0})
        self.assertFalse(result["tracking_level_allowed"])
        self.assertFalse(result["transition_context"]["zone_entry_fabricated"])

    def test_004_missing_goalie_gsax_does_not_fail(self):
        result = evaluate_hockey_goalie_impact({"confirmed_starter": True, "save_percentage": 0.912}, goalie_level_allowed=True)
        self.assertFalse(result["gsax_fabricated"])
        self.assertIn("gsax_missing_not_inferred_from_save_percentage", result["no_bet_reasons"])

    def test_005_missing_line_combinations_does_not_fail(self):
        result = evaluate_hockey_line_pair_context({})
        self.assertFalse(result["line_role_fabricated"])
        self.assertIn("confirmed_lines_missing_caps_skater_props", result["no_bet_reasons"])

    def test_006_tier_1_basic_data_caps_confidence(self):
        result = evaluate_hockey_data_availability("icehockey_nhl", game_context={"team": "A", "opponent": "B"})
        self.assertEqual(result["data_tier"], 1)
        self.assertLessEqual(result["confidence_cap"], 42.0)

    def test_007_tier_2_shot_possession_data_enables_limited_diagnostics(self):
        result = evaluate_hockey_data_availability("icehockey_nhl", team_context={"shots_for_per_game": 32, "shot_attempts_for_per_game": 60})
        self.assertEqual(result["data_tier"], 2)
        self.assertTrue(result["team_level_allowed"])

    def test_008_tier_3_xg_line_goalie_data_enables_stronger_diagnostics(self):
        result = evaluate_hockey_data_availability("icehockey_nhl", team_context={"expected_goals_for_per_game": 3.1}, line_context={"line_xg_share": 0.55}, goalie_context={"goals_saved_above_expected_proxy": 6})
        self.assertEqual(result["data_tier"], 3)
        self.assertTrue(result["goalie_level_allowed"])

    def test_009_tier_4_tracking_transition_is_optional(self):
        result = evaluate_hockey_data_availability("icehockey_nhl", transition_context={"controlled_entry_rate": 0.5})
        self.assertEqual(result["data_tier"], 4)

    def test_010_missing_skater_context_still_allows_team_diagnostics(self):
        result = build_hockey_impact_diagnostics(market_type="total", team_context=_team_context())
        self.assertTrue(result["team_level_allowed"])
        self.assertFalse(result["skater_level_allowed"])

    def test_011_missing_goalie_context_caps_but_does_not_500(self):
        result = build_hockey_impact_diagnostics(market_type="moneyline", team_context=_team_context())
        self.assertEqual(result["goalie_impact"]["goalie_impact_score"], 0.0)
        self.assertIn("missing_goalie_context_caps_goalie_team_markets", result["goalie_impact"]["no_bet_reasons"])


class TestHockeyPossessionXg(unittest.TestCase):
    def test_012_shot_volume_affects_team_scoring(self):
        low = evaluate_hockey_possession_impact(_team_context(shots_for_per_game=24, shots_against_per_game=35))
        high = evaluate_hockey_possession_impact(_team_context(shots_for_per_game=36, shots_against_per_game=24))
        self.assertGreater(high["shot_volume_score"], low["shot_volume_score"])

    def test_013_shot_attempts_affect_possession_score(self):
        low = evaluate_hockey_possession_impact(_team_context(shot_attempts_for_per_game=44, shot_attempts_against_per_game=68, xg_share=0.45))
        high = evaluate_hockey_possession_impact(_team_context(shot_attempts_for_per_game=70, shot_attempts_against_per_game=44, xg_share=0.59))
        self.assertGreater(high["possession_score"], low["possession_score"])

    def test_014_expected_goals_affect_quality_score_where_present(self):
        low = evaluate_hockey_possession_impact(_team_context(expected_goals_for_per_game=2.1, expected_goals_against_per_game=3.6))
        high = evaluate_hockey_possession_impact(_team_context(expected_goals_for_per_game=3.8, expected_goals_against_per_game=2.0))
        self.assertGreater(high["xg_quality_score"], low["xg_quality_score"])

    def test_015_missing_xg_uses_limited_proxy_only(self):
        row = {"goals_for_per_game": 3.3, "goals_against_per_game": 2.8, "shots_for_per_game": 32, "shots_against_per_game": 30}
        result = evaluate_hockey_possession_impact(row, data_tier=1)
        self.assertTrue(result["limited_proxy"])
        self.assertFalse(result["xg_fabricated"])

    def test_016_high_danger_chances_affect_total_team_total_relevance(self):
        low = evaluate_hockey_possession_impact(_team_context(high_danger_chances_for=6, high_danger_xg_for=0.4))
        high = evaluate_hockey_possession_impact(_team_context(high_danger_chances_for=17, high_danger_xg_for=1.7))
        self.assertGreater(high["high_danger_score"], low["high_danger_score"])

    def test_017_rush_rebound_slot_context_modifies_relevance(self):
        result = evaluate_hockey_possession_impact(_team_context(rush_chances_for=8, rebound_chances_for=7, slot_shots_for=12))
        self.assertGreater(result["rush_rebound_score"], 50)

    def test_018_first_period_data_affects_first_period_markets(self):
        result = evaluate_hockey_possession_impact(_team_context(first_period_shot_rate=14, first_period_xg_rate=1.2), market_type="first_period_total")
        self.assertGreater(result["first_period_pressure_score"], 60)

    def test_019_small_sample_flags_insufficient_sample(self):
        result = evaluate_hockey_possession_impact(_team_context(games_sample_size=4))
        self.assertTrue(result["insufficient_sample"])


class TestHockeySkaterGoalieLineSpecialTransition(unittest.TestCase):
    def test_020_skater_shot_generation_affects_sog_relevance(self):
        result = evaluate_hockey_skater_impact(_skater_context(), skater_level_allowed=True, data_tier=3)
        self.assertGreater(result["shot_generation_score"], 50)

    def test_021_individual_xg_affects_goal_relevance_where_supplied(self):
        low = evaluate_hockey_skater_impact(_skater_context(individual_expected_goals=0.08), skater_level_allowed=True)
        high = evaluate_hockey_skater_impact(_skater_context(individual_expected_goals=0.7), skater_level_allowed=True)
        self.assertGreater(high["scoring_quality_score"], low["scoring_quality_score"])

    def test_022_playmaking_metrics_affect_assist_point_relevance(self):
        result = evaluate_hockey_skater_impact(_skater_context(primary_shot_assist_rate=2.5, individual_assists_rate=1.0), skater_level_allowed=True)
        self.assertGreater(result["playmaking_score"], 60)

    def test_023_power_play_role_affects_ppp_relevance(self):
        result = evaluate_hockey_skater_impact(_skater_context(power_play_time_on_ice=4.5), skater_level_allowed=True)
        self.assertGreater(result["special_teams_role_score"], 60)

    def test_024_defensive_role_affects_blocked_shot_relevance(self):
        result = evaluate_hockey_skater_impact({"role": "DEFENSEMAN", "blocked_shots_rate": 3.2, "defensive_zone_start_rate": 0.62, "penalty_kill_time_on_ice": 2.8}, skater_level_allowed=True)
        self.assertGreater(result["blocked_shot_relevance_score"], 60)

    def test_025_missing_individual_xg_does_not_fabricate_it(self):
        result = evaluate_hockey_skater_impact({"role": "WINGER", "shots_on_goal_rate": 3.0}, skater_level_allowed=True)
        self.assertFalse(result["individual_xg_fabricated"])
        self.assertIn("individual_xg_missing_not_fabricated", result["no_bet_reasons"])

    def test_026_missing_line_role_caps_player_prop_confidence(self):
        result = evaluate_hockey_skater_impact({"role": "WINGER", "individual_expected_goals": 0.3}, skater_level_allowed=True)
        self.assertIn("line_role_unconfirmed_caps_player_props", result["no_bet_reasons"])

    def test_027_shooting_percentage_regression_is_caution_only(self):
        result = evaluate_hockey_skater_impact(_skater_context(shooting_percentage_recent=0.24, shooting_percentage_career_proxy=0.10), skater_level_allowed=True)
        self.assertTrue(result["shooting_percentage_regression_caution"])
        self.assertIn("shooting_percentage_regression_caution", result["no_bet_reasons"])

    def test_028_confirmed_goalie_raises_goalie_certainty(self):
        result = evaluate_hockey_goalie_impact(_goalie_context(), goalie_level_allowed=True)
        self.assertGreaterEqual(result["starter_certainty_score"], 90)

    def test_029_unconfirmed_goalie_caps_market_confidence(self):
        result = evaluate_hockey_goalie_impact(_goalie_context(confirmed_starter=False), goalie_level_allowed=True)
        self.assertIn("goalie_starter_unconfirmed_caps_goalie_team_total_markets", result["no_bet_reasons"])

    def test_030_missing_gsax_does_not_fabricate_gsax(self):
        result = evaluate_hockey_goalie_impact(_goalie_context(goals_saved_above_expected_proxy=None), goalie_level_allowed=True)
        self.assertFalse(result["gsax_fabricated"])

    def test_031_recent_save_percentage_is_treated_as_volatile(self):
        result = evaluate_hockey_goalie_impact({"confirmed_starter": True, "recent_save_percentage": 0.940, "save_percentage": 0.912}, goalie_level_allowed=True)
        self.assertIn("recent_save_percentage_volatile_without_shot_quality_adjustment", result["no_bet_reasons"])

    def test_032_back_to_back_goalie_start_creates_fatigue_warning(self):
        result = evaluate_hockey_goalie_impact(_goalie_context(back_to_back_start=True), goalie_level_allowed=True)
        self.assertIn("back_to_back_goalie_start_fatigue_warning", result["no_bet_reasons"])

    def test_033_high_danger_save_context_works_where_supplied(self):
        result = evaluate_hockey_goalie_impact(_goalie_context(high_danger_save_percentage=0.87), goalie_level_allowed=True)
        self.assertGreater(result["high_danger_resilience_score"], 60)

    def test_034_goalie_injury_uncertainty_creates_hard_warning(self):
        result = evaluate_hockey_goalie_impact(_goalie_context(goalie_injury_status="questionable"), goalie_level_allowed=True)
        self.assertIn("goalie_injury_uncertainty_hard_warning", result["no_bet_reasons"])

    def test_035_confirmed_lines_raise_lineup_confidence(self):
        result = evaluate_hockey_line_pair_context(_line_context(confirmed_lines=True))
        self.assertGreater(result["line_stability_score"], 60)

    def test_036_unconfirmed_lines_cap_skater_prop_confidence(self):
        result = evaluate_hockey_line_pair_context(_line_context(confirmed_lines=False))
        self.assertIn("confirmed_lines_missing_caps_skater_props", result["no_bet_reasons"])

    def test_037_line_xg_share_works_where_supplied(self):
        result = evaluate_hockey_line_pair_context(_line_context(line_xg_share=0.60))
        self.assertGreater(result["line_quality_score"], 55)

    def test_038_defensive_pair_xg_share_works_where_supplied(self):
        result = evaluate_hockey_line_pair_context(_line_context(defensive_pair_xg_share=0.58))
        self.assertGreater(result["pair_quality_score"], 55)

    def test_039_pair_instability_affects_defensive_goalie_confidence(self):
        stable = evaluate_hockey_line_pair_context(_line_context(defensive_pair_continuity=0.9))
        unstable = evaluate_hockey_line_pair_context(_line_context(defensive_pair_continuity=0.1))
        self.assertGreater(stable["pair_stability_score"], unstable["pair_stability_score"])

    def test_040_home_last_change_is_modifier_only(self):
        result = evaluate_hockey_line_pair_context(_line_context(home_last_change=True))
        self.assertGreater(result["last_change_context_score"], 0)

    def test_041_pp_xg_shot_rate_affects_ppp_team_total(self):
        result = evaluate_hockey_special_teams_context(_special_context(power_play_xg_rate=1.1, power_play_shot_rate=8.0))
        self.assertGreater(result["player_power_play_prop_relevance"], 50)

    def test_042_pk_xg_against_affects_opposing_pp_relevance(self):
        result = evaluate_hockey_special_teams_context(_special_context(penalty_kill_xg_against_rate=1.1))
        self.assertLess(result["penalty_kill_score"], 50)

    def test_043_penalty_rates_affect_total_special_teams_volatility(self):
        result = evaluate_hockey_special_teams_context(_special_context(opponent_penalty_rate=5.4, penalties_taken_rate=5.2))
        self.assertGreater(result["special_teams_volatility_score"], 60)

    def test_044_missing_referee_tendency_does_not_fabricate_penalty_environment(self):
        result = evaluate_hockey_special_teams_context(_special_context(referee_penalty_tendency_proxy=None))
        self.assertFalse(result["penalty_environment_fabricated"])
        self.assertIn("referee_penalty_tendency_missing_not_fabricated", result["no_bet_reasons"])

    def test_045_special_teams_volatility_lowers_confidence_when_missing_calibration(self):
        special = evaluate_hockey_special_teams_context(_special_context(opponent_penalty_rate=5.4, penalties_taken_rate=5.2))
        red = evaluate_hockey_impact_red_team(special_teams_context=special, calibration={"calibration_status": "insufficient_data"})
        self.assertIn("special_teams_volatility_overfit", red["red_team_reasons"])

    def test_046_controlled_entries_affect_transition_score(self):
        result = evaluate_hockey_transition_context(_transition_context(controlled_entry_rate=0.66))
        self.assertGreater(result["controlled_entry_score"], 60)

    def test_047_zone_exits_affect_defensive_transition_score(self):
        result = evaluate_hockey_transition_context(_transition_context(controlled_exit_rate=0.7, failed_exit_rate=0.06))
        self.assertGreater(result["zone_exit_score"], 60)

    def test_048_rush_chances_affect_total_player_relevance(self):
        result = evaluate_hockey_transition_context(_transition_context(rush_chances_for=9, odd_man_rushes_for=4))
        self.assertGreater(result["rush_attack_score"], 60)

    def test_049_forecheck_pressure_affects_matchup_context(self):
        result = evaluate_hockey_transition_context(_transition_context(forecheck_pressure_rate=0.7))
        self.assertGreater(result["forecheck_score"], 60)

    def test_050_missing_transition_caps_advanced_confidence_but_not_fail(self):
        result = evaluate_hockey_transition_context({})
        self.assertFalse(result["zone_entry_fabricated"])
        self.assertIn("transition_tracking_optional_missing_caps_advanced_confidence", result["no_bet_reasons"])


class TestHockeyMatchupAvailabilityIncentive(unittest.TestCase):
    def test_051_top_line_vs_top_pair_context_works(self):
        result = evaluate_hockey_matchup_context({**_line_context(), "matchup_deployment": 0.8})
        self.assertGreater(result["player_prop_relevance"], 45)

    def test_052_pp_vs_pk_matchup_works(self):
        result = evaluate_hockey_matchup_context({"power_play_xg_rate": 1.1, "opponent_penalty_kill_xg_against_rate": 1.0})
        self.assertIn("power_play_vs_penalty_kill_relevant", result["mismatch_reasons"])

    def test_053_rush_offense_vs_rush_defense_works(self):
        result = evaluate_hockey_matchup_context({"rush_chances_for": 9, "rush_chances_against": 2})
        self.assertIn("rush_offense_vs_rush_defense_relevant", result["mismatch_reasons"])

    def test_054_rebound_heavy_offense_vs_rebound_control_goalie_works(self):
        result = evaluate_hockey_matchup_context({"rebound_chances_for": 7, "opponent_goalie_rebound_control_proxy": 0.15, "high_danger_chances_for": 15})
        self.assertGreater(result["total_relevance"], 30)

    def test_055_high_danger_offense_vs_slot_defense_works(self):
        result = evaluate_hockey_matchup_context({"high_danger_chances_for": 16, "opponent_goalie_high_danger_save_percentage": 0.75})
        self.assertIn("high_danger_rebound_vs_goalie_context_relevant", result["mismatch_reasons"])

    def test_056_fatigue_mismatch_affects_market_relevance(self):
        result = evaluate_hockey_matchup_context({"opponent_back_to_back": True, "rest_advantage_days": 2})
        self.assertIn("rest_fatigue_mismatch_relevant", result["mismatch_reasons"])

    def test_057_conflicting_signals_lower_confidence(self):
        result = evaluate_hockey_matchup_context({"confirmed_lines": False, "confirmed_goalie": False})
        self.assertGreaterEqual(result["matchup_risk_score"], 50)

    def test_058_back_to_back_creates_fatigue_risk(self):
        result = evaluate_hockey_availability_context(_availability_context(back_to_back=True))
        self.assertIn("back_to_back_fatigue_risk", result["no_bet_reasons"])

    def test_059_three_in_four_creates_fatigue_risk(self):
        result = evaluate_hockey_availability_context(_availability_context(three_in_four=True))
        self.assertIn("three_in_four_fatigue_risk", result["no_bet_reasons"])

    def test_060_travel_time_zone_creates_risk(self):
        result = evaluate_hockey_availability_context(_availability_context(travel_distance=2400, time_zone_change=3))
        self.assertGreater(result["rest_travel_risk_score"], 30)

    def test_061_recent_overtime_shootout_creates_fatigue_modifier(self):
        result = evaluate_hockey_availability_context(_availability_context(overtime_recent=2, shootout_recent=2))
        self.assertGreater(result["fatigue_risk_score"], 20)

    def test_062_top_line_absence_affects_team_player_markets(self):
        result = evaluate_hockey_availability_context(_availability_context(top_line_absence=True))
        self.assertIn("top_line_absence_affects_team_and_player_markets", result["no_bet_reasons"])

    def test_063_top_pair_injury_affects_goalie_team_markets(self):
        result = evaluate_hockey_availability_context(_availability_context(defensive_pair_injury=True))
        self.assertIn("top_pair_or_defensive_pair_injury_affects_goalie_team_markets", result["no_bet_reasons"])

    def test_064_missing_injury_status_does_not_fabricate_health(self):
        result = evaluate_hockey_availability_context({"confirmed_goalie": True, "confirmed_lines": True})
        self.assertFalse(result["injury_status_fabricated"])

    def test_065_incentive_context_is_modifier_only(self):
        result = evaluate_hockey_incentive_context({"contract_year": True, "known_bonus_thresholds": [{"goals": 30}]})
        self.assertFalse(result["incentive_is_standalone_edge"])

    def test_066_missing_bonus_threshold_does_not_fabricate_value(self):
        result = evaluate_hockey_incentive_context({"contract_year": True})
        self.assertFalse(result["bonus_threshold_fabricated"])
        self.assertIn("bonus_threshold_unknown_not_fabricated", result["no_bet_reasons"])

    def test_067_weak_narrative_creates_overfit_risk(self):
        result = evaluate_hockey_incentive_context({"revenge_narrative_context": "unverified"})
        self.assertEqual(result["narrative_overfit_risk"], "high")

    def test_068_player_stat_incentive_raises_prop_and_reduces_team_if_misaligned(self):
        result = evaluate_hockey_incentive_context({"known_bonus_thresholds": [{"goals": 30}], "bonus_progress_context": 0.95, "playoff_elimination_status": 1.0})
        self.assertGreaterEqual(result["market_relevance_modifier"]["player_prop_relevance_adjustment"], 0)


class TestHockeyMarketCalibrationRedTeam(unittest.TestCase):
    def _market_result(self, market="moneyline"):
        return build_hockey_impact_diagnostics(
            market_type=market,
            game_context={"home_team": "A", "away_team": "B"},
            team_context=_team_context(),
            skater_context=_skater_context(),
            goalie_context=_goalie_context(),
            line_context=_line_context(),
            pair_context=_line_context(),
            special_teams_context=_special_context(),
            transition_context=_transition_context(),
            availability_context=_availability_context(),
            calibration_context={"matched_outcomes_count": 0},
        )

    def test_069_sog_relevance_links_shot_role_line_pp_suppression(self):
        result = self._market_result("player_shots_on_goal")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["player_shots_on_goal"], 50)

    def test_070_goal_relevance_links_xg_goalie_special_teams(self):
        result = self._market_result("player_goals")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["player_goals"], 35)

    def test_071_assist_point_relevance_links_playmaking_line_pp(self):
        result = self._market_result("player_assists")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["player_assists"], 40)

    def test_072_ppp_relevance_links_pp_unit_pk_penalty_environment(self):
        result = self._market_result("player_power_play_points")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["player_power_play_points"], 45)

    def test_073_blocked_shot_relevance_links_defense_role_dzone_volume(self):
        skater = evaluate_hockey_skater_impact({"role": "DEFENSEMAN", "blocked_shots_rate": 3.6, "defensive_zone_start_rate": 0.66, "penalty_kill_time_on_ice": 3.2}, skater_level_allowed=True)
        market = evaluate_hockey_market_relevance(market_type="player_blocked_shots", skater_impact=skater, line_pair_context=evaluate_hockey_line_pair_context(_line_context()), availability_context=evaluate_hockey_availability_context(_availability_context()))
        self.assertGreater(market["market_relevance_scores"]["player_blocked_shots"], 45)

    def test_074_goalie_saves_relevance_links_starter_volume_defense(self):
        result = self._market_result("goalie_saves")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["goalie_saves"], 50)

    def test_075_goalie_goals_allowed_links_opponent_xg_team_defense_goalie(self):
        result = self._market_result("goalie_goals_allowed")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["goalie_goals_allowed"], 35)

    def test_076_moneyline_puckline_links_possession_xg_goalie_special_rest(self):
        result = self._market_result("puckline")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["puckline"], 45)

    def test_077_totals_team_totals_link_pace_xg_goalie_special_fatigue(self):
        result = self._market_result("total")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["total"], 45)

    def test_078_first_period_relevance_links_first_period_shot_xg_pace(self):
        result = self._market_result("first_period_total")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["first_period_total"], 45)

    def test_079_no_labeled_outcomes_returns_insufficient_data(self):
        result = evaluate_hockey_impact_calibration({}, sport="icehockey_nhl", market_type="moneyline")
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_080_low_sample_returns_insufficient_sample(self):
        result = evaluate_hockey_impact_calibration({"matched_outcomes_count": 20}, sport="icehockey_nhl", market_type="moneyline")
        self.assertTrue(result["insufficient_sample"])

    def test_081_real_labeled_outcomes_enable_partial_calibration(self):
        result = evaluate_hockey_impact_calibration({"settled_outcomes": [{"hit": True}, {"hit": False}], "historical_predictions": [1, 2]}, sport="icehockey_nhl", market_type="moneyline")
        self.assertEqual(result["calibration_status"], "partial_calibration")
        self.assertIn("hit_rate", result)

    def test_082_roi_not_emitted_without_real_returns(self):
        result = evaluate_hockey_impact_calibration({"settled_outcomes": [{"hit": True}]}, sport="icehockey_nhl", market_type="moneyline")
        self.assertNotIn("roi_proxy", result)

    def test_083_clv_not_emitted_without_real_open_close_prices(self):
        result = evaluate_hockey_impact_calibration({"settled_outcomes": [{"hit": True}]}, sport="icehockey_nhl", market_type="moneyline")
        self.assertNotIn("clv_proxy", result)

    def test_084_slippage_not_emitted_without_real_fill_entry_data(self):
        result = evaluate_hockey_impact_calibration({"settled_outcomes": [{"hit": True}]}, sport="icehockey_nhl", market_type="moneyline")
        self.assertNotIn("slippage_proxy", result)

    def test_085_context_buckets_are_preserved(self):
        result = evaluate_hockey_impact_calibration({"matched_outcomes_count": 100, "goalie_status_bucket": "confirmed", "line_stability_bucket": "stable"}, sport="icehockey_nhl", market_type="total")
        self.assertEqual(result["calibration_buckets"]["goalie_status_bucket"], "confirmed")

    def test_086_fake_tracking_claim_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(data_availability={"tracking_level_allowed": False}, tracking_context={"player_speed": 21})
        self.assertIn("tracking_metric_missing_but_claimed", red["red_team_reasons"])

    def test_087_fake_zone_entry_exit_claim_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(data_availability={"missing_field_groups": ["zone_entry_context"]}, tracking_context={"claimed_zone_entries": True})
        self.assertIn("zone_entry_exit_missing_but_claimed", red["red_team_reasons"])

    def test_088_fake_gsax_claim_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(goalie_impact={"shot_quality_adjusted_score": 70, "missing_goalie_inputs": ["goals_saved_above_expected_proxy"]})
        self.assertIn("goalie_gsax_missing_but_claimed", red["red_team_reasons"])

    def test_089_unconfirmed_line_overconfidence_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(line_pair_context={"confirmed_lines": False}, market_relevance={"selected_market_type": "player_shots_on_goal"})
        self.assertIn("line_combination_unconfirmed_overconfidence", red["red_team_reasons"])

    def test_090_unconfirmed_goalie_overconfidence_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(goalie_impact={"starter_certainty_score": 30}, market_relevance={"selected_market_type": "moneyline"})
        self.assertIn("confirmed_goalie_missing_overconfidence", red["red_team_reasons"])

    def test_091_rest_back_to_back_overfit_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(availability_context={"fatigue_risk_score": 80})
        self.assertIn("rest_back_to_back_overfit", red["red_team_reasons"])

    def test_092_recent_save_percentage_overfit_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(goalie_impact={"no_bet_reasons": ["recent_save_percentage_volatile_without_shot_quality_adjustment"]})
        self.assertIn("recent_save_percentage_overfit", red["red_team_reasons"])

    def test_093_shooting_percentage_overfit_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(skater_impact={"shooting_percentage_regression_caution": True})
        self.assertIn("shooting_percentage_overfit", red["red_team_reasons"])

    def test_094_small_sample_xg_overfit_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(possession_impact={"insufficient_sample": True, "xg_quality_score": 70})
        self.assertIn("small_sample_xg_overfit", red["red_team_reasons"])

    def test_095_special_teams_volatility_overfit_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(special_teams_context={"special_teams_volatility_score": 70}, calibration={"calibration_status": "insufficient_data"})
        self.assertIn("special_teams_volatility_overfit", red["red_team_reasons"])

    def test_096_first_period_full_game_confusion_is_downgraded(self):
        red = evaluate_hockey_impact_red_team(data_availability={"missing_field_groups": ["first_period_context"]}, possession_impact={"total_signal_score": 70}, market_relevance={"selected_market_type": "first_period_total"})
        self.assertIn("first_period_full_game_context_confusion", red["red_team_reasons"])

    def test_097_calibration_missing_prevents_overconfident_active_review(self):
        result = self._market_result("moneyline")
        self.assertEqual(result["calibration_status"], "insufficient_data")
        self.assertNotEqual(result["recommended_review_status"], "ACTIVE_REVIEW")


class TestHockeySafetyAndEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_098_readiness_endpoint_returns_provider_write_false(self):
        response = self.client.get("/api/automation/hockey-impact-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])
        self.assertFalse(response.json()["no_spend_policy"]["new_api_keys_required"])

    def test_099_diagnostics_endpoint_returns_execution_allowed_false(self):
        response = self.client.post("/api/automation/hockey-impact-diagnostics", json={"sport": "icehockey_nhl", "market_type": "total", "team_context": _team_context()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_100_dry_run_false_is_rejected(self):
        response = self.client.post("/api/automation/hockey-impact-diagnostics", json={"sport": "icehockey_nhl", "dry_run": False})
        self.assertEqual(response.status_code, 400)

    def test_101_no_order_payload_survives_compaction(self):
        safe = redact_and_limit_payload({"order_payload": {"side": "buy"}})
        self.assertEqual(safe["order_payload"], "[omitted]")

    def test_102_no_bet_slip_survives_compaction(self):
        safe = redact_and_limit_payload({"bet_slip": {"stake": 10}, "slip_payload": {"stake": 10}})
        self.assertEqual(safe["bet_slip"], "[omitted]")
        self.assertEqual(safe["slip_payload"], "[omitted]")

    def test_103_secrets_raw_payloads_are_redacted(self):
        result = build_hockey_impact_diagnostics(team_context={"team": "A", "api_key": "sk_test_secret_value_1234567890", "raw_payload": {"x": 1}})
        self.assertFalse(result["secrets_included"])
        self.assertNotIn("sk_test_secret", str(result))

    def test_104_red_team_cannot_promote_execution(self):
        red = evaluate_hockey_impact_red_team()
        self.assertFalse(red["execution_allowed"])
        self.assertFalse(red["provider_write"])

    def test_105_health_endpoint_still_passes(self):
        response = self.client.get("/api/automation/health")
        self.assertEqual(response.status_code, 200)

    def test_106_security_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/security-readiness")
        self.assertEqual(response.status_code, 200)

    def test_107_strategy_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/strategy-readiness")
        self.assertEqual(response.status_code, 200)

    def test_108_advanced_red_team_endpoint_still_passes(self):
        response = self.client.get("/api/automation/advanced-red-team-report")
        self.assertEqual(response.status_code, 200)

    def test_109_extreme_randomness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/extreme-randomness-report")
        self.assertEqual(response.status_code, 200)

    def test_110_basketball_impact_endpoint_still_passes(self):
        response = self.client.get("/api/automation/basketball-player-impact-readiness")
        self.assertEqual(response.status_code, 200)

    def test_111_football_impact_endpoint_still_passes(self):
        response = self.client.get("/api/automation/football-impact-readiness")
        self.assertEqual(response.status_code, 200)

    def test_112_baseball_impact_endpoint_passes_if_present(self):
        response = self.client.get("/api/automation/baseball-impact-readiness")
        if response.status_code != 404:
            self.assertEqual(response.status_code, 200)

    def test_113_nhl_malformed_payload_does_not_500(self):
        response = self.client.post("/api/automation/hockey-impact-diagnostics", json={"sport": "icehockey_nhl", "team_context": "bad"})
        self.assertLess(response.status_code, 500)

    def test_114_limited_public_data_payload_returns_tier_without_fake_tracking(self):
        response = self.client.post(
            "/api/automation/hockey-impact-diagnostics",
            json={
                "sport": "icehockey_nhl",
                "market_type": "total",
                "team_context": {"goals_for_per_game": 3.2, "shots_for_per_game": 31.8, "shots_against_per_game": 30.2},
                "goalie_context": {"confirmed_starter": False, "save_percentage": 0.912},
            },
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(payload["tracking_level_allowed"])
        self.assertFalse(payload["goalie_impact"]["gsax_fabricated"])

    def test_115_compact_diagnostic_output_is_safety_locked(self):
        compact = compact_hockey_impact_diagnostics_response(build_hockey_impact_diagnostics(team_context=_team_context()))
        self.assertFalse(compact["provider_write"])
        self.assertFalse(compact["execution_allowed"])
        self.assertFalse(compact["live_execution_enabled"])
        self.assertTrue(compact["compact_response"])


if __name__ == "__main__":
    unittest.main()
