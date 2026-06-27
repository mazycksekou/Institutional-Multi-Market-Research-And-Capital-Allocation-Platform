import unittest

from fastapi.testclient import TestClient

from src.market_intelligence.response_compactor import compact_golf_impact_diagnostics_response, redact_and_limit_payload
from src.market_intelligence.sports import (
    build_golf_impact_diagnostics,
    build_golf_impact_readiness,
    evaluate_golf_approach_impact,
    evaluate_golf_availability_context,
    evaluate_golf_course_fit_context,
    evaluate_golf_data_availability,
    evaluate_golf_field_tournament_context,
    evaluate_golf_impact_calibration,
    evaluate_golf_impact_red_team,
    evaluate_golf_incentive_context,
    evaluate_golf_market_relevance,
    evaluate_golf_off_tee_impact,
    evaluate_golf_short_game_putting_context,
    evaluate_golf_strokes_gained_impact,
    evaluate_golf_weather_wave_context,
)
from tests.support.action_imports import app


def _tournament_context(**extra):
    row = {
        "tournament_name": "sample_event",
        "course_name": "sample_course",
        "field_size": 132,
        "cut_rule": "top_65_and_ties",
    }
    row.update(extra)
    return row


def _player_context(**extra):
    row = {
        "player_id": "sample_player",
        "player_name": "Sample Player",
        "world_ranking_proxy": 38,
        "recent_finish_proxy": 22,
        "basic_cut_history": 0.74,
    }
    row.update(extra)
    return row


def _sg_context(**extra):
    row = {
        "sg_total": 1.12,
        "sg_tee_to_green": 0.84,
        "sg_off_the_tee": 0.22,
        "sg_approach": 0.46,
        "sg_around_the_green": 0.08,
        "sg_putting": 0.28,
        "birdie_or_better_rate": 0.245,
        "bogey_avoidance_rate": 0.835,
        "cut_rate": 0.74,
        "volatility_proxy": 0.42,
        "sample_size": 36,
    }
    row.update(extra)
    return row


def _off_tee_context(**extra):
    row = {
        "sg_off_the_tee": 0.28,
        "driving_distance": 306,
        "driving_accuracy": 0.61,
        "driving_dispersion": 0.44,
        "fairways_hit_rate": 0.62,
        "penalty_off_tee_rate": 0.05,
        "course_fairway_width": "medium",
        "rough_difficulty": "above_average",
    }
    row.update(extra)
    return row


def _approach_context(**extra):
    row = {
        "sg_approach": 0.48,
        "greens_in_regulation_rate": 0.69,
        "proximity_total": 33,
        "proximity_150_175": 31,
        "proximity_175_200": 38,
        "long_iron_skill": 0.62,
        "wedge_skill": 0.58,
        "course_approach_distance_distribution": {"150_175": 0.34, "175_200": 0.28},
        "green_size": "small",
        "green_firmness": "firm",
    }
    row.update(extra)
    return row


def _short_game_context(**extra):
    row = {
        "sg_around_the_green": 0.12,
        "scrambling_rate": 0.64,
        "sand_save_rate": 0.56,
        "sg_putting": 0.18,
        "three_putt_avoidance": 0.965,
        "grass_type_fit": 0.58,
        "bermuda_putting_fit": 0.62,
        "putting_volatility": 0.44,
        "recent_putting_delta": 0.12,
        "long_term_putting_baseline": 0.05,
    }
    row.update(extra)
    return row


def _course_context(**extra):
    row = {
        "course_name": "sample_course",
        "course_length": 7420,
        "par": 72,
        "par_5_reachable_rate": 0.38,
        "fairway_width": "medium",
        "rough_difficulty": "above_average",
        "green_size": "small",
        "green_speed": "fast",
        "green_firmness": "firm",
        "grass_type": "bermuda",
        "bunker_density": "average",
        "water_hazard_density": "moderate",
        "wind_exposure": "moderate",
        "approach_distance_distribution": {"150_175": 0.34, "175_200": 0.28},
        "scoring_difficulty": 0.62,
        "course_history_results": {"starts": 4, "average_finish": 24},
        "comparable_course_results": {"starts": 8, "average_finish": 28},
    }
    row.update(extra)
    return row


def _weather_context(**extra):
    row = {
        "tee_time": "07:40",
        "tee_wave": "morning",
        "round_number": 1,
        "wind_speed": 12,
        "wind_gust": 18,
        "rain_probability": 0.25,
        "temperature": 78,
        "morning_wave_conditions": "slightly_better",
        "afternoon_wave_conditions": "windier",
        "weather_edge_by_wave": "morning",
        "delay_risk": 0.12,
        "wind_skill": 0.57,
        "bad_weather_skill": 0.55,
    }
    row.update(extra)
    return row


def _field_context(**extra):
    row = {
        "field_size": 132,
        "field_strength": 0.72,
        "world_ranking_field_strength_proxy": 0.74,
        "top_20_field_count": 18,
        "cut_rule": "top_65_and_ties",
        "major_championship": False,
        "travel_distance": 900,
        "previous_week_finish": 18,
        "consecutive_weeks_played": 2,
    }
    row.update(extra)
    return row


def _availability_context(**extra):
    row = {
        "injury_status": "healthy",
        "withdrawal_risk": 0.04,
        "travel_distance": 900,
        "time_zone_change": 1,
        "consecutive_weeks_played": 2,
        "previous_week_rounds_played": 4,
        "rest_days": 4,
    }
    row.update(extra)
    return row


def _incentive_context(**extra):
    row = {
        "fedex_cup_context": "playoff_position_relevant",
        "major_exemption_context": "not_applicable",
        "tour_card_status": "secure",
    }
    row.update(extra)
    return row


def _calibration_context(**extra):
    row = {
        "matched_outcomes_count": 0,
    }
    row.update(extra)
    return row


def _full_report(**overrides):
    payload = {
        "sport": "golf",
        "market_type": "top_20",
        "tournament_context": _tournament_context(),
        "player_context": _player_context(),
        "strokes_gained_context": _sg_context(),
        "off_tee_context": _off_tee_context(),
        "approach_context": _approach_context(),
        "around_green_context": _short_game_context(),
        "putting_context": _short_game_context(),
        "course_context": _course_context(),
        "weather_context": _weather_context(),
        "wave_context": _weather_context(),
        "field_context": _field_context(),
        "availability_context": _availability_context(),
        "incentive_context": _incentive_context(),
        "calibration_context": _calibration_context(),
    }
    payload.update(overrides)
    return build_golf_impact_diagnostics(**payload)


class TestGolfImpactIntelligence(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_001_golf_tier_0_returns_data_insufficient(self):
        report = build_golf_impact_diagnostics(sport="golf", market_type="make_cut")
        self.assertEqual(report["data_tier"], 0)
        self.assertEqual(report["recommended_review_status"], "DATA_INSUFFICIENT")

    def test_002_missing_sg_splits_does_not_fail(self):
        report = _full_report(strokes_gained_context={"sg_total": 0.8, "sample_size": 30})
        self.assertTrue(report["ok"])
        self.assertFalse(report["strokes_gained_impact"]["sg_splits_fabricated"])

    def test_003_missing_approach_buckets_does_not_fail(self):
        result = evaluate_golf_approach_impact({"sg_approach": 0.35}, course_fit_allowed=True)
        self.assertFalse(result["distance_bucket_fit_supported"])
        self.assertIn("approach_distance_bucket_fit_requires_player_and_course_buckets", result["no_bet_reasons"])

    def test_004_missing_course_architecture_does_not_fail(self):
        result = evaluate_golf_course_fit_context({})
        self.assertFalse(result["course_architecture_fabricated"])
        self.assertIn("course_name_missing_caps_course_fit", result["no_bet_reasons"])

    def test_005_missing_grass_fit_does_not_fail(self):
        result = evaluate_golf_short_game_putting_context({"sg_putting": 0.2})
        self.assertFalse(result["grass_fit_fabricated"])
        self.assertIn("grass_fit_requires_grass_specific_history", result["no_bet_reasons"])

    def test_006_missing_tee_time_wave_does_not_fail(self):
        result = evaluate_golf_weather_wave_context({"wind_speed": 12})
        self.assertFalse(result["tee_time_wave_fabricated"])
        self.assertIn("tee_time_wave_missing_no_wave_draw_claim", result["no_bet_reasons"])

    def test_007_missing_weather_wave_does_not_fail(self):
        result = evaluate_golf_weather_wave_context({"tee_wave": "morning", "wind_speed": 12})
        self.assertFalse(result["weather_wave_edge_fabricated"])

    def test_008_missing_field_strength_does_not_fail(self):
        result = evaluate_golf_field_tournament_context({"field_size": 144})
        self.assertIn("field_strength_missing_caps_outright_top_finish_confidence", result["no_bet_reasons"])

    def test_009_missing_injury_status_does_not_fail(self):
        result = evaluate_golf_availability_context({})
        self.assertFalse(result["injury_status_fabricated"])
        self.assertIn("injury_status", result["missing_inputs"])

    def test_010_tier_1_basic_data_caps_confidence(self):
        availability = evaluate_golf_data_availability(
            sport="golf",
            market_type="make_cut",
            tournament_context={"tournament_name": "sample"},
            player_context={"player_name": "Sample Player", "basic_cut_history": 0.7},
        )
        self.assertEqual(availability["data_tier"], 1)
        self.assertLessEqual(availability["confidence_cap"], 42.0)

    def test_011_tier_2_sg_summary_enables_limited_diagnostics(self):
        availability = evaluate_golf_data_availability(
            sport="golf",
            market_type="top_20",
            tournament_context=_tournament_context(),
            player_context=_player_context(),
            strokes_gained_context={"sg_total": 0.9, "sample_size": 24},
        )
        self.assertEqual(availability["data_tier"], 2)
        self.assertTrue(availability["player_level_allowed"])

    def test_012_tier_3_course_weather_field_data_enables_stronger_diagnostics(self):
        availability = evaluate_golf_data_availability(
            sport="golf",
            market_type="top_20",
            tournament_context=_tournament_context(),
            player_context=_player_context(),
            strokes_gained_context=_sg_context(),
            course_context=_course_context(),
            weather_context=_weather_context(),
            field_context=_field_context(),
        )
        self.assertGreaterEqual(availability["data_tier"], 3)
        self.assertTrue(availability["course_fit_allowed"])

    def test_013_tier_4_simulation_tracking_optional(self):
        availability = evaluate_golf_data_availability(
            sport="golf",
            market_type="tournament_matchup",
            tournament_context=_tournament_context(),
            player_context=_player_context(),
            simulation_context={"player_volatility_distribution": [1, 2, 3]},
        )
        self.assertEqual(availability["data_tier"], 4)
        self.assertTrue(availability["simulation_allowed"])

    def test_014_sg_total_affects_impact_score(self):
        high = evaluate_golf_strokes_gained_impact({"sg_total": 1.2, "sample_size": 40})
        low = evaluate_golf_strokes_gained_impact({"sg_total": -0.6, "sample_size": 40})
        self.assertGreater(high["strokes_gained_score"], low["strokes_gained_score"])

    def test_015_sg_tee_to_green_affects_stability(self):
        result = evaluate_golf_strokes_gained_impact({"sg_tee_to_green": 1.0, "sample_size": 40})
        self.assertGreater(result["tee_to_green_score"], 70)

    def test_016_sg_approach_affects_course_market_relevance(self):
        result = evaluate_golf_approach_impact({"sg_approach": 0.7}, course_fit_allowed=True)
        self.assertGreater(result["approach_score"], 75)

    def test_017_sg_putting_affects_score_but_volatility_capped(self):
        result = evaluate_golf_strokes_gained_impact({"sg_putting": 0.9, "putting_volatility": 0.8, "sample_size": 40})
        self.assertGreater(result["putting_score"], 70)
        self.assertGreater(result["volatility_score"], 50)

    def test_018_recent_putting_spike_is_caution(self):
        result = evaluate_golf_short_game_putting_context({"sg_putting": 0.7, "recent_putting_delta": 0.8, "long_term_putting_baseline": 0.0})
        self.assertIn("recent_putting_spike_volatility_warning", result["no_bet_reasons"])

    def test_019_recent_form_does_not_dominate_long_term_baseline(self):
        result = evaluate_golf_strokes_gained_impact({"recent_sg_total": 2.0, "long_term_sg_total": 0.1, "sample_size": 24})
        self.assertLess(result["recent_vs_baseline_delta"], 2.0)

    def test_020_scoring_average_creates_limited_proxy_only(self):
        result = evaluate_golf_strokes_gained_impact({"scoring_average": 69.8, "sample_size": 20})
        self.assertTrue(result["limited_proxy"])
        self.assertIn("strokes_gained_missing_scoring_average_limited_proxy", result["confidence_cap_reason"])

    def test_021_small_sample_flags_insufficient_sample(self):
        result = evaluate_golf_strokes_gained_impact({"sg_total": 1.0, "sample_size": 6})
        self.assertTrue(result["insufficient_sample"])

    def test_022_cut_rate_profile_affects_cut_markets(self):
        result = evaluate_golf_strokes_gained_impact({"cut_rate": 0.82, "sample_size": 50})
        self.assertGreater(result["cut_made_profile_score"], 70)

    def test_023_distance_affects_off_tee_score(self):
        high = evaluate_golf_off_tee_impact({"driving_distance": 320}, course_fit_allowed=True)
        low = evaluate_golf_off_tee_impact({"driving_distance": 275}, course_fit_allowed=True)
        self.assertGreater(high["distance_advantage_score"], low["distance_advantage_score"])

    def test_024_accuracy_affects_off_tee_score(self):
        high = evaluate_golf_off_tee_impact({"driving_accuracy": 0.72}, course_fit_allowed=True)
        low = evaluate_golf_off_tee_impact({"driving_accuracy": 0.48}, course_fit_allowed=True)
        self.assertGreater(high["accuracy_score"], low["accuracy_score"])

    def test_025_dispersion_works_only_if_supplied(self):
        result = evaluate_golf_off_tee_impact({"driving_accuracy": 0.70}, course_fit_allowed=True)
        self.assertFalse(result["dispersion_inferred"])
        self.assertIn("driving_dispersion", result["missing_inputs"])

    def test_026_narrow_course_reduces_pure_distance_confidence(self):
        result = evaluate_golf_off_tee_impact({"driving_distance": 318, "course_fairway_width": "narrow"}, course_fit_allowed=True)
        self.assertIn("narrow_course_reduces_pure_distance_confidence", result["no_bet_reasons"])

    def test_027_rough_difficulty_modifies_distance_advantage(self):
        wide = evaluate_golf_off_tee_impact({"driving_distance": 318, "rough_difficulty": "low"}, course_fit_allowed=True)
        penal = evaluate_golf_off_tee_impact({"driving_distance": 318, "rough_difficulty": "very_penal"}, course_fit_allowed=True)
        self.assertLess(penal["course_off_tee_fit_score"], wide["course_off_tee_fit_score"])

    def test_028_missing_course_architecture_caps_off_tee_course_fit(self):
        result = evaluate_golf_off_tee_impact({"driving_distance": 318}, course_fit_allowed=False)
        self.assertTrue(result["course_fit_confidence_capped"])

    def test_029_sg_approach_affects_approach_score(self):
        result = evaluate_golf_approach_impact({"sg_approach": 0.55}, course_fit_allowed=True)
        self.assertGreater(result["approach_score"], 70)

    def test_030_gir_alone_does_not_fabricate_sg_approach(self):
        result = evaluate_golf_approach_impact({"greens_in_regulation_rate": 0.70}, course_fit_allowed=True)
        self.assertFalse(result["sg_approach_fabricated"])
        self.assertIn("gir_alone_does_not_fabricate_sg_approach", result["no_bet_reasons"])

    def test_031_distance_buckets_require_player_and_course_fields(self):
        result = evaluate_golf_approach_impact({"proximity_150_175": 30}, course_fit_allowed=True)
        self.assertFalse(result["distance_bucket_fit_supported"])

    def test_032_long_iron_fit_works_where_supplied(self):
        result = evaluate_golf_approach_impact({"long_iron_skill": 0.72, "course_approach_distance_distribution": {"175_200": 0.4, "200_plus": 0.2}}, course_fit_allowed=True)
        self.assertGreater(result["distance_bucket_fit_score"], 50)

    def test_033_wedge_fit_works_where_supplied(self):
        result = evaluate_golf_approach_impact({"wedge_skill": 0.74, "course_approach_distance_distribution": {"50_125": 0.5}}, course_fit_allowed=True)
        self.assertGreater(result["distance_bucket_fit_score"], 50)

    def test_034_green_size_firmness_modifies_approach_confidence(self):
        result = evaluate_golf_approach_impact({"sg_approach": 0.4, "green_size": "small", "green_firmness": "firm"}, course_fit_allowed=True)
        self.assertIn("firm_green_or_wind_context_caps_approach_confidence", result["no_bet_reasons"])

    def test_035_wind_adjusted_approach_works_only_when_supplied(self):
        result = evaluate_golf_approach_impact({"sg_approach": 0.4}, course_fit_allowed=True)
        self.assertIn("wind_adjusted_approach_skill", result["missing_inputs"])

    def test_036_scrambling_affects_score_save_modifier(self):
        result = evaluate_golf_short_game_putting_context({"scrambling_rate": 0.68})
        self.assertGreater(result["scrambling_score"], 60)

    def test_037_bunker_sand_save_works_where_supplied(self):
        result = evaluate_golf_short_game_putting_context({"sand_save_rate": 0.62})
        self.assertGreater(result["bunker_score"], 60)

    def test_038_sg_putting_works_where_supplied(self):
        result = evaluate_golf_short_game_putting_context({"sg_putting": 0.35})
        self.assertGreater(result["putting_score"], 60)

    def test_039_putts_alone_do_not_fabricate_sg_putting(self):
        result = evaluate_golf_short_game_putting_context({"putts_per_round": 28.1})
        self.assertFalse(result["sg_putting_fabricated"])
        self.assertIn("putts_alone_do_not_fabricate_sg_putting", result["no_bet_reasons"])

    def test_040_grass_specific_putting_requires_supply(self):
        result = evaluate_golf_short_game_putting_context({"sg_putting": 0.1})
        self.assertIn("grass_fit_requires_grass_specific_history", result["no_bet_reasons"])

    def test_041_three_putt_risk_affects_putting_props(self):
        result = evaluate_golf_short_game_putting_context({"three_putt_avoidance": 0.82})
        self.assertGreater(result["three_putt_risk_score"], 50)

    def test_042_recent_putting_volatility_downgrades_overconfidence(self):
        result = evaluate_golf_short_game_putting_context({"putting_volatility": 0.9})
        self.assertGreater(result["putting_volatility_score"], 60)

    def test_043_course_length_affects_fit(self):
        result = evaluate_golf_course_fit_context({"course_length": 7600, "par": 72})
        self.assertGreaterEqual(result["architecture_fit_score"], 0)

    def test_044_par5_reachable_affects_birdie_eagle_relevance(self):
        result = evaluate_golf_course_fit_context({"par_5_reachable_rate": 0.55})
        self.assertGreater(result["distance_bucket_fit_score"], 50)

    def test_045_fairway_width_rough_difficulty_affects_driving_fit(self):
        result = evaluate_golf_course_fit_context({"fairway_width": "narrow", "rough_difficulty": "very_penal"})
        self.assertGreater(result["hazard_risk_score"], 50)

    def test_046_green_speed_grass_affects_putting_context_when_supplied(self):
        result = evaluate_golf_course_fit_context({"green_speed": "fast", "grass_type": "bermuda"})
        self.assertGreater(result["grass_surface_fit_score"], 0)

    def test_047_course_history_is_supportive_but_capped(self):
        result = evaluate_golf_course_fit_context({"course_history_results": {"starts": 2, "average_finish": 5}})
        self.assertIn("course_history_small_sample_capped", result["no_bet_reasons"])

    def test_048_comparable_course_history_is_capped_if_sample_low(self):
        result = evaluate_golf_course_fit_context({"comparable_course_results": {"starts": 2, "average_finish": 8}})
        self.assertIn("comparable_course_history_small_sample_capped", result["no_bet_reasons"])

    def test_049_course_debut_increases_uncertainty(self):
        result = evaluate_golf_course_fit_context({"course_debut_flag": True, "course_length": 7300})
        self.assertIn("course_debut_increases_uncertainty", result["no_bet_reasons"])

    def test_050_missing_architecture_does_not_fabricate_course_fit(self):
        result = evaluate_golf_course_fit_context({})
        self.assertFalse(result["course_architecture_fabricated"])

    def test_051_tee_time_wave_works_where_supplied(self):
        result = evaluate_golf_weather_wave_context({"tee_wave": "morning", "weather_edge_by_wave": "morning"})
        self.assertGreater(result["wave_draw_score"], 50)

    def test_052_missing_tee_time_wave_does_not_fabricate_draw(self):
        result = evaluate_golf_weather_wave_context({"wind_speed": 10})
        self.assertFalse(result["tee_time_wave_fabricated"])

    def test_053_wind_speed_gust_affects_relevance(self):
        calm = evaluate_golf_weather_wave_context({"wind_speed": 4, "wind_gust": 8})
        windy = evaluate_golf_weather_wave_context({"wind_speed": 18, "wind_gust": 28})
        self.assertNotEqual(windy["weather_impact_score"], calm["weather_impact_score"])

    def test_054_weather_by_wave_creates_modifier_only_if_supplied(self):
        result = evaluate_golf_weather_wave_context({"tee_wave": "afternoon", "weather_edge_by_wave": "afternoon"})
        self.assertGreater(result["wave_draw_score"], 50)

    def test_055_delay_suspension_risk_increases_volatility(self):
        result = evaluate_golf_weather_wave_context({"delay_risk": 0.6, "suspension_risk": 0.4})
        self.assertGreater(result["delay_risk_score"], 50)

    def test_056_wind_skill_requires_supplied_evidence(self):
        result = evaluate_golf_weather_wave_context({"wind_speed": 18})
        self.assertFalse(result["wind_skill_fabricated"])
        self.assertIn("wind_skill", result["missing_inputs"])

    def test_057_field_strength_affects_outright_top_finish_confidence(self):
        weak = evaluate_golf_field_tournament_context({"field_strength": 0.25})
        strong = evaluate_golf_field_tournament_context({"field_strength": 0.85})
        self.assertGreater(strong["field_strength_score"], weak["field_strength_score"])

    def test_058_cut_rule_affects_cut_market_logic(self):
        result = evaluate_golf_field_tournament_context({"cut_rule": "top_65_and_ties"})
        self.assertGreater(result["cut_rule_context_score"], 50)

    def test_059_no_cut_event_disables_cut_logic(self):
        report = _full_report(market_type="make_cut", field_context=_field_context(no_cut_event=True))
        self.assertEqual(report["recommended_review_status"], "NO_BET")
        self.assertIn("no_cut_event_disables_make_miss_cut_logic", report["no_bet_reasons"])

    def test_060_unsupported_formats_return_safe_data_insufficient(self):
        report = _full_report(market_type="top_20", field_context=_field_context(match_play_event=True))
        self.assertEqual(report["recommended_review_status"], "DATA_INSUFFICIENT")

    def test_061_travel_consecutive_starts_affect_volatility(self):
        result = evaluate_golf_field_tournament_context({"travel_distance": 2500, "consecutive_weeks_played": 5})
        self.assertGreater(result["travel_fatigue_risk_score"], 50)

    def test_062_previous_week_contention_affects_fatigue(self):
        result = evaluate_golf_availability_context({"previous_week_contention": True, "previous_week_rounds_played": 4})
        self.assertGreater(result["schedule_load_score"], 20)

    def test_063_injury_uncertainty_caps_all_markets(self):
        result = evaluate_golf_availability_context({"injury_status": "questionable"})
        self.assertEqual(result["confidence_cap_reason"], "injury_uncertainty_caps_all_markets")

    def test_064_withdrawal_risk_creates_hard_warning(self):
        result = evaluate_golf_availability_context({"withdrawal_risk": 0.75})
        self.assertIn("withdrawal_risk_hard_warning", result["no_bet_reasons"])

    def test_065_swing_equipment_caddie_change_is_uncertainty_modifier(self):
        result = evaluate_golf_availability_context({"swing_change_context": True, "equipment_change_context": True, "caddie_change_context": True})
        self.assertGreater(result["change_uncertainty_score"], 40)

    def test_066_incentive_context_is_modifier_only(self):
        result = evaluate_golf_incentive_context({"fedex_cup_context": "bubble"})
        self.assertFalse(result["incentive_is_standalone_edge"])

    def test_067_missing_motivation_does_not_fabricate(self):
        result = evaluate_golf_incentive_context({})
        self.assertFalse(result["motivation_fabricated"])

    def test_068_tour_card_season_race_modifies_only_when_supplied(self):
        result = evaluate_golf_incentive_context({"tour_card_status": "bubble", "fedex_cup_context": "bubble"})
        self.assertGreater(result["incentive_behavior_score"], 0)

    def test_069_tuneup_context_lowers_confidence(self):
        result = evaluate_golf_incentive_context({"tune_up_event_context": True})
        self.assertIn("withdrawal_or_tuneup_risk_lowers_confidence", result["no_bet_reasons"])

    def test_070_outright_relevance_links_core_contexts(self):
        report = _full_report(market_type="outright_winner")
        self.assertIn("outright_winner", report["market_relevance"]["outright_relevance"])

    def test_071_top_finish_relevance_links_stability_course_cut(self):
        report = _full_report(market_type="top_20")
        self.assertIn("top_20", report["market_relevance"]["top_finish_relevance"])

    def test_072_make_cut_relevance_links_t2g_bogey_cut_history(self):
        report = _full_report(market_type="make_cut")
        self.assertIn("make_cut", report["market_relevance"]["cut_market_relevance"])

    def test_073_tournament_matchup_relevance_maps_relative_context(self):
        report = _full_report(market_type="tournament_matchup")
        self.assertIn("tournament_matchup", report["market_relevance"]["matchup_relevance"])

    def test_074_round_matchup_frl_links_weather_round_scoring(self):
        report = _full_report(market_type="first_round_leader", strokes_gained_context=_sg_context(round_1_scoring=68.9))
        self.assertIn("first_round_leader", report["market_relevance"]["round_market_relevance"])

    def test_075_round_score_links_scoring_course_weather(self):
        report = _full_report(market_type="round_score", strokes_gained_context=_sg_context(scoring_average=69.8))
        self.assertIn("round_score", report["market_relevance"]["round_market_relevance"])

    def test_076_birdies_bogeys_link_rates_and_par_scoring(self):
        report = _full_report(market_type="birdies_or_better")
        self.assertIn("birdies_or_better", report["market_relevance"]["player_prop_relevance"])

    def test_077_fairways_gir_driving_putting_props_map_to_skill_fields(self):
        report = _full_report(market_type="greens_in_regulation")
        props = report["market_relevance"]["player_prop_relevance"]
        self.assertIn("greens_in_regulation", props)
        self.assertIn("driving_distance", props)
        self.assertIn("putts", props)

    def test_078_outright_longshot_markets_calibration_capped(self):
        report = _full_report(market_type="outright_winner", calibration_context={"matched_outcomes_count": 0})
        self.assertIn("outright_winner", report["market_relevance"]["market_confidence_caps"])

    def test_079_no_labeled_outcomes_returns_insufficient_data(self):
        result = evaluate_golf_impact_calibration({"matched_outcomes_count": 0}, sport="golf", market_type="top_20", skill_group="COURSE_FIT", data_tier=3)
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_080_low_sample_returns_insufficient_sample(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": True}] * 12}, sport="golf", market_type="make_cut", skill_group="CUT_MADE_PROFILE", data_tier=3)
        self.assertTrue(result["insufficient_sample"])

    def test_081_real_labeled_outcomes_enable_partial_calibration(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": i % 2 == 0} for i in range(40)]}, sport="golf", market_type="make_cut", skill_group="CUT_MADE_PROFILE", data_tier=3)
        self.assertEqual(result["calibration_status"], "partial_calibration")

    def test_082_roi_not_emitted_without_real_returns(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": True}] * 40}, sport="golf", market_type="make_cut", skill_group="CUT_MADE_PROFILE", data_tier=3)
        self.assertNotIn("roi_proxy", result)

    def test_083_clv_not_emitted_without_open_close_prices(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": True}] * 40}, sport="golf", market_type="make_cut", skill_group="CUT_MADE_PROFILE", data_tier=3)
        self.assertNotIn("clv_proxy", result)

    def test_084_slippage_not_emitted_without_fill_entry_data(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": True}] * 40}, sport="golf", market_type="make_cut", skill_group="CUT_MADE_PROFILE", data_tier=3)
        self.assertNotIn("slippage_proxy", result)

    def test_085_outright_calibration_is_extra_conservative(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": False}] * 80}, sport="golf", market_type="outright_winner", skill_group="COURSE_FIT", data_tier=3)
        self.assertEqual(result["calibration_status"], "partial_calibration")
        self.assertTrue(result["outright_extra_conservative"])

    def test_086_placement_markets_have_separate_buckets(self):
        result = evaluate_golf_impact_calibration({"settled_outcomes": [{"hit": True}] * 60}, sport="golf", market_type="top_20", skill_group="COURSE_FIT", data_tier=3)
        self.assertTrue(result["placement_market_bucketed_separately"])

    def test_087_context_buckets_are_preserved(self):
        result = evaluate_golf_impact_calibration(
            {"settled_outcomes": [{"hit": True}] * 40, "course_fit_bucket": "long_penal", "weather_wave_bucket": "windy"},
            sport="golf",
            market_type="top_20",
            skill_group="COURSE_FIT",
            data_tier=3,
        )
        self.assertEqual(result["calibration_buckets"]["course_fit_bucket"], "long_penal")
        self.assertEqual(result["calibration_buckets"]["weather_wave_bucket"], "windy")

    def _red_team(self, source_payload=None, **sections):
        report = _full_report()
        args = {
            "data_availability": evaluate_golf_data_availability(sport="golf", market_type="top_20"),
            "strokes_gained_impact": report["strokes_gained_impact"],
            "approach_impact": report["approach_impact"],
            "course_fit_context": report["course_fit_context"],
            "weather_wave_context": report["weather_wave_context"],
            "field_tournament_context": report["field_tournament_context"],
            "availability_context": report["availability_context"],
            "calibration": report["calibration"],
            "market_type": "top_20",
            "source_payload": source_payload or {},
        }
        args.update(sections)
        return evaluate_golf_impact_red_team(**args)

    def test_088_fake_sg_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["strokes_gained"]}, strokes_gained_impact=evaluate_golf_strokes_gained_impact({}))
        self.assertIn("strokes_gained_missing_but_claimed", result["red_team_reasons"])

    def test_089_fake_sg_split_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["sg_split"]}, strokes_gained_impact=evaluate_golf_strokes_gained_impact({"sg_total": 0.5}))
        self.assertIn("sg_split_missing_but_claimed", result["red_team_reasons"])

    def test_090_fake_approach_bucket_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["approach_bucket"]}, approach_impact=evaluate_golf_approach_impact({"sg_approach": 0.3}))
        self.assertIn("approach_bucket_missing_but_claimed", result["red_team_reasons"])

    def test_091_fake_course_architecture_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["course_architecture"]}, course_fit_context=evaluate_golf_course_fit_context({}))
        self.assertIn("course_architecture_missing_but_claimed", result["red_team_reasons"])

    def test_092_fake_grass_fit_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["grass_fit"]}, course_fit_context=evaluate_golf_course_fit_context({}))
        self.assertIn("grass_fit_missing_but_claimed", result["red_team_reasons"])

    def test_093_fake_tee_time_wave_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["tee_time_wave"]}, weather_wave_context=evaluate_golf_weather_wave_context({}))
        self.assertIn("tee_time_wave_missing_but_claimed", result["red_team_reasons"])

    def test_094_fake_weather_wave_edge_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["weather_wave_edge"]}, weather_wave_context=evaluate_golf_weather_wave_context({"tee_wave": "morning"}))
        self.assertIn("weather_wave_edge_missing_but_claimed", result["red_team_reasons"])

    def test_095_fake_injury_status_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["injury"]}, availability_context=evaluate_golf_availability_context({}))
        self.assertIn("injury_status_missing_but_claimed", result["red_team_reasons"])

    def test_096_fake_field_strength_claim_is_downgraded(self):
        result = self._red_team(source_payload={"claimed_metrics": ["field_strength"]}, field_tournament_context=evaluate_golf_field_tournament_context({}))
        self.assertIn("field_strength_missing_but_claimed", result["red_team_reasons"])

    def test_097_putting_spike_overfit_is_downgraded(self):
        result = self._red_team(short_game_putting_context=evaluate_golf_short_game_putting_context({"sg_putting": 1.2, "recent_putting_delta": 1.4, "long_term_putting_baseline": 0.0}))
        self.assertIn("putting_spike_overfit", result["red_team_reasons"])

    def test_098_recent_form_overfit_is_downgraded(self):
        result = self._red_team(source_payload={"recent_form_weight": 0.5}, strokes_gained_impact=evaluate_golf_strokes_gained_impact({"recent_sg_total": 2.0, "long_term_sg_total": -0.2, "sample_size": 12}))
        self.assertIn("recent_form_overfit", result["red_team_reasons"])

    def test_099_course_history_overfit_is_downgraded(self):
        result = self._red_team(source_payload={"overconfidence_flag": True}, course_fit_context=evaluate_golf_course_fit_context({"course_history_results": {"starts": 2, "average_finish": 3}}))
        self.assertIn("course_history_overfit", result["red_team_reasons"])

    def test_100_comparable_course_overfit_is_downgraded(self):
        result = self._red_team(source_payload={"overconfidence_flag": True}, course_fit_context=evaluate_golf_course_fit_context({"comparable_course_results": {"starts": 2, "average_finish": 3}}))
        self.assertIn("comp_course_overfit", result["red_team_reasons"])

    def test_101_outright_longshot_overconfidence_is_downgraded(self):
        result = self._red_team(market_type="outright_winner", source_payload={"market_implied_probability": 0.01})
        self.assertIn("outright_longshot_overconfidence", result["red_team_reasons"])

    def test_102_frl_volatility_ignored_is_downgraded(self):
        result = self._red_team(market_type="first_round_leader", source_payload={"ignores_volatility": True}, strokes_gained_impact=evaluate_golf_strokes_gained_impact({"volatility_proxy": 0.9, "sample_size": 20}))
        self.assertIn("first_round_leader_volatility_ignored", result["red_team_reasons"])

    def test_103_withdrawal_risk_ignored_is_downgraded(self):
        result = self._red_team(source_payload={"ignores_withdrawal_risk": True}, availability_context=evaluate_golf_availability_context({"withdrawal_risk": 0.75}))
        self.assertIn("withdrawal_risk_ignored", result["red_team_reasons"])

    def test_104_cut_rule_context_confusion_is_downgraded(self):
        result = self._red_team(market_type="make_cut", field_tournament_context=evaluate_golf_field_tournament_context({"no_cut_event": True}))
        self.assertIn("cut_rule_context_confusion", result["red_team_reasons"])

    def test_105_calibration_missing_prevents_overconfident_active_review(self):
        report = _full_report(calibration_context={"matched_outcomes_count": 0})
        self.assertNotEqual(report["recommended_review_status"], "ACTIVE_REVIEW")
        self.assertIn("calibration_missing", report["red_team"]["red_team_reasons"])

    def test_106_readiness_endpoint_returns_provider_write_false(self):
        response = self.client.get("/api/automation/golf-impact-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_107_diagnostics_endpoint_returns_execution_allowed_false(self):
        response = self.client.post("/api/automation/golf-impact-diagnostics", json={"sport": "golf", "market_type": "top_20", "player_context": {"player_name": "A"}, "dry_run": True})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_108_dry_run_false_is_rejected(self):
        response = self.client.post("/api/automation/golf-impact-diagnostics", json={"sport": "golf", "market_type": "top_20", "dry_run": False})
        self.assertEqual(response.status_code, 400)

    def test_109_no_order_payload_survives_compaction(self):
        compact = compact_golf_impact_diagnostics_response({"status": "x", "order_payload": {"secret": "drop"}})
        self.assertNotIn("order_payload", str(compact))

    def test_110_no_bet_slip_survives_compaction(self):
        compact = compact_golf_impact_diagnostics_response({"status": "x", "bet_slip": {"pick": "drop"}})
        self.assertNotIn("bet_slip", str(compact))

    def test_111_secrets_raw_payloads_are_redacted(self):
        redacted = redact_and_limit_payload({"raw_payload": {"x": 1}, "api_key": "sk-test-secret", "safe": "ok"})
        self.assertNotIn("sk-test-secret", str(redacted))
        self.assertIn("[omitted]", str(redacted))

    def test_112_ai_red_team_output_cannot_promote_execution(self):
        result = self._red_team(source_payload={"recommended_action": "EXECUTE", "provider_write": True})
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["provider_write"])

    def test_113_health_endpoint_still_passes(self):
        response = self.client.get("/api/automation/health")
        self.assertEqual(response.status_code, 200)

    def test_114_security_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/security-readiness")
        self.assertEqual(response.status_code, 200)

    def test_115_strategy_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/strategy-readiness")
        self.assertEqual(response.status_code, 200)

    def test_116_advanced_red_team_endpoint_still_passes(self):
        response = self.client.get("/api/automation/advanced-red-team-report")
        self.assertEqual(response.status_code, 200)

    def test_117_extreme_randomness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/extreme-randomness-report")
        self.assertEqual(response.status_code, 200)

    def test_118_basketball_impact_endpoint_still_passes(self):
        response = self.client.get("/api/automation/basketball-player-impact-readiness")
        self.assertEqual(response.status_code, 200)

    def test_119_football_impact_endpoint_still_passes(self):
        response = self.client.get("/api/automation/football-impact-readiness")
        self.assertEqual(response.status_code, 200)

    def test_120_baseball_impact_endpoint_still_passes(self):
        response = self.client.get("/api/automation/baseball-impact-readiness")
        self.assertEqual(response.status_code, 200)

    def test_121_hockey_impact_endpoint_still_passes(self):
        response = self.client.get("/api/automation/hockey-impact-readiness")
        self.assertEqual(response.status_code, 200)

    def test_122_soccer_impact_endpoint_still_passes_if_present(self):
        response = self.client.get("/api/automation/soccer-impact-readiness")
        self.assertIn(response.status_code, {200, 404})
        if response.status_code == 200:
            self.assertFalse(response.json()["provider_write"])

    def test_123_golf_malformed_payload_does_not_500(self):
        response = self.client.post("/api/automation/golf-impact-diagnostics", json={"sport": {"bad": "type"}, "dry_run": True})
        self.assertNotEqual(response.status_code, 500)

    def test_124_limited_public_data_payload_returns_without_fake_claims(self):
        report = build_golf_impact_diagnostics(
            sport="golf",
            market_type="make_cut",
            tournament_context={"tournament_name": "sample_event", "field_size": 144},
            player_context={"player_name": "Sample Player", "recent_finish_proxy": 32, "basic_cut_history": 0.71},
            calibration_context={"matched_outcomes_count": 0},
        )
        self.assertIn(report["data_tier"], {1, 2})
        self.assertFalse(report["strokes_gained_impact"]["sg_splits_fabricated"])
        self.assertFalse(report["course_fit_context"]["course_architecture_fabricated"])
        self.assertFalse(report["weather_wave_context"]["tee_time_wave_fabricated"])

    def test_125_full_suite_anchor_readiness_shape(self):
        readiness = build_golf_impact_readiness()
        self.assertEqual(readiness["status"], "golf_impact_readiness")
        self.assertIn("outright_winner", readiness["supported_markets"])
        self.assertFalse(readiness["provider_write"])


if __name__ == "__main__":
    unittest.main()
