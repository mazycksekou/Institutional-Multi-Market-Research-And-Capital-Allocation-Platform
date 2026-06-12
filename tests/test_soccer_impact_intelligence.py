import unittest

from fastapi.testclient import TestClient

from automation_scheduler.response_compactor import compact_soccer_impact_diagnostics_response, redact_and_limit_payload
from automation_scheduler.soccer_data_availability import evaluate_soccer_data_availability
from automation_scheduler.soccer_goalkeeper_context import evaluate_soccer_goalkeeper_context
from automation_scheduler.soccer_impact_calibration import evaluate_soccer_impact_calibration
from automation_scheduler.soccer_impact_red_team import evaluate_soccer_impact_red_team
from automation_scheduler.soccer_impact_report import build_soccer_impact_diagnostics
from automation_scheduler.soccer_incentive_context import evaluate_soccer_incentive_context
from automation_scheduler.soccer_lineup_availability_context import evaluate_soccer_lineup_availability_context
from automation_scheduler.soccer_market_relevance import evaluate_soccer_market_relevance
from automation_scheduler.soccer_matchup_context import evaluate_soccer_matchup_context
from automation_scheduler.soccer_player_role_impact import evaluate_soccer_player_role_impact
from automation_scheduler.soccer_possession_value_impact import evaluate_soccer_possession_value_impact
from automation_scheduler.soccer_pressing_transition_context import evaluate_soccer_pressing_transition_context
from automation_scheduler.soccer_referee_context import evaluate_soccer_referee_context
from automation_scheduler.soccer_set_piece_context import evaluate_soccer_set_piece_context
from automation_scheduler.soccer_tactical_context import evaluate_soccer_tactical_context
from tests.support.action_imports import app


def _team(**extra):
    row = {
        "team": "home",
        "opponent": "away",
        "goals_for_per_game": 1.7,
        "goals_against_per_game": 1.1,
        "shots_for_per_game": 14.2,
        "shots_against_per_game": 9.8,
        "shots_on_target_for": 5.1,
        "shots_on_target_against": 3.2,
        "xg_for": 1.72,
        "xg_against": 1.08,
        "non_penalty_xg_for": 1.48,
        "non_penalty_xg_against": 0.94,
        "xg_per_shot": 0.12,
        "big_chances_for": 2.6,
        "big_chances_against": 1.1,
        "box_entries_for": 24,
        "box_entries_against": 15,
        "penalty_area_touches_for": 24,
        "field_tilt": 0.58,
        "possession_share": 0.55,
        "final_third_entries": 48,
        "passes_into_final_third": 52,
        "passes_into_penalty_area": 12,
        "progressive_passes": 58,
        "progressive_carries": 22,
        "expected_threat_for": 1.45,
        "expected_threat_against": 0.82,
        "possession_value_for": 1.3,
        "possession_value_against": 0.8,
        "vaep_for": 1.2,
        "vaep_against": 0.7,
        "counterattack_xg": 0.31,
        "set_piece_xg_for": 0.28,
        "set_piece_xg_against": 0.16,
        "first_half_xg_for": 0.82,
        "first_half_xg_against": 0.45,
        "matches_sample_size": 28,
    }
    row.update(extra)
    return row


def _tactical(**extra):
    row = {
        "formation": "4-3-3",
        "high_press_rate": 0.62,
        "pressure_intensity": 0.64,
        "ppda_proxy": 8.4,
        "counter_pressing_rate": 0.58,
        "defensive_line_height": 0.57,
        "directness_score": 0.44,
        "compactness_proxy": 0.66,
        "central_progression_rate": 0.55,
        "wide_progression_rate": 0.52,
        "rest_defense_structure": 0.68,
    }
    row.update(extra)
    return row


def _press(**extra):
    row = {
        "pressures": 155,
        "successful_pressures": 54,
        "pressures_final_third": 28,
        "high_turnovers": 8,
        "counterpress_regains": 11,
        "pressure_regain_time": 5.0,
        "ppda_proxy": 8.5,
        "counterattack_xg": 0.31,
        "transition_xg_for": 0.42,
        "transition_xg_against": 0.22,
        "transition_shots_against": 2,
        "rest_defense_quality": 0.72,
    }
    row.update(extra)
    return row


def _player(**extra):
    row = {
        "role": "FORWARD",
        "non_penalty_xg": 0.42,
        "shots": 3.4,
        "shots_on_target": 1.3,
        "touches_in_box": 6.1,
        "carries_into_box": 2.1,
        "expected_assists": 0.18,
        "key_passes": 1.4,
        "xT_created": 0.28,
        "progressive_passes": 3.0,
        "minutes_projection": 82,
        "substitution_risk": 0.18,
        "role_security": 0.78,
        "penalty_taker_status": "unknown",
        "set_piece_taker_status": "unknown",
    }
    row.update(extra)
    return row


def _lineup(**extra):
    row = {
        "confirmed_lineup": True,
        "projected_lineup": True,
        "starting_xi_stability": 0.72,
        "starting_goalkeeper_confirmed": True,
        "minutes_projection": 82,
        "substitution_risk": 0.18,
        "rotation_risk": 0.18,
        "days_rest": 6,
    }
    row.update(extra)
    return row


def _keeper(**extra):
    row = {
        "confirmed_starter": True,
        "save_percentage": 0.713,
        "post_shot_xg_allowed": 1.1,
        "goals_prevented_proxy": 3.5,
        "high_claim_rate": 0.62,
        "cross_claim_rate": 0.58,
        "sweep_actions": 1.8,
        "distribution_accuracy": 0.78,
        "long_pass_accuracy": 0.42,
        "opponent_xg": 1.35,
        "opponent_shot_volume": 12.0,
    }
    row.update(extra)
    return row


def _setpiece(**extra):
    row = {
        "set_piece_xg_for": 0.28,
        "set_piece_xg_against": 0.16,
        "corner_rate_for": 5.8,
        "corner_rate_against": 3.6,
        "penalty_rate_for": 0.18,
        "penalty_rate_against": 0.09,
        "aerial_duel_strength": 0.62,
        "set_piece_taker_status": "confirmed",
        "penalty_taker_status": "confirmed",
        "opponent_set_piece_defense": 0.42,
        "referee_penalty_rate": 0.18,
    }
    row.update(extra)
    return row


def _ref(**extra):
    row = {
        "referee_name": "sample_ref",
        "card_rate": 4.8,
        "yellow_card_rate": 4.5,
        "red_card_rate": 0.18,
        "foul_rate": 25,
        "penalty_rate": 0.18,
        "team_foul_rate": 12,
        "player_card_risk": 0.38,
    }
    row.update(extra)
    return row


class TestSoccerDataAvailability(unittest.TestCase):
    def test_001_soccer_tier_0_returns_data_insufficient(self):
        result = evaluate_soccer_data_availability("soccer")
        self.assertEqual(result["data_tier"], 0)
        self.assertEqual(result["status"], "DATA_INSUFFICIENT")

    def test_002_missing_tracking_data_does_not_fail(self):
        result = evaluate_soccer_data_availability("soccer", team_context={"team": "A", "shots_for_per_game": 12})
        self.assertFalse(result["tracking_level_allowed"])
        self.assertTrue(result["tracking_not_required"])

    def test_003_missing_xt_does_not_fail(self):
        result = build_soccer_impact_diagnostics(team_context={"team": "A", "xg_for": 1.2})
        self.assertFalse(result["possession_value_impact"]["xt_fabricated"])

    def test_004_missing_obv_vaep_does_not_fail(self):
        result = build_soccer_impact_diagnostics(team_context={"team": "A", "xg_for": 1.2})
        self.assertFalse(result["possession_value_impact"]["obv_vaep_fabricated"])

    def test_005_missing_formation_does_not_fail(self):
        result = evaluate_soccer_tactical_context({})
        self.assertFalse(result["formation_fabricated"])

    def test_006_missing_confirmed_lineup_caps_confidence(self):
        result = evaluate_soccer_data_availability("soccer", lineup_context={"projected_lineup": True})
        self.assertLessEqual(result["confidence_cap"], 66)

    def test_007_missing_goalkeeper_confirmation_caps_confidence(self):
        result = evaluate_soccer_data_availability("soccer", goalkeeper_context={"save_percentage": 0.72})
        self.assertLessEqual(result["confidence_cap"], 68)

    def test_008_missing_referee_context_does_not_fail(self):
        result = evaluate_soccer_referee_context({})
        self.assertFalse(result["referee_tendency_fabricated"])

    def test_009_tier_1_basic_data_caps_confidence(self):
        result = evaluate_soccer_data_availability("football", game_context={"team": "A", "opponent": "B"})
        self.assertEqual(result["data_tier"], 1)
        self.assertLessEqual(result["confidence_cap"], 42)

    def test_010_tier_2_xg_shot_data_enables_limited_diagnostics(self):
        result = evaluate_soccer_data_availability("association_football", team_context={"xg_for": 1.5, "shots_for_per_game": 12})
        self.assertEqual(result["data_tier"], 2)

    def test_011_tier_3_possession_value_player_role_enables_stronger_diagnostics(self):
        result = evaluate_soccer_data_availability("soccer", possession_value_context={"expected_threat_for": 1.2}, player_context={"role": "FORWARD", "minutes_projection": 80})
        self.assertEqual(result["data_tier"], 3)
        self.assertTrue(result["player_level_allowed"])

    def test_012_tier_4_tracking_optional(self):
        result = evaluate_soccer_data_availability("soccer", tracking_context={"pitch_control": 0.55})
        self.assertEqual(result["data_tier"], 4)

    def test_013_missing_player_context_allows_team_diagnostics(self):
        result = build_soccer_impact_diagnostics(team_context=_team())
        self.assertTrue(result["team_level_allowed"])
        self.assertFalse(result["player_level_allowed"])


class TestSoccerPossessionChanceQuality(unittest.TestCase):
    def test_014_xg_affects_chance_quality_score(self):
        low = evaluate_soccer_possession_value_impact(_team(xg_for=0.6, xg_against=2.2))
        high = evaluate_soccer_possession_value_impact(_team(xg_for=2.4, xg_against=0.7))
        self.assertGreater(high["chance_quality_score"], low["chance_quality_score"])

    def test_015_non_penalty_xg_separates_open_play(self):
        result = evaluate_soccer_possession_value_impact(_team(non_penalty_xg_for=2.2, set_piece_xg_for=0.0))
        self.assertGreater(result["open_play_attack_score"], 50)

    def test_016_xg_per_shot_affects_chance_quality(self):
        low = evaluate_soccer_possession_value_impact(_team(xg_per_shot=0.05))
        high = evaluate_soccer_possession_value_impact(_team(xg_per_shot=0.17))
        self.assertGreater(high["xg_quality_score"], low["xg_quality_score"])

    def test_017_big_chances_affect_totals(self):
        high = evaluate_soccer_possession_value_impact(_team(big_chances_for=5))
        self.assertGreater(high["total_signal_score"], 45)

    def test_018_field_tilt_affects_territorial_dominance(self):
        low = evaluate_soccer_possession_value_impact(_team(field_tilt=0.44))
        high = evaluate_soccer_possession_value_impact(_team(field_tilt=0.64))
        self.assertGreater(high["territorial_dominance_score"], low["territorial_dominance_score"])

    def test_019_progressive_actions_affect_progression(self):
        result = evaluate_soccer_possession_value_impact(_team(progressive_passes=80, progressive_carries=35))
        self.assertGreater(result["progression_score"], 60)

    def test_020_xt_affects_possession_value(self):
        low = evaluate_soccer_possession_value_impact(_team(expected_threat_for=0.3))
        high = evaluate_soccer_possession_value_impact(_team(expected_threat_for=2.4))
        self.assertGreater(high["possession_value_score"], low["possession_value_score"])

    def test_021_obv_vaep_affects_possession_value(self):
        result = evaluate_soccer_possession_value_impact(_team(possession_value_for=2.2, vaep_for=2.0))
        self.assertGreater(result["possession_value_score"], 60)

    def test_022_missing_xt_obv_vaep_not_fabricated(self):
        result = evaluate_soccer_possession_value_impact({"shots_for_per_game": 12, "goals_for_per_game": 1.4})
        self.assertFalse(result["xt_fabricated"])
        self.assertFalse(result["obv_vaep_fabricated"])

    def test_023_first_half_xg_affects_first_half_markets(self):
        result = evaluate_soccer_possession_value_impact(_team(first_half_xg_for=1.3), market_type="first_half_total")
        self.assertGreater(result["first_half_pressure_score"], 60)

    def test_024_basic_shots_goals_create_limited_proxy_only(self):
        result = evaluate_soccer_possession_value_impact({"goals_for_per_game": 1.6, "shots_for_per_game": 12.4}, data_tier=1)
        self.assertTrue(result["limited_proxy"])
        self.assertFalse(result["xg_fabricated"])


class TestSoccerTacticalPressingPlayerLineup(unittest.TestCase):
    def test_025_formation_context_works(self):
        result = evaluate_soccer_tactical_context(_tactical())
        self.assertEqual(result["formation"], "4-3-3")

    def test_026_missing_formation_does_not_fabricate(self):
        result = evaluate_soccer_tactical_context({"high_press_rate": 0.6})
        self.assertFalse(result["formation_fabricated"])

    def test_027_pressing_intensity_works(self):
        result = evaluate_soccer_tactical_context(_tactical(high_press_rate=0.8))
        self.assertGreater(result["pressing_score"], 60)

    def test_028_ppda_proxy_works(self):
        result = evaluate_soccer_tactical_context(_tactical(ppda_proxy=6.5))
        self.assertGreater(result["pressing_score"], 60)

    def test_029_counterpressing_works(self):
        result = evaluate_soccer_tactical_context(_tactical(counter_pressing_rate=0.8))
        self.assertGreater(result["counter_pressing_score"], 60)

    def test_030_defensive_line_height_works(self):
        result = evaluate_soccer_tactical_context(_tactical(defensive_line_height=0.85))
        self.assertGreater(result["tactical_fit_score"], 40)

    def test_031_tactical_shift_caps_confidence(self):
        result = evaluate_soccer_tactical_context(_tactical(tactical_shift_recent=1.0))
        self.assertIn("recent_tactical_or_manager_change_caps_history", result["no_bet_reasons"])

    def test_032_tactical_context_modifier_only(self):
        result = evaluate_soccer_tactical_context(_tactical())
        self.assertFalse(result["tactical_context_standalone_edge"])

    def test_033_high_turnovers_affect_relevance(self):
        result = evaluate_soccer_pressing_transition_context(_press(high_turnovers=13))
        self.assertGreater(result["high_turnover_score"], 60)

    def test_034_counterattack_xg_affects_btts_total(self):
        result = evaluate_soccer_pressing_transition_context(_press(counterattack_xg=0.7))
        self.assertGreater(result["transition_attack_score"], 60)

    def test_035_transition_defense_weakness_affects_markets(self):
        result = evaluate_soccer_pressing_transition_context(_press(transition_xg_against=0.8))
        self.assertGreater(result["transition_defense_risk"], 60)

    def test_036_rest_defense_quality_works(self):
        result = evaluate_soccer_pressing_transition_context(_press(rest_defense_quality=0.9, transition_xg_against=0.1))
        self.assertGreater(result["rest_defense_score"], 60)

    def test_037_missing_pressing_caps_but_not_fail(self):
        result = evaluate_soccer_pressing_transition_context({})
        self.assertFalse(result["pressing_fabricated"])

    def test_038_possession_share_alone_no_pressing_claim(self):
        result = evaluate_soccer_pressing_transition_context({"possession_share": 0.65})
        self.assertIn("pressing_not_inferred_from_possession_share", result["no_bet_reasons"])

    def test_039_goalkeeper_role_works(self):
        result = evaluate_soccer_player_role_impact({"role": "GOALKEEPER", "post_shot_xg_allowed": 0.8, "goals_prevented_proxy": 4, "minutes_projection": 90}, player_level_allowed=True)
        self.assertEqual(result["role"], "GOALKEEPER")

    def test_040_post_shot_xg_not_fabricated_from_save_percentage(self):
        result = evaluate_soccer_player_role_impact({"role": "GOALKEEPER", "save_percentage": 0.74}, player_level_allowed=True)
        self.assertFalse(result["post_shot_xg_fabricated"])

    def test_041_defender_role_supports_tackles_cards(self):
        result = evaluate_soccer_player_role_impact({"role": "CENTER_BACK", "tackles": 3.5, "card_risk": 0.6, "minutes_projection": 90}, player_level_allowed=True)
        self.assertGreater(result["defensive_work_score"], 40)

    def test_042_midfielder_role_supports_progression(self):
        result = evaluate_soccer_player_role_impact({"role": "CENTRAL_MIDFIELDER", "progressive_passes": 12, "xT_created": 0.8, "minutes_projection": 85}, player_level_allowed=True)
        self.assertGreater(result["creative_value_score"], 50)

    def test_043_forward_role_supports_goal_shots(self):
        result = evaluate_soccer_player_role_impact(_player(), player_level_allowed=True)
        self.assertGreater(result["attacking_threat_score"], 45)

    def test_044_penalty_taker_affects_goal_only_if_supplied(self):
        result = evaluate_soccer_player_role_impact(_player(penalty_taker_status="confirmed"), player_level_allowed=True)
        self.assertGreater(result["set_piece_role_score"], 0)

    def test_045_set_piece_taker_affects_assists_if_supplied(self):
        result = evaluate_soccer_player_role_impact(_player(set_piece_taker_status="confirmed"), player_level_allowed=True)
        self.assertGreater(result["set_piece_role_score"], 0)

    def test_046_minutes_substitution_caps_props(self):
        result = evaluate_soccer_player_role_impact(_player(minutes_projection=40, substitution_risk=0.8), player_level_allowed=True)
        self.assertIn("minutes_or_substitution_risk_caps_player_props", result["no_bet_reasons"])

    def test_047_missing_player_role_returns_not_allowed(self):
        result = evaluate_soccer_player_role_impact({}, player_level_allowed=False)
        self.assertFalse(result["player_level_allowed"])

    def test_048_confirmed_lineup_raises_certainty(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(confirmed_lineup=True))
        self.assertGreater(result["lineup_certainty_score"], 60)

    def test_049_unconfirmed_lineup_caps_player_props(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(confirmed_lineup=False))
        self.assertIn("confirmed_lineup_missing_caps_player_props_tactical_confidence", result["no_bet_reasons"])

    def test_050_missing_confirmed_goalkeeper_caps_team_total(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(starting_goalkeeper_confirmed=False))
        self.assertIn("confirmed_goalkeeper_missing_caps_team_total_confidence", result["no_bet_reasons"])

    def test_051_rotation_risk_affects_markets(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(rotation_risk=0.9))
        self.assertGreater(result["rotation_risk_score"], 60)

    def test_052_fixture_congestion_creates_risk(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(fixture_congestion=0.9, midweek_match=True))
        self.assertGreater(result["rotation_risk_score"], 45)

    def test_053_travel_rest_affects_volatility(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(days_rest=2, travel_distance=4000, time_zone_change=3))
        self.assertGreater(result["rest_travel_risk_score"], 40)

    def test_054_suspensions_injuries_affect_no_bet(self):
        result = evaluate_soccer_lineup_availability_context(_lineup(key_attacker_absent=True, suspension_context=1))
        self.assertIn("injury_or_suspension_context_affects_market_confidence", result["no_bet_reasons"])

    def test_055_do_not_fabricate_injury_status(self):
        result = evaluate_soccer_lineup_availability_context(_lineup())
        self.assertFalse(result["injury_status_fabricated"])


class TestSoccerSetPieceGoalkeeperRefereeMatchup(unittest.TestCase):
    def test_056_set_piece_xg_separated_from_open_play(self):
        result = evaluate_soccer_set_piece_context(_setpiece())
        self.assertTrue(result["set_piece_xg_separated"])

    def test_057_corner_rate_affects_set_piece_relevance(self):
        result = evaluate_soccer_set_piece_context(_setpiece(corner_rate_for=8.5))
        self.assertGreater(result["corner_context_score"], 60)

    def test_058_penalty_context_works(self):
        result = evaluate_soccer_set_piece_context(_setpiece(penalty_rate_for=0.4))
        self.assertGreater(result["penalty_context_score"], 50)

    def test_059_penalty_taker_not_fabricated(self):
        result = evaluate_soccer_set_piece_context({"set_piece_xg_for": 0.2})
        self.assertFalse(result["penalty_taker_fabricated"])

    def test_060_aerial_mismatch_works(self):
        result = evaluate_soccer_set_piece_context(_setpiece(aerial_duel_strength=0.9, opponent_set_piece_defense=0.2))
        self.assertGreater(result["aerial_mismatch_score"], 60)

    def test_061_referee_penalty_tendency_not_fabricated(self):
        result = evaluate_soccer_set_piece_context({"set_piece_xg_for": 0.2})
        self.assertFalse(result["referee_penalty_tendency_fabricated"])

    def test_062_confirmed_goalkeeper_raises_certainty(self):
        result = evaluate_soccer_goalkeeper_context(_keeper(confirmed_starter=True))
        self.assertGreaterEqual(result["starter_certainty_score"], 90)

    def test_063_missing_goalkeeper_confirmation_caps_confidence(self):
        result = evaluate_soccer_goalkeeper_context(_keeper(confirmed_starter=False))
        self.assertIn("goalkeeper_starter_unconfirmed_caps_team_total_goalkeeper_markets", result["no_bet_reasons"])

    def test_064_post_shot_xg_works(self):
        result = evaluate_soccer_goalkeeper_context(_keeper(post_shot_xg_allowed=0.5))
        self.assertGreater(result["shot_stopping_score"], 55)

    def test_065_save_percentage_treated_as_volatile(self):
        result = evaluate_soccer_goalkeeper_context({"confirmed_starter": True, "save_percentage": 0.78})
        self.assertIn("save_percentage_volatile_without_post_shot_xg", result["no_bet_reasons"])

    def test_066_distribution_sweeping_context_works(self):
        result = evaluate_soccer_goalkeeper_context(_keeper(sweep_actions=4, distribution_accuracy=0.9))
        self.assertGreater(result["distribution_score"], 50)
        self.assertGreater(result["sweeping_score"], 40)

    def test_067_keeper_errors_increase_volatility(self):
        result = evaluate_soccer_goalkeeper_context(_keeper(errors_leading_to_shots=3))
        self.assertIn("goalkeeper_errors_increase_scoreline_volatility", result["no_bet_reasons"])

    def test_068_card_rate_affects_card_markets(self):
        result = evaluate_soccer_referee_context(_ref(card_rate=7.0))
        self.assertGreater(result["card_market_relevance"], 60)

    def test_069_penalty_rate_affects_total_context(self):
        result = evaluate_soccer_referee_context(_ref(penalty_rate=0.4))
        self.assertGreater(result["penalty_market_relevance"], 60)

    def test_070_red_card_volatility_reduces_scoreline_confidence(self):
        result = evaluate_soccer_referee_context(_ref(red_card_rate=0.45))
        self.assertIn("red_card_volatility_reduces_scoreline_confidence", result["no_bet_reasons"])

    def test_071_missing_referee_does_not_fabricate(self):
        result = evaluate_soccer_referee_context({"referee_name": "sample"})
        self.assertFalse(result["referee_tendency_fabricated"])

    def test_072_referee_context_modifier_only(self):
        result = evaluate_soccer_referee_context(_ref())
        self.assertFalse(result["referee_context_standalone_edge"])

    def test_073_high_press_vs_weak_build_up(self):
        result = evaluate_soccer_matchup_context({**_tactical(), "opponent_build_up_error_rate": 0.8})
        self.assertIn("high_press_vs_weak_build_up", result["tactical_mismatch_reasons"])

    def test_074_counterattack_vs_high_line(self):
        result = evaluate_soccer_matchup_context({"counterattack_xg": 0.7, "opponent_defensive_line_height": 0.9})
        self.assertIn("counterattack_vs_high_defensive_line", result["tactical_mismatch_reasons"])

    def test_075_wide_overload_mismatch(self):
        result = evaluate_soccer_matchup_context({"wide_progression_rate": 0.9, "overload_side": 0.9, "opponent_fullback_weakness": 0.9})
        self.assertIn("wide_overload_vs_weak_fullback_side", result["tactical_mismatch_reasons"])

    def test_076_set_piece_attack_vs_defense(self):
        result = evaluate_soccer_matchup_context({"set_piece_xg_for": 0.75, "opponent_set_piece_defense": 0.2})
        self.assertIn("set_piece_attack_vs_set_piece_defense", result["tactical_mismatch_reasons"])

    def test_077_low_block_vs_possession_team(self):
        result = evaluate_soccer_matchup_context({"possession_share": 0.65, "opponent_low_block": 0.9, "xg_per_shot": 0.15})
        self.assertIn("possession_team_vs_low_block_shot_quality", result["tactical_mismatch_reasons"])

    def test_078_tactical_mismatch_not_without_support(self):
        result = evaluate_soccer_matchup_context({})
        self.assertFalse(result["tactical_mismatch_fabricated"])

    def test_079_conflicting_signals_lower_confidence(self):
        result = evaluate_soccer_matchup_context({"confirmed_lineup": False})
        self.assertGreaterEqual(result["matchup_risk_score"], 40)


class TestSoccerIncentiveMarketCalibrationRedTeam(unittest.TestCase):
    def test_080_incentive_modifier_only(self):
        result = evaluate_soccer_incentive_context({"fixture_priority": 1.0})
        self.assertFalse(result["incentive_is_standalone_edge"])

    def test_081_missing_bonus_threshold_not_fabricated(self):
        result = evaluate_soccer_incentive_context({"contract_year": True})
        self.assertFalse(result["bonus_threshold_fabricated"])

    def test_082_golden_boot_modifies_props_if_supplied(self):
        result = evaluate_soccer_incentive_context({"known_bonus_thresholds": [{"goals": 20}], "golden_boot_context": 1.0})
        self.assertGreater(result["market_relevance_modifier"]["player_prop_relevance_adjustment"], 0)

    def test_083_cup_rotation_affects_lineup_confidence(self):
        result = evaluate_soccer_incentive_context({"cup_rotation_context": 1.0, "fixture_priority": 0.2})
        self.assertIn("cup_rotation_or_fixture_priority_caps_lineup_confidence", result["no_bet_reasons"])

    def test_084_narrative_overfit_downgraded(self):
        result = evaluate_soccer_incentive_context({"revenge_narrative_context": "unverified"})
        self.assertEqual(result["narrative_overfit_risk"], "high")

    def _diagnostic(self, market="asian_handicap"):
        return build_soccer_impact_diagnostics(
            sport="soccer",
            market_type=market,
            game_context={"home_team": "home", "away_team": "away"},
            team_context=_team(),
            tactical_context=_tactical(),
            pressing_context=_press(),
            transition_context=_press(),
            player_context=_player(),
            lineup_context=_lineup(),
            set_piece_context=_setpiece(),
            goalkeeper_context=_keeper(),
            referee_context=_ref(),
            calibration_context={"matched_outcomes_count": 0},
        )

    def test_085_three_way_relevance_links_core_signals(self):
        result = self._diagnostic("three_way_moneyline")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["three_way_moneyline"], 45)

    def test_086_asian_handicap_links_xg_field_tilt(self):
        result = self._diagnostic("asian_handicap")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["asian_handicap"], 45)

    def test_087_totals_links_xg_transition_referee_keeper(self):
        result = self._diagnostic("total")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["total"], 40)

    def test_088_team_total_links_xg_box_setpieces(self):
        result = self._diagnostic("team_total")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["team_total"], 45)

    def test_089_btts_links_xg_transition_keeper_uncertainty(self):
        result = self._diagnostic("both_teams_to_score")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["both_teams_to_score"], 35)

    def test_090_correct_score_conservative_capped(self):
        result = self._diagnostic("correct_score")
        self.assertIn("correct_score", result["market_relevance"]["market_confidence_caps"])

    def test_091_first_half_relevance_links_first_half_xg(self):
        result = self._diagnostic("first_half_total")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["first_half_total"], 35)

    def test_092_anytime_goal_links_npxg_minutes_penalty(self):
        result = self._diagnostic("anytime_goal")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["anytime_goal"], 40)

    def test_093_shots_sot_link_volume_role_minutes(self):
        result = self._diagnostic("shots_on_target")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["shots_on_target"], 40)

    def test_094_assists_passes_link_creative_progression(self):
        result = self._diagnostic("assists")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["assists"], 35)

    def test_095_cards_fouls_link_referee_tactical_stress(self):
        result = self._diagnostic("cards")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["cards"], 35)

    def test_096_goalkeeper_saves_link_opponent_volume(self):
        result = self._diagnostic("goalkeeper_saves")
        self.assertGreater(result["market_relevance"]["market_relevance_scores"]["goalkeeper_saves"], 35)

    def test_097_no_labeled_outcomes_insufficient_data(self):
        result = evaluate_soccer_impact_calibration({}, sport="soccer", market_type="total")
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_098_low_sample_insufficient_sample(self):
        result = evaluate_soccer_impact_calibration({"matched_outcomes_count": 20}, sport="soccer", market_type="total")
        self.assertTrue(result["insufficient_sample"])

    def test_099_real_labeled_outcomes_partial_calibration(self):
        result = evaluate_soccer_impact_calibration({"settled_outcomes": [{"hit": True}, {"hit": False}], "historical_predictions": [1, 2]}, sport="soccer", market_type="total")
        self.assertEqual(result["calibration_status"], "partial_calibration")

    def test_100_roi_not_emitted_without_returns(self):
        result = evaluate_soccer_impact_calibration({"settled_outcomes": [{"hit": True}]}, sport="soccer", market_type="total")
        self.assertNotIn("roi_proxy", result)

    def test_101_clv_not_emitted_without_prices(self):
        result = evaluate_soccer_impact_calibration({"settled_outcomes": [{"hit": True}]}, sport="soccer", market_type="total")
        self.assertNotIn("clv_proxy", result)

    def test_102_slippage_not_emitted_without_fills(self):
        result = evaluate_soccer_impact_calibration({"settled_outcomes": [{"hit": True}]}, sport="soccer", market_type="total")
        self.assertNotIn("slippage_proxy", result)

    def test_103_correct_score_extra_conservative(self):
        result = evaluate_soccer_impact_calibration({"matched_outcomes_count": 100}, sport="soccer", market_type="correct_score")
        self.assertTrue(result["correct_score_extra_conservative"])
        self.assertLessEqual(result["confidence_cap"], 32)

    def test_104_context_buckets_preserved(self):
        result = evaluate_soccer_impact_calibration({"matched_outcomes_count": 100, "lineup_status_bucket": "confirmed"}, sport="soccer", market_type="total")
        self.assertEqual(result["calibration_buckets"]["lineup_status_bucket"], "confirmed")

    def test_105_fake_xt_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"missing_field_groups": ["expected_threat_context"]}, tracking_context={"claimed_xt": True})
        self.assertIn("xt_missing_but_claimed", red["red_team_reasons"])

    def test_106_fake_obv_vaep_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"missing_field_groups": ["obv_vaep_context"]}, tracking_context={"claimed_obv_vaep": True})
        self.assertIn("obv_vaep_missing_but_claimed", red["red_team_reasons"])

    def test_107_fake_tracking_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"tracking_level_allowed": False}, tracking_context={"pitch_control": 0.5})
        self.assertIn("tracking_missing_but_claimed", red["red_team_reasons"])

    def test_108_fake_pitch_control_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"missing_field_groups": ["tracking_context"]}, tracking_context={"claimed_pitch_control": True})
        self.assertIn("pitch_control_missing_but_claimed", red["red_team_reasons"])

    def test_109_fake_formation_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"missing_field_groups": ["formation_context"]}, tracking_context={"claimed_formation": True})
        self.assertIn("formation_missing_but_claimed", red["red_team_reasons"])

    def test_110_missing_lineup_overconfidence_downgraded(self):
        red = evaluate_soccer_impact_red_team(lineup_availability_context={"lineup_certainty_score": 28}, market_relevance={"selected_market_type": "shots"})
        self.assertIn("confirmed_lineup_missing_overconfidence", red["red_team_reasons"])

    def test_111_missing_goalkeeper_confirmation_downgraded(self):
        red = evaluate_soccer_impact_red_team(goalkeeper_context={"starter_certainty_score": 28}, market_relevance={"selected_market_type": "total"})
        self.assertIn("goalkeeper_confirmation_missing_overconfidence", red["red_team_reasons"])

    def test_112_missing_referee_tendency_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"missing_field_groups": ["referee_context"]}, tracking_context={"claimed_referee_tendency": True})
        self.assertIn("referee_tendency_missing_but_claimed", red["red_team_reasons"])

    def test_113_missing_penalty_taker_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(set_piece_context={"missing_inputs": ["penalty_taker_status"]}, tracking_context={"claimed_penalty_taker": True})
        self.assertIn("penalty_taker_missing_but_claimed", red["red_team_reasons"])

    def test_114_missing_set_piece_role_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(set_piece_context={"missing_inputs": ["set_piece_taker_status"]}, tracking_context={"claimed_set_piece_role": True})
        self.assertIn("set_piece_role_missing_but_claimed", red["red_team_reasons"])

    def test_115_missing_post_shot_xg_claim_downgraded(self):
        red = evaluate_soccer_impact_red_team(goalkeeper_context={"shot_stopping_score": 70, "missing_goalkeeper_inputs": ["post_shot_xg_allowed"]})
        self.assertIn("post_shot_xg_missing_but_claimed", red["red_team_reasons"])

    def test_116_small_sample_xg_overfit_downgraded(self):
        red = evaluate_soccer_impact_red_team(possession_value_impact={"insufficient_sample": True, "xg_quality_score": 70})
        self.assertIn("small_sample_xg_overfit", red["red_team_reasons"])

    def test_117_recent_form_overfit_downgraded(self):
        red = evaluate_soccer_impact_red_team(tracking_context={"recent_form_claimed": True})
        self.assertIn("recent_form_overfit", red["red_team_reasons"])

    def test_118_possession_percentage_overfit_downgraded(self):
        red = evaluate_soccer_impact_red_team(possession_value_impact={"limited_proxy": True, "territorial_dominance_score": 70})
        self.assertIn("possession_percentage_overfit", red["red_team_reasons"])

    def test_119_tactical_narrative_overfit_downgraded(self):
        red = evaluate_soccer_impact_red_team(incentive_context={"narrative_overfit_risk": "high"})
        self.assertIn("tactical_narrative_overfit", red["red_team_reasons"])

    def test_120_red_card_volatility_ignored_downgraded(self):
        red = evaluate_soccer_impact_red_team(referee_context={"red_card_volatility_risk": 80}, market_relevance={"selected_market_type": "correct_score"})
        self.assertIn("red_card_volatility_ignored", red["red_team_reasons"])

    def test_121_correct_score_overconfidence_downgraded(self):
        red = evaluate_soccer_impact_red_team(market_relevance={"selected_market_type": "correct_score"}, calibration={"calibration_status": "insufficient_data"})
        self.assertIn("correct_score_overconfidence", red["red_team_reasons"])

    def test_122_first_half_full_game_confusion_downgraded(self):
        red = evaluate_soccer_impact_red_team(data_availability={"missing_field_groups": ["first_half_context"]}, possession_value_impact={"total_signal_score": 70}, market_relevance={"selected_market_type": "first_half_total"})
        self.assertIn("first_half_full_game_context_confusion", red["red_team_reasons"])

    def test_123_calibration_missing_prevents_active_review(self):
        result = self._diagnostic("asian_handicap")
        self.assertEqual(result["calibration_status"], "insufficient_data")
        self.assertNotEqual(result["recommended_review_status"], "ACTIVE_REVIEW")


class TestSoccerSafetyAndEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_124_readiness_provider_write_false(self):
        response = self.client.get("/api/automation/soccer-impact-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_125_diagnostics_execution_allowed_false(self):
        response = self.client.post("/api/automation/soccer-impact-diagnostics", json={"sport": "soccer", "team_context": _team()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_126_dry_run_false_rejected(self):
        response = self.client.post("/api/automation/soccer-impact-diagnostics", json={"sport": "soccer", "dry_run": False})
        self.assertEqual(response.status_code, 400)

    def test_127_no_order_payload_survives_compaction(self):
        safe = redact_and_limit_payload({"order_payload": {"side": "buy"}})
        self.assertEqual(safe["order_payload"], "[omitted]")

    def test_128_no_bet_slip_survives_compaction(self):
        safe = redact_and_limit_payload({"bet_slip": {"stake": 10}, "slip_payload": {"stake": 10}})
        self.assertEqual(safe["bet_slip"], "[omitted]")
        self.assertEqual(safe["slip_payload"], "[omitted]")

    def test_129_secrets_raw_payloads_redacted(self):
        result = build_soccer_impact_diagnostics(team_context={"team": "A", "api_key": "sk_test_secret_value_1234567890", "raw_payload": {"x": 1}})
        self.assertFalse(result["secrets_included"])
        self.assertNotIn("sk_test_secret", str(result))

    def test_130_red_team_cannot_promote_execution(self):
        red = evaluate_soccer_impact_red_team()
        self.assertFalse(red["execution_allowed"])
        self.assertFalse(red["provider_write"])

    def test_131_health_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/health").status_code, 200)

    def test_132_security_readiness_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/security-readiness").status_code, 200)

    def test_133_strategy_readiness_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/strategy-readiness").status_code, 200)

    def test_134_advanced_red_team_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/advanced-red-team-report").status_code, 200)

    def test_135_extreme_randomness_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/extreme-randomness-report").status_code, 200)

    def test_136_basketball_impact_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/basketball-player-impact-readiness").status_code, 200)

    def test_137_football_impact_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/football-impact-readiness").status_code, 200)

    def test_138_baseball_impact_still_passes_if_present(self):
        response = self.client.get("/api/automation/baseball-impact-readiness")
        if response.status_code != 404:
            self.assertEqual(response.status_code, 200)

    def test_139_hockey_impact_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/hockey-impact-readiness").status_code, 200)

    def test_140_soccer_malformed_payload_does_not_500(self):
        response = self.client.post("/api/automation/soccer-impact-diagnostics", json={"sport": "soccer", "team_context": "bad"})
        self.assertLess(response.status_code, 500)

    def test_141_limited_public_data_no_fake_tracking_possession_value(self):
        response = self.client.post(
            "/api/automation/soccer-impact-diagnostics",
            json={
                "sport": "soccer",
                "market_type": "total",
                "team_context": {"goals_for_per_game": 1.6, "shots_for_per_game": 12.4, "shots_against_per_game": 10.9},
                "goalkeeper_context": {"confirmed_starter": False},
                "lineup_context": {"confirmed_lineup": False},
                "calibration_context": {"matched_outcomes_count": 0},
            },
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(payload["tracking_level_allowed"])
        self.assertFalse(payload["possession_value_impact"]["xt_fabricated"])
        self.assertFalse(payload["possession_value_impact"]["obv_vaep_fabricated"])

    def test_142_compact_output_safety_locked(self):
        compact = compact_soccer_impact_diagnostics_response(build_soccer_impact_diagnostics(team_context=_team()))
        self.assertFalse(compact["provider_write"])
        self.assertFalse(compact["execution_allowed"])
        self.assertTrue(compact["compact_response"])


if __name__ == "__main__":
    unittest.main()
