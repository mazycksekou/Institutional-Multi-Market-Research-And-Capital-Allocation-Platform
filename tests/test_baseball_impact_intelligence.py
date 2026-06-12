import unittest

from fastapi.testclient import TestClient

from automation_scheduler.baseball_availability_context import evaluate_baseball_availability_context
from automation_scheduler.baseball_batter_impact import evaluate_baseball_batter_impact
from automation_scheduler.baseball_bullpen_context import evaluate_baseball_bullpen_context
from automation_scheduler.baseball_data_availability import evaluate_baseball_data_availability
from automation_scheduler.baseball_defense_baserunning_context import evaluate_baseball_defense_baserunning_context
from automation_scheduler.baseball_impact_calibration import evaluate_baseball_impact_calibration
from automation_scheduler.baseball_impact_readiness import build_baseball_impact_readiness
from automation_scheduler.baseball_impact_red_team import evaluate_baseball_impact_red_team
from automation_scheduler.baseball_impact_report import build_baseball_impact_diagnostics
from automation_scheduler.baseball_incentive_context import evaluate_baseball_incentive_context
from automation_scheduler.baseball_lineup_context import evaluate_baseball_lineup_context
from automation_scheduler.baseball_market_relevance import evaluate_baseball_market_relevance
from automation_scheduler.baseball_matchup_context import evaluate_baseball_matchup_context
from automation_scheduler.baseball_park_weather_umpire_context import evaluate_baseball_park_weather_umpire_context
from automation_scheduler.baseball_pitcher_impact import evaluate_baseball_pitcher_impact
from automation_scheduler.baseball_run_value_impact import evaluate_baseball_run_value_impact
from automation_scheduler.response_compactor import compact_baseball_impact_diagnostics_response
from tests.support.action_imports import app


def _team_context(**extra):
    row = {
        "team": "sample_home",
        "opponent": "sample_away",
        "runs_scored_per_game": 4.7,
        "runs_allowed_per_game": 4.2,
        "team_woba": 0.335,
        "team_xwoba": 0.342,
        "team_iso": 0.178,
        "team_k_rate": 0.215,
        "team_bb_rate": 0.086,
        "team_barrel_rate": 0.085,
        "team_hard_hit_rate": 0.42,
    }
    row.update(extra)
    return row


def _pitcher_context(**extra):
    row = {
        "role": "STARTING_PITCHER",
        "confirmed_starter": True,
        "k_rate": 0.285,
        "bb_rate": 0.072,
        "k_minus_bb_rate": 0.213,
        "whiff_rate": 0.31,
        "chase_rate": 0.34,
        "zone_rate": 0.50,
        "first_pitch_strike_rate": 0.63,
        "called_strike_plus_whiff_proxy": 0.30,
        "swinging_strike_rate": 0.13,
        "ground_ball_rate": 0.46,
        "fly_ball_rate": 0.34,
        "barrel_allowed_rate": 0.065,
        "hard_hit_allowed_rate": 0.36,
        "xwoba_allowed": 0.305,
        "xba_allowed": 0.238,
        "xslg_allowed": 0.385,
        "hr_per_9_proxy": 1.05,
        "pitch_count_recent": 94,
        "innings_per_start": 5.9,
        "times_through_order_penalty": 0.08,
        "rest_days": 5,
        "sample_size": 240,
    }
    row.update(extra)
    return row


def _batter_context(**extra):
    row = {
        "role": "BATTER",
        "plate_appearances_projection": 4.5,
        "lineup_slot": 2,
        "confirmed_lineup": True,
        "handedness": "R",
        "platoon_split_woba": 0.365,
        "platoon_split_xwoba": 0.374,
        "k_rate": 0.19,
        "bb_rate": 0.10,
        "chase_rate": 0.26,
        "whiff_rate": 0.22,
        "zone_contact_rate": 0.86,
        "contact_rate": 0.78,
        "hard_hit_rate": 0.47,
        "barrel_rate": 0.12,
        "average_exit_velocity": 91.5,
        "launch_angle": 14.0,
        "sweet_spot_rate": 0.36,
        "xwoba": 0.370,
        "xba": 0.285,
        "xslg": 0.520,
        "iso": 0.220,
        "pull_rate": 0.43,
        "ground_ball_rate": 0.39,
        "fly_ball_rate": 0.41,
        "sprint_speed": 28.5,
        "stolen_base_attempt_rate": 0.08,
        "recent_form_proxy": 62,
        "sample_size": 220,
    }
    row.update(extra)
    return row


def _lineup_context(**extra):
    row = {
        "confirmed_lineup": True,
        "lineup_slot": 2,
        "team_woba": 0.335,
        "team_xwoba": 0.342,
        "team_iso": 0.178,
        "team_k_rate": 0.215,
        "team_bb_rate": 0.086,
        "lineup_handedness_balance": 0.55,
    }
    row.update(extra)
    return row


def _bullpen_context(**extra):
    row = {
        "bullpen_era_proxy": 3.55,
        "bullpen_fip_proxy": 3.75,
        "bullpen_xwoba_allowed": 0.315,
        "bullpen_k_rate": 0.25,
        "bullpen_bb_rate": 0.08,
        "bullpen_hr_rate": 0.032,
        "bullpen_recent_innings": 7.0,
        "bullpen_recent_pitch_count": 112,
        "closer_available": True,
        "setup_available": True,
    }
    row.update(extra)
    return row


def _park_weather_context(**extra):
    row = {
        "park_factor": 1.04,
        "home_run_factor": 1.08,
        "run_factor": 1.03,
        "roof_status": "open",
        "wind_speed": 8,
        "wind_direction": "out",
        "temperature": 76,
    }
    row.update(extra)
    return row


def _umpire_context(**extra):
    row = {
        "umpire_name": "sample_ump",
        "umpire_zone_size_proxy": 1.04,
        "umpire_k_rate_proxy": 0.23,
        "umpire_walk_rate_proxy": 0.08,
        "umpire_over_under_tendency_proxy": 0.51,
    }
    row.update(extra)
    return row


def _full_report(**overrides):
    payload = {
        "sport": "baseball_mlb",
        "market_type": "total",
        "game_context": {"home_team": "sample_home", "away_team": "sample_away"},
        "team_context": _team_context(),
        "pitcher_context": _pitcher_context(),
        "batter_context": _batter_context(),
        "lineup_context": _lineup_context(),
        "bullpen_context": _bullpen_context(),
        "park_weather_context": _park_weather_context(),
        "umpire_context": _umpire_context(),
        "calibration_context": {"matched_outcomes_count": 0},
    }
    payload.update(overrides)
    return build_baseball_impact_diagnostics(**payload)


class TestBaseballDataAvailability(unittest.TestCase):
    def test_01_mlb_tier_0_returns_data_insufficient(self):
        result = evaluate_baseball_data_availability("baseball_mlb")
        self.assertEqual(result["data_tier"], 0)
        self.assertEqual(result["recommended_review_status"], "DATA_INSUFFICIENT")

    def test_02_missing_statcast_style_data_does_not_fail(self):
        result = build_baseball_impact_diagnostics(
            sport="baseball_mlb",
            market_type="moneyline",
            team_context={"team": "A", "opponent": "B", "runs_scored_per_game": 4.5},
        )
        self.assertTrue(result["ok"])
        self.assertIn("contact_quality_context", result["data_availability"]["missing_field_groups"])

    def test_03_missing_pitch_tracking_does_not_fail(self):
        result = build_baseball_impact_diagnostics(
            sport="baseball_mlb",
            market_type="pitcher_strikeouts",
            pitcher_context=_pitcher_context(spin_rate_proxy=None, pitch_movement_proxy=None, extension_proxy=None),
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["pitcher_impact"]["pitch_tracking_inferred"])

    def test_04_missing_bat_tracking_does_not_fail(self):
        result = evaluate_baseball_batter_impact(_batter_context())
        self.assertFalse(result["bat_tracking_inferred"])
        self.assertIn("bat_speed", result["missing_batter_inputs"])

    def test_05_tier_1_basic_data_caps_confidence(self):
        result = build_baseball_impact_diagnostics(
            sport="baseball_mlb",
            market_type="total",
            team_context={"team": "A", "opponent": "B", "runs_scored_per_game": 4.7, "runs_allowed_per_game": 4.2},
        )
        self.assertEqual(result["data_tier"], 1)
        self.assertLessEqual(result["data_availability"]["confidence_cap"], 50)

    def test_06_tier_2_split_box_score_data_enables_limited_diagnostics(self):
        result = evaluate_baseball_data_availability(
            "baseball_mlb",
            pitcher_context={"k_rate": 0.25, "bb_rate": 0.07, "pitcher_hand": "R"},
            batter_context={"platoon_split_woba": 0.350, "handedness": "L"},
        )
        self.assertEqual(result["data_tier"], 2)
        self.assertTrue(result["pitcher_level_allowed"])

    def test_07_tier_3_pitch_contact_data_enables_stronger_diagnostics(self):
        result = evaluate_baseball_data_availability(
            "baseball_mlb",
            pitcher_context={"whiff_rate": 0.31, "chase_rate": 0.34},
            batter_context={"xwoba": 0.370, "barrel_rate": 0.12, "hard_hit_rate": 0.47},
        )
        self.assertEqual(result["data_tier"], 3)
        self.assertTrue(result["batter_level_allowed"])

    def test_08_tier_4_tracking_fields_optional_never_required(self):
        tier3 = evaluate_baseball_data_availability("baseball_mlb", batter_context={"xwoba": 0.360, "barrel_rate": 0.10})
        tier4 = evaluate_baseball_data_availability("baseball_mlb", tracking_context={"bat_speed": 73.0})
        self.assertEqual(tier3["data_tier"], 3)
        self.assertFalse(tier3["tracking_level_allowed"])
        self.assertEqual(tier4["data_tier"], 4)

    def test_09_missing_pitcher_context_still_allows_team_diagnostics(self):
        result = build_baseball_impact_diagnostics(sport="baseball_mlb", market_type="total", team_context=_team_context())
        self.assertTrue(result["data_availability"]["team_level_allowed"])
        self.assertFalse(result["data_availability"]["pitcher_level_allowed"])

    def test_10_missing_batter_context_still_allows_team_diagnostics(self):
        result = build_baseball_impact_diagnostics(sport="baseball_mlb", market_type="moneyline", team_context=_team_context(), pitcher_context=_pitcher_context())
        self.assertTrue(result["data_availability"]["team_level_allowed"])
        self.assertFalse(result["data_availability"]["batter_level_allowed"])


class TestBaseballRunValue(unittest.TestCase):
    def test_11_pitch_level_run_value_affects_pitcher_team_scoring(self):
        base = evaluate_baseball_run_value_impact(_team_context())
        rich = evaluate_baseball_run_value_impact({**_team_context(), "pitch_run_value": 0.18, "pitch_type_run_values": {"fastball": 0.12}})
        self.assertGreater(rich["pitch_level_score"], base["pitch_level_score"])

    def test_12_plate_appearance_run_value_affects_batter_team_scoring(self):
        low = evaluate_baseball_run_value_impact({"plate_appearance_run_value": -0.05, "expected_runs_created": 3.6, "sample_size": 250})
        high = evaluate_baseball_run_value_impact({"plate_appearance_run_value": 0.15, "expected_runs_created": 5.0, "sample_size": 250})
        self.assertGreater(high["plate_appearance_score"], low["plate_appearance_score"])

    def test_13_missing_run_value_uses_limited_proxy_only_if_allowed(self):
        result = evaluate_baseball_run_value_impact({"runs_scored_per_game": 4.8, "runs_allowed_per_game": 4.1, "sample_size": 220})
        self.assertTrue(result["limited_proxy"])
        self.assertFalse(result["run_value_fabricated"])

    def test_14_small_sample_flags_insufficient_sample(self):
        result = evaluate_baseball_run_value_impact({"pitch_run_value": 0.1, "sample_size": 18})
        self.assertTrue(result["insufficient_sample"])

    def test_15_first_five_scoring_weights_starter_context_more(self):
        weak = evaluate_baseball_run_value_impact({"starter_fip_proxy": 5.1, "first_five_run_differential": -0.7, "sample_size": 240})
        strong = evaluate_baseball_run_value_impact({"starter_fip_proxy": 3.1, "first_five_run_differential": 0.8, "sample_size": 240})
        self.assertGreater(strong["first_five_signal_score"], weak["first_five_signal_score"])

    def test_16_full_game_scoring_includes_bullpen_context(self):
        low = evaluate_baseball_run_value_impact({"runs_scored_per_game": 4.5, "bullpen_quality_score": 25, "sample_size": 240})
        high = evaluate_baseball_run_value_impact({"runs_scored_per_game": 4.5, "bullpen_quality_score": 80, "sample_size": 240})
        self.assertGreater(high["full_game_signal_score"], low["full_game_signal_score"])

    def test_17_total_scoring_includes_park_weather_umpire_context(self):
        low = evaluate_baseball_run_value_impact({"runs_scored_per_game": 4.2, "park_run_environment_score": 35, "umpire_zone_modifier": 0.95, "sample_size": 240})
        high = evaluate_baseball_run_value_impact({"runs_scored_per_game": 4.2, "park_run_environment_score": 85, "umpire_zone_modifier": 1.08, "sample_size": 240})
        self.assertGreater(high["total_signal_score"], low["total_signal_score"])


class TestBaseballPitcherImpact(unittest.TestCase):
    def test_18_starting_pitcher_core_fields_produce_stable_score(self):
        result = evaluate_baseball_pitcher_impact(_pitcher_context())
        self.assertEqual(result["pitcher_role"], "STARTING_PITCHER")
        self.assertGreater(result["pitcher_impact_score"], 50)

    def test_19_missing_pitch_tracking_does_not_fabricate_spin_movement_extension(self):
        result = evaluate_baseball_pitcher_impact(_pitcher_context())
        self.assertFalse(result["pitch_tracking_inferred"])
        self.assertIn("spin_rate_proxy", result["missing_pitcher_inputs"])

    def test_20_pitch_count_rest_fatigue_affects_pitcher_props(self):
        rested = evaluate_baseball_pitcher_impact(_pitcher_context(rest_days=6, pitch_count_recent=85))
        tired = evaluate_baseball_pitcher_impact(_pitcher_context(rest_days=3, pitch_count_recent=112))
        self.assertGreater(tired["workload_fatigue_score"], rested["workload_fatigue_score"])

    def test_21_times_through_order_risk_affects_starter_markets(self):
        low = evaluate_baseball_pitcher_impact(_pitcher_context(times_through_order_penalty=0.02))
        high = evaluate_baseball_pitcher_impact(_pitcher_context(times_through_order_penalty=0.18))
        self.assertGreater(high["times_through_order_risk"], low["times_through_order_risk"])

    def test_22_reliever_back_to_back_usage_affects_bullpen_score(self):
        fresh = evaluate_baseball_pitcher_impact({"role": "RELIEF_PITCHER", "recent_pitch_count": 12, "back_to_back_usage": False})
        tired = evaluate_baseball_pitcher_impact({"role": "RELIEF_PITCHER", "recent_pitch_count": 34, "back_to_back_usage": True})
        self.assertGreater(tired["workload_fatigue_score"], fresh["workload_fatigue_score"])

    def test_23_unconfirmed_starter_caps_first_five_pitcher_prop_confidence(self):
        result = evaluate_baseball_pitcher_impact(_pitcher_context(confirmed_starter=False))
        self.assertIn("unconfirmed_starter_caps_pitcher_prop_and_first_five_confidence", result["no_bet_reasons"])

    def test_24_opener_bulk_context_prevents_overconfident_starter_prop_output(self):
        result = evaluate_baseball_pitcher_impact(_pitcher_context(opener_risk=True))
        self.assertIn("opener_bulk_pattern_caps_starter_props", result["no_bet_reasons"])


class TestBaseballBatterImpact(unittest.TestCase):
    def test_25_contact_quality_fields_affect_batter_score(self):
        low = evaluate_baseball_batter_impact(_batter_context(hard_hit_rate=0.28, barrel_rate=0.03, xwoba=0.300))
        high = evaluate_baseball_batter_impact(_batter_context(hard_hit_rate=0.52, barrel_rate=0.15, xwoba=0.405))
        self.assertGreater(high["contact_quality_score"], low["contact_quality_score"])

    def test_26_expected_stats_affect_prop_relevance_where_supplied(self):
        result = evaluate_baseball_batter_impact(_batter_context(xwoba=0.390, xba=0.305, xslg=0.570))
        self.assertGreater(result["hit_probability_proxy"], 50)
        self.assertGreater(result["total_bases_relevance_score"], 50)

    def test_27_missing_bat_tracking_does_not_fabricate_bat_speed_swing_length(self):
        result = evaluate_baseball_batter_impact(_batter_context())
        self.assertFalse(result["bat_tracking_inferred"])
        self.assertIn("swing_length", result["missing_batter_inputs"])

    def test_28_platoon_split_works_where_supplied(self):
        low = evaluate_baseball_batter_impact(_batter_context(platoon_split_woba=0.290, platoon_split_xwoba=0.300))
        high = evaluate_baseball_batter_impact(_batter_context(platoon_split_woba=0.390, platoon_split_xwoba=0.405))
        self.assertGreater(high["batter_impact_score"], low["batter_impact_score"])

    def test_29_unknown_batting_order_caps_pa_projection(self):
        result = evaluate_baseball_batter_impact(_batter_context(lineup_slot=None, confirmed_lineup=False))
        self.assertIn("batting_order_unknown_caps_batter_prop_confidence", result["no_bet_reasons"])

    def test_30_recent_form_is_weak_modifier_only(self):
        cold = evaluate_baseball_batter_impact(_batter_context(recent_form_proxy=25))
        hot = evaluate_baseball_batter_impact(_batter_context(recent_form_proxy=95))
        self.assertTrue(hot["recent_form_modifier_only"])
        self.assertLess(hot["batter_impact_score"] - cold["batter_impact_score"], 25)

    def test_31_stolen_base_relevance_requires_runner_pitcher_catcher_context(self):
        result = evaluate_baseball_defense_baserunning_context({"sprint_speed": 29, "stolen_base_attempt_rate": 0.10})
        self.assertIn("stolen_base_context_incomplete", result["no_bet_reasons"])


class TestBaseballMatchup(unittest.TestCase):
    def test_32_handedness_matchup_works(self):
        result = evaluate_baseball_matchup_context({"pitcher_handedness": "L", "batter_handedness": "R", "team_platoon_woba": 0.360})
        self.assertGreater(result["matchup_advantage_score"], 0)

    def test_33_pitch_mix_vs_batter_weakness_works_where_supplied(self):
        result = evaluate_baseball_matchup_context({"pitch_mix_advantage_score": 72, "pitcher_primary_pitch": "slider", "hitter_pitch_type_weakness": "slider"})
        self.assertIn("pitch_mix_advantage", result["mismatch_reasons"])

    def test_34_strikeout_pitcher_vs_high_k_lineup_affects_k_props(self):
        result = evaluate_baseball_matchup_context({"pitcher_k_rate": 0.31, "opponent_k_rate": 0.26})
        self.assertIn("strikeout_pitcher_vs_high_k_lineup", result["mismatch_reasons"])
        self.assertIn("pitcher_strikeouts", result["market_specific_matchup_notes"])

    def test_35_barrel_heavy_lineup_vs_homer_prone_pitcher_affects_power_markets(self):
        result = evaluate_baseball_matchup_context({"pitcher_hr_rate": 0.05, "team_barrel_rate": 0.12})
        self.assertIn("barrel_heavy_lineup_vs_homer_prone_pitcher", result["mismatch_reasons"])
        self.assertIn("batter_home_runs", result["market_specific_matchup_notes"])

    def test_36_batter_vs_pitcher_history_is_low_weight(self):
        result = evaluate_baseball_matchup_context({"batter_vs_pitcher_history_weight": 0.6, "batter_vs_pitcher_pa": 8})
        self.assertLessEqual(result["batter_vs_pitcher_history_weight"], 0.1)
        self.assertIn("batter_vs_pitcher_history_low_weight_only", result["no_bet_reasons"])

    def test_37_umpire_context_modifies_only_if_supplied(self):
        missing = evaluate_baseball_matchup_context({"umpire_name": "sample_ump"})
        supplied = evaluate_baseball_matchup_context({"umpire_zone_size_proxy": 1.08, "umpire_k_rate_proxy": 0.26})
        self.assertFalse(missing["umpire_context_used"])
        self.assertTrue(supplied["umpire_context_used"])


class TestBaseballLineupBullpen(unittest.TestCase):
    def test_38_confirmed_lineup_raises_lineup_confidence(self):
        unconfirmed = evaluate_baseball_lineup_context(_lineup_context(confirmed_lineup=False))
        confirmed = evaluate_baseball_lineup_context(_lineup_context(confirmed_lineup=True))
        self.assertGreater(confirmed["lineup_stability_score"], unconfirmed["lineup_stability_score"])

    def test_39_unconfirmed_lineup_caps_batter_prop_confidence(self):
        result = evaluate_baseball_lineup_context(_lineup_context(confirmed_lineup=False))
        self.assertIn("unconfirmed_lineup_caps_batter_prop_confidence", result["no_bet_reasons"])

    def test_40_lineup_slot_affects_pa_projection(self):
        first = evaluate_baseball_lineup_context(_lineup_context(lineup_slot=1))
        ninth = evaluate_baseball_lineup_context(_lineup_context(lineup_slot=9))
        self.assertGreater(first["plate_appearance_projection_confidence"], ninth["plate_appearance_projection_confidence"])

    def test_41_bullpen_freshness_affects_full_game_more_than_first_five(self):
        result = evaluate_baseball_bullpen_context(_bullpen_context(bullpen_recent_pitch_count=145, bullpen_recent_innings=10))
        self.assertGreaterEqual(result["first_five_vs_full_game_split"], 0)
        self.assertIn("full_game", result["full_game_market_modifier_context"])

    def test_42_missing_bullpen_availability_caps_full_game_confidence(self):
        result = evaluate_baseball_bullpen_context({"bullpen_era_proxy": 3.8})
        self.assertIn("closer_available", result["missing_inputs"])
        self.assertIn("bullpen_availability_missing_caps_full_game_confidence", result["no_bet_reasons"])


class TestBaseballParkWeatherUmpire(unittest.TestCase):
    def test_43_park_factor_modifies_run_hr_environment_where_supplied(self):
        pitcher_park = evaluate_baseball_park_weather_umpire_context({"park_factor": 0.92, "home_run_factor": 0.88})
        hitter_park = evaluate_baseball_park_weather_umpire_context({"park_factor": 1.12, "home_run_factor": 1.18})
        self.assertGreater(hitter_park["home_run_environment_score"], pitcher_park["home_run_environment_score"])

    def test_44_wind_weather_modifies_hr_total_pitcher_props_with_uncertainty(self):
        result = evaluate_baseball_park_weather_umpire_context({"wind_speed": 18, "wind_direction": "out", "temperature": 84})
        self.assertGreater(result["weather_run_modifier"], 50)
        self.assertLess(result["pitcher_prop_weather_modifier"], 50)

    def test_45_roof_status_reduces_weather_uncertainty(self):
        result = evaluate_baseball_park_weather_umpire_context({"roof_status": "closed", "wind_speed": 20, "precipitation_risk": 0.8})
        self.assertTrue(result["roof_weather_uncertainty_reduced"])

    def test_46_umpire_zone_tendency_affects_k_walk_total_when_supplied(self):
        result = evaluate_baseball_park_weather_umpire_context({"umpire_zone_size_proxy": 1.08, "umpire_k_rate_proxy": 0.27, "umpire_walk_rate_proxy": 0.06})
        self.assertGreater(result["umpire_zone_modifier"], 1.0)

    def test_47_missing_umpire_data_does_not_fabricate_tendency(self):
        result = evaluate_baseball_park_weather_umpire_context({"umpire_name": "sample_ump"})
        self.assertTrue(result["umpire_tendency_fabricated"] is False)
        self.assertIn("umpire_name_without_tendency_data_no_zone_claim", result["no_bet_reasons"])

    def test_48_weather_delay_risk_downgrades_pitcher_props(self):
        result = evaluate_baseball_availability_context({"weather_delay_risk": 80, "confirmed_starter": True})
        self.assertIn("weather_delay_breaks_pitcher_prop_confidence", result["no_bet_reasons"])


class TestBaseballDefenseBaserunning(unittest.TestCase):
    def test_49_defense_modifies_pitcher_team_context_where_supplied(self):
        weak = evaluate_baseball_defense_baserunning_context({"outs_above_average_proxy": -8})
        strong = evaluate_baseball_defense_baserunning_context({"outs_above_average_proxy": 12})
        self.assertGreater(strong["pitcher_support_modifier"], weak["pitcher_support_modifier"])

    def test_50_oaa_style_fielding_proxy_works_where_supplied(self):
        result = evaluate_baseball_defense_baserunning_context({"outs_above_average_proxy": 10})
        self.assertGreater(result["defense_impact_score"], 50)

    def test_51_catcher_pop_framing_context_works_where_supplied(self):
        result = evaluate_baseball_defense_baserunning_context({"catcher_pop_time_proxy": 1.86, "catcher_framing_proxy": 6})
        self.assertGreater(result["catcher_run_prevention_score"], 50)

    def test_52_missing_catcher_metrics_does_not_fail(self):
        result = evaluate_baseball_defense_baserunning_context({"outs_above_average_proxy": 2})
        self.assertTrue(result["ok"] if "ok" in result else True)
        self.assertIn("catcher_pop_time_proxy", result["missing_inputs"])

    def test_53_stolen_base_context_uses_runner_pitcher_catcher_factors(self):
        result = evaluate_baseball_defense_baserunning_context({
            "sprint_speed": 29.5,
            "stolen_base_attempt_rate": 0.13,
            "stolen_base_success_rate": 0.82,
            "pitcher_hold_runner_score": 30,
            "catcher_pop_time_proxy": 2.05,
        })
        self.assertGreater(result["stolen_base_relevance_score"], 40)


class TestBaseballAvailabilityIncentive(unittest.TestCase):
    def test_54_injury_uncertainty_caps_confidence(self):
        result = evaluate_baseball_availability_context({"player_injury_status": "questionable"})
        self.assertIn("injury_uncertainty_caps_confidence", result["confidence_cap_reason"])

    def test_55_pitch_count_limit_creates_hard_warning(self):
        result = evaluate_baseball_availability_context({"confirmed_starter": True, "pitch_count_limit": 68})
        self.assertIn("pitch_count_limit_caps_outs_and_strikeout_props", result["no_bet_reasons"])

    def test_56_doubleheader_day_game_after_night_game_creates_rest_risk(self):
        result = evaluate_baseball_availability_context({"doubleheader_context": True, "day_game_after_night_game": True})
        self.assertGreater(result["lineup_rest_risk_score"], 0)

    def test_57_incentive_context_is_modifier_only(self):
        result = evaluate_baseball_incentive_context({"contract_year": True, "award_race_context": 60})
        self.assertFalse(result["incentive_is_standalone_edge"])
        self.assertEqual(result["incentive_context_status"], "modifier_only")

    def test_58_missing_bonus_threshold_does_not_fabricate_value(self):
        result = evaluate_baseball_incentive_context({"contract_year": True})
        self.assertFalse(result["bonus_threshold_fabricated"])
        self.assertIn("known_bonus_thresholds", result["missing_inputs"])

    def test_59_narrative_overfit_risk_downgrades_weak_incentive_claims(self):
        result = evaluate_baseball_incentive_context({"revenge_narrative_context": True})
        self.assertEqual(result["narrative_overfit_risk"], "high")
        self.assertIn("weak_incentive_evidence_narrative_overfit_risk", result["no_bet_reasons"])


class TestBaseballMarketRelevance(unittest.TestCase):
    def _market_bundle(self, market_type):
        return evaluate_baseball_market_relevance(
            market_type=market_type,
            pitcher_impact=evaluate_baseball_pitcher_impact(_pitcher_context()),
            batter_impact=evaluate_baseball_batter_impact(_batter_context()),
            matchup_context=evaluate_baseball_matchup_context({"pitcher_k_rate": 0.31, "opponent_k_rate": 0.26, "pitcher_hr_rate": 0.05, "team_barrel_rate": 0.12}),
            lineup_context=evaluate_baseball_lineup_context(_lineup_context()),
            bullpen_context=evaluate_baseball_bullpen_context(_bullpen_context()),
            park_weather_umpire_context=evaluate_baseball_park_weather_umpire_context({**_park_weather_context(), **_umpire_context()}),
            defense_baserunning_context=evaluate_baseball_defense_baserunning_context({
                "outs_above_average_proxy": 8,
                "catcher_pop_time_proxy": 1.9,
                "catcher_framing_proxy": 5,
                "sprint_speed": 29,
                "stolen_base_attempt_rate": 0.12,
                "pitcher_hold_runner_score": 35,
            }),
            availability_context=evaluate_baseball_availability_context({"confirmed_starter": True, "rest_days": 5}),
        )

    def test_60_pitcher_strikeout_relevance_links_core_factors(self):
        result = self._market_bundle("pitcher_strikeouts")
        self.assertIn("pitcher_strikeouts", result["pitcher_prop_relevance"])
        self.assertGreater(result["market_relevance_scores"]["pitcher_strikeouts"], 0)

    def test_61_pitcher_outs_relevance_links_workload_efficiency_weather_bullpen(self):
        result = self._market_bundle("pitcher_outs_recorded")
        self.assertIn("pitcher_outs_recorded", result["pitcher_prop_relevance"])
        self.assertGreater(result["selected_market_relevance_score"], 0)

    def test_62_batter_hit_relevance_links_pa_contact_platoon(self):
        result = self._market_bundle("batter_hits")
        self.assertIn("batter_hits", result["batter_prop_relevance"])
        self.assertGreater(result["market_relevance_scores"]["batter_hits"], 0)

    def test_63_total_bases_hr_relevance_links_barrel_park_weather_pitcher_hr(self):
        result = self._market_bundle("batter_home_runs")
        self.assertIn("batter_home_runs", result["batter_prop_relevance"])
        self.assertGreater(result["market_relevance_scores"]["batter_home_runs"], 0)

    def test_64_stolen_base_relevance_links_runner_pitcher_catcher_game_context(self):
        result = self._market_bundle("batter_stolen_bases")
        self.assertIn("batter_stolen_bases", result["batter_prop_relevance"])
        self.assertGreaterEqual(result["market_relevance_scores"]["batter_stolen_bases"], 0)

    def test_65_moneyline_runline_relevance_links_starter_bullpen_lineup_defense(self):
        result = self._market_bundle("moneyline")
        self.assertIn("moneyline", result["team_market_relevance"])
        self.assertGreater(result["market_relevance_scores"]["moneyline"], 0)

    def test_66_first_five_relevance_separates_starter_from_bullpen(self):
        result = self._market_bundle("first_five_moneyline")
        self.assertIn("first_five_moneyline", result["team_market_relevance"])
        self.assertGreater(result["market_relevance_scores"]["first_five_moneyline"], 0)

    def test_67_total_team_total_relevance_links_run_environment(self):
        result = self._market_bundle("total")
        self.assertIn("total", result["team_market_relevance"])
        self.assertGreater(result["market_relevance_scores"]["total"], 0)


class TestBaseballCalibration(unittest.TestCase):
    def test_68_no_labeled_outcomes_returns_insufficient_data(self):
        result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 0}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=2)
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_69_low_sample_returns_insufficient_sample(self):
        result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 12, "settled_outcomes": [1, 0, 1]}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=2)
        self.assertTrue(result["insufficient_sample"])

    def test_70_real_labeled_outcomes_enable_partial_calibration(self):
        result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 35, "settled_outcomes": [1, 0, 1, 1]}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=3)
        self.assertEqual(result["calibration_status"], "partial_calibration")

    def test_71_roi_not_emitted_without_real_returns(self):
        result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 35, "settled_outcomes": [1, 0]}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=3)
        self.assertNotIn("roi_proxy", result)

    def test_72_clv_not_emitted_without_real_open_close_prices(self):
        result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 35, "settled_outcomes": [1, 0]}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=3)
        self.assertNotIn("clv_proxy", result)

    def test_73_slippage_not_emitted_without_real_fill_entry_data(self):
        result = evaluate_baseball_impact_calibration({"matched_outcomes_count": 35, "settled_outcomes": [1, 0]}, sport="baseball_mlb", market_type="total", role="TEAM_OFFENSE", data_tier=3)
        self.assertNotIn("slippage_proxy", result)

    def test_74_context_buckets_are_preserved(self):
        result = evaluate_baseball_impact_calibration(
            {"matched_outcomes_count": 35, "settled_outcomes": [1, 0], "park_weather_bucket": "wind_out", "umpire_bucket": "large_zone"},
            sport="baseball_mlb",
            market_type="total",
            role="TEAM_OFFENSE",
            data_tier=3,
        )
        self.assertEqual(result["calibration_buckets"]["weather_bucket"], "wind_out")
        self.assertEqual(result["calibration_buckets"]["umpire_bucket"], "large_zone")


class TestBaseballRedTeam(unittest.TestCase):
    def _red_team(self, **source):
        return evaluate_baseball_impact_red_team(
            data_availability=evaluate_baseball_data_availability("baseball_mlb"),
            run_value_impact={"run_value_score": 70, "insufficient_sample": source.get("insufficient_sample", False)},
            pitcher_impact={"no_bet_reasons": source.get("pitcher_no_bet", [])},
            batter_impact={"no_bet_reasons": source.get("batter_no_bet", [])},
            lineup_context={"no_bet_reasons": source.get("lineup_no_bet", [])},
            bullpen_context={"no_bet_reasons": source.get("bullpen_no_bet", [])},
            park_weather_umpire_context={"no_bet_reasons": source.get("park_no_bet", [])},
            availability_context={"no_bet_reasons": source.get("availability_no_bet", [])},
            incentive_context={"no_bet_reasons": source.get("incentive_no_bet", [])},
            calibration={"calibration_status": source.get("calibration_status", "insufficient_data")},
            source_payload=source,
        )

    def test_75_fake_statcast_claim_is_downgraded(self):
        result = self._red_team(claimed_metrics=["statcast"])
        self.assertIn("statcast_metric_missing_but_claimed", result["red_team_reasons"])

    def test_76_fake_pitch_tracking_claim_is_downgraded(self):
        result = self._red_team(claimed_metrics=["pitch_tracking"])
        self.assertIn("pitch_tracking_missing_but_claimed", result["red_team_reasons"])

    def test_77_fake_bat_tracking_claim_is_downgraded(self):
        result = self._red_team(claimed_metrics=["bat_tracking"])
        self.assertIn("bat_tracking_missing_but_claimed", result["red_team_reasons"])

    def test_78_missing_umpire_tendency_claim_is_downgraded(self):
        result = self._red_team(claimed_metrics=["umpire_tendency"])
        self.assertIn("umpire_tendency_missing_but_claimed", result["red_team_reasons"])

    def test_79_unconfirmed_lineup_overconfidence_is_downgraded(self):
        result = self._red_team(lineup_no_bet=["unconfirmed_lineup_caps_batter_prop_confidence"], overconfidence_flag=True)
        self.assertIn("lineup_unconfirmed_overconfidence", result["red_team_reasons"])

    def test_80_unconfirmed_starter_overconfidence_is_downgraded(self):
        result = self._red_team(pitcher_no_bet=["unconfirmed_starter_caps_pitcher_prop_and_first_five_confidence"], overconfidence_flag=True)
        self.assertIn("starter_unconfirmed_overconfidence", result["red_team_reasons"])

    def test_81_weather_delay_pitcher_prop_risk_is_downgraded(self):
        result = self._red_team(availability_no_bet=["weather_delay_breaks_pitcher_prop_confidence"])
        self.assertIn("weather_delay_pitcher_prop_risk", result["red_team_reasons"])

    def test_82_pitch_count_limit_ignored_is_downgraded(self):
        result = self._red_team(availability_no_bet=["pitch_count_limit_caps_outs_and_strikeout_props"], ignored_pitch_count_limit=True)
        self.assertIn("pitch_count_limit_ignored", result["red_team_reasons"])

    def test_83_small_sample_split_overfit_is_downgraded(self):
        result = self._red_team(split_sample_size=8, overconfidence_flag=True)
        self.assertIn("small_sample_split_overfit", result["red_team_reasons"])

    def test_84_batter_vs_pitcher_history_overfit_is_downgraded(self):
        result = self._red_team(batter_vs_pitcher_history_weight=0.7)
        self.assertIn("batter_vs_pitcher_history_overfit", result["red_team_reasons"])

    def test_85_first_five_full_game_context_confusion_is_downgraded(self):
        result = self._red_team(uses_bullpen_for_first_five=True)
        self.assertIn("first_five_full_game_context_confusion", result["red_team_reasons"])

    def test_86_calibration_missing_prevents_overconfident_active_review(self):
        result = _full_report(calibration_context={"matched_outcomes_count": 0})
        self.assertNotEqual(result["recommended_review_status"], "ACTIVE_REVIEW")
        self.assertIn("calibration_missing", result["red_team"]["red_team_reasons"])


class TestBaseballSafetyRegression(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_87_readiness_endpoint_returns_provider_write_false(self):
        payload = self.client.get("/api/automation/baseball-impact-readiness").json()
        self.assertEqual(payload["status"], "baseball_impact_readiness")
        self.assertFalse(payload["provider_write"])

    def test_88_diagnostics_endpoint_returns_execution_allowed_false(self):
        payload = self.client.post("/api/automation/baseball-impact-diagnostics", json={"dry_run": True, "sport": "baseball_mlb"}).json()
        self.assertFalse(payload["execution_allowed"])

    def test_89_dry_run_false_is_rejected_or_forced_safe(self):
        response = self.client.post("/api/automation/baseball-impact-diagnostics", json={"dry_run": False, "sport": "baseball_mlb"})
        self.assertEqual(response.status_code, 400)

    def test_90_no_order_payload_survives_compaction(self):
        compact = compact_baseball_impact_diagnostics_response({"order_payload": {"order": "drop"}, "status": "baseball_player_impact_complete"})
        self.assertNotIn("order_payload", str(compact))

    def test_91_no_bet_slip_survives_compaction(self):
        compact = compact_baseball_impact_diagnostics_response({"bet_slip": {"ticket": "drop"}, "status": "baseball_player_impact_complete"})
        self.assertNotIn("bet_slip", str(compact))

    def test_92_secrets_raw_payloads_are_redacted(self):
        payload = self.client.post(
            "/api/automation/baseball-impact-diagnostics?verbose=true&include_debug=true",
            json={"dry_run": True, "sport": "baseball_mlb", "game_context": {"api_key": "sk-test-secret", "raw_payload": {"x": 1}}},
        ).json()
        self.assertNotIn("sk-test-secret", str(payload))
        self.assertNotIn("'x': 1", str(payload))

    def test_93_ai_red_team_output_cannot_promote_execution(self):
        result = _full_report(game_context={"model_claims": ["EXECUTE", "PLACE_BET"], "overconfidence_flag": True})
        self.assertFalse(result["execution_allowed"])
        self.assertNotIn(result["recommended_review_status"], {"EXECUTE", "PLACE_BET", "AUTO_BET"})

    def test_94_health_endpoint_still_passes(self):
        response = self.client.get("/api/automation/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_95_security_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/security-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_96_strategy_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/strategy-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_97_advanced_red_team_endpoint_still_passes(self):
        response = self.client.get("/api/automation/advanced-red-team-report")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_98_extreme_randomness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/extreme-randomness-report")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_99_basketball_impact_endpoints_still_pass(self):
        readiness = self.client.get("/api/automation/basketball-player-impact-readiness")
        diagnostic = self.client.post("/api/automation/basketball-player-impact", json={"dry_run": True, "candidate": {"sport": "basketball_nba"}})
        self.assertEqual(readiness.status_code, 200)
        self.assertEqual(diagnostic.status_code, 200)

    def test_100_football_impact_endpoints_still_pass(self):
        readiness = self.client.get("/api/automation/football-impact-readiness")
        diagnostic = self.client.post("/api/automation/football-impact-diagnostics", json={"dry_run": True, "sport": "americanfootball_nfl"})
        self.assertEqual(readiness.status_code, 200)
        self.assertEqual(diagnostic.status_code, 200)

    def test_101_mlb_malformed_payload_does_not_500(self):
        response = self.client.post("/api/automation/baseball-impact-diagnostics", json={"dry_run": True, "sport": {"bad": "shape"}})
        self.assertNotEqual(response.status_code, 500)

    def test_102_limited_public_data_payload_returns_tier_1_or_2_without_fake_tracking(self):
        payload = self.client.post(
            "/api/automation/baseball-impact-diagnostics",
            json={
                "dry_run": True,
                "sport": "baseball_mlb",
                "market_type": "total",
                "team_context": {"runs_scored_per_game": 4.7, "runs_allowed_per_game": 4.2},
                "pitcher_context": {"confirmed_starter": True},
                "park_weather_context": {"roof_status": "closed"},
                "calibration_context": {"matched_outcomes_count": 0},
            },
        ).json()
        self.assertIn(payload["data_tier"], [1, 2])
        self.assertFalse(payload["tracking_level_allowed"])
        self.assertFalse(payload["pitcher_impact"]["pitch_tracking_inferred"])
        self.assertFalse(payload["batter_impact"]["bat_tracking_inferred"])

    def test_103_readiness_builder_contains_forbidden_features(self):
        result = build_baseball_impact_readiness()
        self.assertIn("automatic_betting", result["forbidden_features"])
        self.assertFalse(result["provider_write"])


if __name__ == "__main__":
    unittest.main()
