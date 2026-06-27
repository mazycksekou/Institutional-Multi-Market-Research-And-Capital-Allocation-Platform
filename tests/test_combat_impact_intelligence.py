import unittest

from fastapi.testclient import TestClient

from src.market_intelligence.response_compactor import compact_combat_impact_diagnostics_response, redact_and_limit_payload
from src.market_intelligence.sports import (
    build_combat_impact_diagnostics,
    evaluate_combat_availability_context,
    evaluate_combat_damage_durability_context,
    evaluate_combat_data_availability,
    evaluate_combat_grappling_control_impact,
    evaluate_combat_impact_calibration,
    evaluate_combat_impact_red_team,
    evaluate_combat_incentive_context,
    evaluate_combat_market_relevance,
    evaluate_combat_matchup_context,
    evaluate_combat_pace_cardio_context,
    evaluate_combat_phase_control_context,
    evaluate_combat_ruleset_referee_judging_context,
    evaluate_combat_striking_impact,
)
from tests.support.action_imports import app


def _bout(**extra):
    row = {"organization": "ufc", "weight_class": "lightweight", "scheduled_rounds": 3, "ruleset": "mma"}
    row.update(extra)
    return row


def _fa(**extra):
    row = {"fighter_id": "fighter_a", "fighter_name": "Sample Fighter A", "stance": "orthodox", "reach_inches": 72, "age": 30}
    row.update(extra)
    return row


def _fb(**extra):
    row = {"fighter_id": "fighter_b", "fighter_name": "Sample Fighter B", "stance": "southpaw", "reach_inches": 70, "age": 31}
    row.update(extra)
    return row


def _strike(**extra):
    row = {
        "fighter_a_significant_strikes_landed_per_minute": 4.6,
        "fighter_a_significant_strikes_absorbed_per_minute": 3.2,
        "fighter_a_striking_accuracy": 0.48,
        "fighter_a_striking_defense": 0.57,
        "fighter_a_knockdown_average": 0.32,
        "fighter_a_jab_rate": 28.5,
        "fighter_a_jab_accuracy": 0.31,
        "fighter_a_power_punch_rate": 18.2,
        "fighter_a_power_punch_accuracy": 0.42,
        "fighter_b_significant_strikes_landed_per_minute": 3.1,
        "fighter_b_significant_strikes_absorbed_per_minute": 4.0,
        "fighter_b_striking_accuracy": 0.42,
        "fighter_b_striking_defense": 0.51,
        "sample_size": 8,
    }
    row.update(extra)
    return row


def _grapple(**extra):
    row = {
        "fighter_a_takedowns_per_15": 2.1,
        "fighter_a_takedown_accuracy": 0.41,
        "fighter_a_takedown_attempts_per_15": 5.4,
        "fighter_b_takedown_defense": 0.64,
        "fighter_a_control_time_average": 4.8,
        "fighter_a_top_control_time": 3.1,
        "fighter_a_get_up_rate": 0.72,
        "fighter_a_scramble_success_rate": 0.58,
        "fighter_a_submission_attempts_per_15": 0.8,
        "fighter_a_submission_attempt_quality": 0.42,
        "fighter_b_submission_defense": 0.7,
        "sample_size": 8,
    }
    row.update(extra)
    return row


def _phase(**extra):
    row = {"open_space_striking_control": 0.58, "clinch_control": 0.52, "cage_wrestling_control": 0.55, "top_control_success": 0.52, "scramble_win_rate": 0.56}
    row.update(extra)
    return row


def _damage(**extra):
    row = {"fighter_a_knockdowns_landed": 1.2, "fighter_b_knockdowns_absorbed": 1.8, "fighter_b_head_strike_absorption_rate": 0.58, "fighter_b_cut_history": 0.4, "recent_damage_taken": 0.35}
    row.update(extra)
    return row


def _pace(**extra):
    row = {"average_fight_time": 12.4, "first_round_pace": 0.72, "second_round_pace": 0.66, "third_round_pace": 0.58, "output_decline_by_round": 0.22, "cardio_rating_proxy": 0.68}
    row.update(extra)
    return row


def _diag(market="method_of_victory", **extra):
    payload = {
        "sport": "ufc",
        "market_type": market,
        "bout_context": _bout(),
        "fighter_a_context": _fa(),
        "fighter_b_context": _fb(),
        "striking_context": _strike(),
        "grappling_context": _grapple(),
        "phase_context": _phase(),
        "damage_context": _damage(),
        "pace_cardio_context": _pace(),
        "calibration_context": {"matched_outcomes_count": 0},
    }
    payload.update(extra)
    return build_combat_impact_diagnostics(**payload)


class TestCombatDataAvailability(unittest.TestCase):
    def test_001_combat_tier_0_returns_data_insufficient(self):
        self.assertEqual(evaluate_combat_data_availability("mma")["status"], "DATA_INSUFFICIENT")

    def test_002_missing_phase_control_data_does_not_fail(self):
        result = _diag(phase_context={})
        self.assertFalse(result["phase_control_context"]["phase_control_fabricated"])

    def test_003_missing_punch_tracking_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_striking_impact(_strike(fighter_a_jab_rate=None))["punch_tracking_fabricated"])

    def test_004_missing_grappling_control_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_grappling_control_impact({"fighter_a_takedowns_per_15": 1.5})["control_time_fabricated"])

    def test_005_missing_durability_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_damage_durability_context({})["durability_fabricated"])

    def test_006_missing_injury_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_availability_context({})["injury_status_fabricated"])

    def test_007_missing_weight_cut_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_availability_context({})["weight_cut_fabricated"])

    def test_008_missing_camp_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_availability_context({})["camp_context_fabricated"])

    def test_009_missing_referee_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_ruleset_referee_judging_context({})["referee_tendency_fabricated"])

    def test_010_missing_judge_data_does_not_fail(self):
        self.assertFalse(evaluate_combat_ruleset_referee_judging_context({})["judge_tendency_fabricated"])

    def test_011_tier_1_basic_data_caps_confidence(self):
        result = evaluate_combat_data_availability("ufc", bout_context=_bout(), fighter_a_context=_fa(), fighter_b_context=_fb())
        self.assertEqual(result["data_tier"], 1)
        self.assertLessEqual(result["confidence_cap"], 42)

    def test_012_tier_2_summary_enables_limited_diagnostics(self):
        result = evaluate_combat_data_availability("mma", bout_context=_bout(), fighter_a_context=_fa(), fighter_b_context=_fb(), striking_context=_strike())
        self.assertEqual(result["data_tier"], 2)

    def test_013_tier_3_round_phase_enables_stronger_diagnostics(self):
        result = evaluate_combat_data_availability("ufc", bout_context=_bout(), fighter_a_context=_fa(), fighter_b_context=_fb(), phase_context=_phase())
        self.assertEqual(result["data_tier"], 3)

    def test_014_tier_4_film_optional(self):
        result = evaluate_combat_data_availability("boxing", bout_context=_bout(ruleset="boxing"), fighter_a_context=_fa(), fighter_b_context=_fb(), film_tracking_context={"film_tracking_available": True})
        self.assertEqual(result["data_tier"], 4)


class TestCombatStrikingGrapplingPhaseDamagePace(unittest.TestCase):
    def test_015_sig_strike_rate_affects_score(self):
        self.assertGreater(evaluate_combat_striking_impact(_strike(fighter_a_significant_strikes_landed_per_minute=6.0))["volume_score"], evaluate_combat_striking_impact(_strike(fighter_a_significant_strikes_landed_per_minute=1.0))["volume_score"])

    def test_016_strike_absorption_affects_damage_risk(self):
        self.assertGreater(evaluate_combat_striking_impact(_strike(fighter_a_significant_strikes_absorbed_per_minute=6.0))["damage_absorption_risk_score"], 40)

    def test_017_accuracy_affects_efficiency(self):
        self.assertGreater(evaluate_combat_striking_impact(_strike(fighter_a_striking_accuracy=0.65))["accuracy_score"], 50)

    def test_018_defense_affects_responsibility(self):
        self.assertGreater(evaluate_combat_striking_impact(_strike(fighter_a_striking_defense=0.72))["defense_score"], 50)

    def test_019_knockdown_average_sample_capped(self):
        result = evaluate_combat_striking_impact(_strike(fighter_a_knockdown_average=0.8, sample_size=3))
        self.assertTrue(result["insufficient_sample"])
        self.assertIn("knockdown_average_sample_capped", result["no_bet_reasons"])

    def test_020_boxing_jab_power_fields_work(self):
        self.assertGreater(evaluate_combat_striking_impact(_strike())["boxing_punch_profile_score"], 30)

    def test_021_missing_punch_tracking_not_fabricated(self):
        result = evaluate_combat_striking_impact({"fighter_a_significant_strikes_landed_per_minute": 3.0})
        self.assertFalse(result["punch_tracking_fabricated"])

    def test_022_limited_summary_striking_proxy_capped(self):
        self.assertTrue(evaluate_combat_striking_impact({"fighter_a_significant_strikes_landed_per_minute": 3.0})["limited_proxy"])

    def test_023_takedown_average_affects_grappling(self):
        self.assertGreater(evaluate_combat_grappling_control_impact(_grapple(fighter_a_takedowns_per_15=4.0))["takedown_threat_score"], 50)

    def test_024_takedown_defense_affects_anti_wrestling(self):
        self.assertGreater(evaluate_combat_grappling_control_impact(_grapple(fighter_b_takedown_defense=0.9))["takedown_defense_score"], 70)

    def test_025_control_time_affects_decision(self):
        self.assertGreater(evaluate_combat_grappling_control_impact(_grapple(fighter_a_control_time_average=8.0))["decision_relevance_modifier"], 30)

    def test_026_submission_attempts_affect_submission(self):
        self.assertGreater(evaluate_combat_grappling_control_impact(_grapple(fighter_a_submission_attempts_per_15=2.5))["submission_relevance_modifier"], 40)

    def test_027_get_up_scramble_works(self):
        self.assertGreater(evaluate_combat_grappling_control_impact(_grapple(fighter_a_scramble_success_rate=0.9))["scramble_score"], 60)

    def test_028_missing_control_time_no_fabrication(self):
        self.assertFalse(evaluate_combat_grappling_control_impact({"fighter_a_takedowns_per_15": 2.0})["control_time_fabricated"])

    def test_029_missing_submission_quality_no_fabrication(self):
        self.assertFalse(evaluate_combat_grappling_control_impact({"fighter_a_submission_attempts_per_15": 1.0})["submission_quality_fabricated"])

    def test_030_limited_takedown_proxy_capped(self):
        self.assertTrue(evaluate_combat_grappling_control_impact({"fighter_a_takedowns_per_15": 2.0})["limited_proxy"])

    def test_031_open_space_phase_works(self):
        self.assertIn("OPEN_SPACE_STRIKING", evaluate_combat_phase_control_context(_phase(open_space_striking_control=0.8))["fighter_a_phase_edges"])

    def test_032_clinch_cage_phase_works(self):
        result = evaluate_combat_phase_control_context(_phase(clinch_control=0.8, cage_wrestling_control=0.8))
        self.assertIn("clinch_or_cage_control_supported", result["phase_mismatch_reasons"])

    def test_033_top_bottom_scramble_phase_works(self):
        self.assertIn("top_bottom_scramble_phase_supported", evaluate_combat_phase_control_context(_phase(top_control_success=0.8))["phase_mismatch_reasons"])

    def test_034_preferred_phase_returned(self):
        self.assertNotEqual(evaluate_combat_phase_control_context(_phase(open_space_striking_control=0.9))["preferred_phase"], "UNKNOWN")

    def test_035_missing_phase_caps_confidence(self):
        self.assertIn("phase_control_missing_caps_advanced_confidence", evaluate_combat_phase_control_context({})["no_bet_reasons"])

    def test_036_phase_not_inferred_from_result(self):
        self.assertIn("phase_control_not_inferred_from_final_result", evaluate_combat_phase_control_context({"final_result": "ko"})["no_bet_reasons"])

    def test_037_knockdowns_absorbed_affect_durability(self):
        self.assertGreater(evaluate_combat_damage_durability_context(_damage(fighter_b_knockdowns_absorbed=3.0))["chin_risk_score"], 50)

    def test_038_head_body_leg_damage_fields_work(self):
        result = evaluate_combat_damage_durability_context(_damage(fighter_b_body_strike_absorption_rate=0.8, fighter_b_leg_kick_absorption_rate=0.7))
        self.assertGreater(result["body_damage_risk_score"], 50)
        self.assertGreater(result["leg_damage_risk_score"], 50)

    def test_039_cut_doctor_history_works(self):
        self.assertGreater(evaluate_combat_damage_durability_context(_damage(fighter_b_doctor_stoppage_history=0.8))["doctor_stoppage_risk_score"], 50)

    def test_040_recent_damage_caps_confidence(self):
        self.assertIn("recent_damage_context_caps_confidence", evaluate_combat_damage_durability_context(_damage(recent_damage_taken=0.8))["no_bet_reasons"])

    def test_041_chin_not_inferred_from_record(self):
        self.assertIn("chin_not_inferred_from_record_only", evaluate_combat_damage_durability_context({"ko_losses": 2})["no_bet_reasons"])

    def test_042_medical_suspension_not_fabricated(self):
        self.assertFalse(evaluate_combat_damage_durability_context({})["medical_suspension_fabricated"])

    def test_043_durability_missing_aware(self):
        self.assertIn("durability_data_missing_no_chin_certainty", evaluate_combat_damage_durability_context({})["no_bet_reasons"])

    def test_044_round_pace_works(self):
        self.assertGreater(evaluate_combat_pace_cardio_context(_pace(first_round_pace=0.9))["pace_score"], 50)

    def test_045_output_decline_late_risk(self):
        self.assertGreater(evaluate_combat_pace_cardio_context(_pace(output_decline_by_round=0.9))["late_fight_risk_score"], 30)

    def test_046_five_round_context_affects_cardio(self):
        self.assertGreaterEqual(evaluate_combat_pace_cardio_context(_pace(five_round_experience=3, five_round_performance=0.8))["five_round_readiness_score"], 50)

    def test_047_short_notice_affects_cardio(self):
        self.assertIn("short_notice_caps_cardio_confidence", evaluate_combat_pace_cardio_context(_pace(short_notice_flag=True))["no_bet_reasons"])

    def test_048_weight_cut_affects_cardio_only_if_supplied(self):
        self.assertIn("weight_cut_severity_caps_late_round_confidence", evaluate_combat_pace_cardio_context(_pace(weight_cut_severity=0.8))["no_bet_reasons"])

    def test_049_average_fight_time_not_cardio_alone(self):
        self.assertIn("average_fight_time_alone_does_not_infer_cardio", evaluate_combat_pace_cardio_context({"average_fight_time": 12})["no_bet_reasons"])

    def test_050_missing_round_decline_does_not_fail(self):
        self.assertFalse(evaluate_combat_pace_cardio_context({})["round_decline_fabricated"])


class TestCombatContextMarketCalibrationRedTeam(unittest.TestCase):
    def test_051_striker_vs_grappler_matchup(self):
        self.assertTrue(evaluate_combat_matchup_context({**_strike(), **_grapple()})["tactical_mismatch_reasons"])

    def test_052_wrestler_vs_takedown_defense(self):
        self.assertIn("wrestler_vs_takedown_defense", evaluate_combat_matchup_context(_grapple(fighter_a_takedowns_per_15=4.5))["tactical_mismatch_reasons"])

    def test_053_submission_hunter_vs_defense(self):
        self.assertIn("submission_hunter_vs_submission_defense", evaluate_combat_matchup_context(_grapple(fighter_a_submission_attempts_per_15=2.5))["tactical_mismatch_reasons"])

    def test_054_pressure_boxer_vs_counter(self):
        self.assertIn("pressure_boxer_vs_counter_striker", evaluate_combat_matchup_context({"fighter_a_pressure_striking_rate": 0.8, "fighter_b_counter_strike_rate": 0.7})["tactical_mismatch_reasons"])

    def test_055_southpaw_orthodox_context(self):
        self.assertIn("southpaw_orthodox_context_supported", evaluate_combat_matchup_context({**_fa(), **{"fighter_b_stance": "southpaw"}})["tactical_mismatch_reasons"])

    def test_056_reach_height_context(self):
        self.assertIn("reach_height_distance_management_context_supported", evaluate_combat_matchup_context({"fighter_a_reach_inches": 76, "fighter_b_reach_inches": 70})["tactical_mismatch_reasons"])

    def test_057_short_notice_pace_matchup(self):
        self.assertIn("short_notice_fighter_vs_pace_heavy_opponent", evaluate_combat_matchup_context({"short_notice_flag": True, "fighter_a_pressure_striking_rate": 0.8})["tactical_mismatch_reasons"])

    def test_058_missing_stance_reach_no_fabrication(self):
        result = evaluate_combat_matchup_context({})
        self.assertFalse(result["stance_fabricated"])
        self.assertFalse(result["reach_fabricated"])

    def test_059_conflicting_signals_reduce_confidence(self):
        self.assertGreaterEqual(evaluate_combat_matchup_context({"fighter_b_knockdowns_absorbed": 4})["matchup_risk_score"], 40)

    def test_060_injury_uncertainty_caps_if_supplied(self):
        self.assertGreater(evaluate_combat_availability_context({"injury_status": "questionable"})["injury_risk_score"], 60)

    def test_061_weight_cut_warning_if_supplied(self):
        self.assertIn("bad_weight_cut_supplied_hard_warning", evaluate_combat_availability_context({"weight_cut_severity": 0.9})["no_bet_reasons"])

    def test_062_short_notice_warning_if_supplied(self):
        self.assertIn("short_notice_supplied_market_wide_uncertainty", evaluate_combat_availability_context({"short_notice_flag": True})["no_bet_reasons"])

    def test_063_layoff_affects_volatility(self):
        self.assertGreater(evaluate_combat_availability_context({"layoff_days": 700})["layoff_risk_score"], 50)

    def test_064_opponent_change_invalidates_matchup(self):
        self.assertIn("opponent_change_invalidates_matchup_assumptions", evaluate_combat_availability_context({"opponent_change_context": 1})["no_bet_reasons"])

    def test_065_camp_change_modifier_only(self):
        self.assertIn("camp_change_uncertainty_modifier_only", evaluate_combat_availability_context({"camp_change_context": 1})["no_bet_reasons"])

    def test_066_missing_health_not_fabricated(self):
        self.assertFalse(evaluate_combat_availability_context({})["health_fabricated"])

    def test_067_scheduled_rounds_affect_totals(self):
        self.assertGreater(evaluate_combat_ruleset_referee_judging_context({"scheduled_rounds": 12, "ruleset": "boxing"})["ruleset_context_score"], 30)

    def test_068_five_round_title_affects_context(self):
        self.assertGreater(evaluate_combat_ruleset_referee_judging_context({"scheduled_rounds": 5, "title_fight": True})["five_round_context_score"], 80)

    def test_069_mma_boxing_rules_separated(self):
        self.assertEqual(evaluate_combat_ruleset_referee_judging_context({"ruleset": "boxing"})["ruleset"], "boxing")

    def test_070_referee_stoppage_supplied(self):
        self.assertGreater(evaluate_combat_ruleset_referee_judging_context({"referee_stoppage_tendency": 0.8})["referee_stoppage_modifier"], 70)

    def test_071_referee_standup_supplied(self):
        self.assertGreater(evaluate_combat_ruleset_referee_judging_context({"referee_standup_tendency": 0.8})["referee_standup_modifier"], 70)

    def test_072_judge_volatility_supplied(self):
        self.assertGreater(evaluate_combat_ruleset_referee_judging_context({"judging_variance_proxy": 0.8})["judging_volatility_score"], 60)

    def test_073_missing_ref_judge_no_fabrication(self):
        result = evaluate_combat_ruleset_referee_judging_context({})
        self.assertFalse(result["referee_tendency_fabricated"])
        self.assertFalse(result["judge_tendency_fabricated"])

    def test_074_split_decision_capped(self):
        self.assertIn("judging_volatility_caps_decision_split_markets", evaluate_combat_ruleset_referee_judging_context({"judging_variance_proxy": 0.8})["no_bet_reasons"])

    def test_075_incentive_modifier_only(self):
        self.assertFalse(evaluate_combat_incentive_context({"title_fight_context": True}).get("incentive_is_standalone_edge", False))

    def test_076_title_stakes_if_supplied(self):
        self.assertGreater(evaluate_combat_incentive_context({"title_eliminator_context": True})["motivation_alignment_score"], 20)

    def test_077_bonus_finish_chase_if_supplied(self):
        self.assertGreater(evaluate_combat_incentive_context({"performance_bonus_motivation": 1.0})["finish_chase_risk"], 40)

    def test_078_rivalry_volatility_only(self):
        self.assertIn("rivalry_grudge_context_volatility_only", evaluate_combat_incentive_context({"rivalry_context": 1.0})["no_bet_reasons"])

    def test_079_narrative_overfit(self):
        self.assertEqual(evaluate_combat_incentive_context({})["narrative_overfit_risk"], "high")

    def _market(self, market="moneyline"):
        diag = _diag(market)
        return diag["market_relevance"]["market_relevance_scores"]

    def test_080_moneyline_links_core(self):
        self.assertGreater(self._market("moneyline")["moneyline"], 35)

    def test_081_method_links_paths(self):
        self.assertGreater(self._market("method_of_victory")["method_of_victory"], 25)

    def test_082_goes_distance_links_finish(self):
        self.assertIn("fight_goes_distance", self._market("fight_goes_distance"))

    def test_083_over_under_links_rounds(self):
        self.assertGreater(self._market("over_rounds")["over_rounds"], 20)

    def test_084_exact_round_capped(self):
        diag = _diag("exact_round")
        self.assertIn("exact_round", diag["market_relevance"]["market_confidence_caps"])

    def test_085_striking_props_link_pace_range(self):
        self.assertGreater(self._market("fighter_significant_strikes")["fighter_significant_strikes"], 25)

    def test_086_takedown_props_link_wrestling(self):
        self.assertGreater(self._market("fighter_takedowns")["fighter_takedowns"], 25)

    def test_087_submission_props_link_threat(self):
        self.assertGreater(self._market("fighter_submission_attempts")["fighter_submission_attempts"], 20)

    def test_088_boxing_props_link_punch_profile(self):
        self.assertGreater(self._market("fighter_total_punches_landed")["fighter_total_punches_landed"], 20)

    def test_089_no_outcomes_insufficient_data(self):
        self.assertEqual(evaluate_combat_impact_calibration({}, sport="mma", market_type="moneyline")["calibration_status"], "insufficient_data")

    def test_090_low_sample_insufficient(self):
        self.assertTrue(evaluate_combat_impact_calibration({"matched_outcomes_count": 12}, market_type="moneyline")["insufficient_sample"])

    def test_091_real_outcomes_partial(self):
        self.assertEqual(evaluate_combat_impact_calibration({"settled_outcomes": [{"hit": True}, {"hit": False}]}, market_type="moneyline")["calibration_status"], "partial_calibration")

    def test_092_roi_not_emitted_without_returns(self):
        self.assertNotIn("roi_proxy", evaluate_combat_impact_calibration({"settled_outcomes": [{"hit": True}]}, market_type="moneyline"))

    def test_093_clv_not_emitted_without_prices(self):
        self.assertNotIn("clv_proxy", evaluate_combat_impact_calibration({"settled_outcomes": [{"hit": True}]}, market_type="moneyline"))

    def test_094_slippage_not_emitted_without_fills(self):
        self.assertNotIn("slippage_proxy", evaluate_combat_impact_calibration({"settled_outcomes": [{"hit": True}]}, market_type="moneyline"))

    def test_095_exact_round_extra_conservative(self):
        self.assertTrue(evaluate_combat_impact_calibration({"matched_outcomes_count": 100}, market_type="exact_round")["exact_round_extra_conservative"])

    def test_096_split_decision_extra_conservative(self):
        self.assertTrue(evaluate_combat_impact_calibration({"matched_outcomes_count": 100}, market_type="split_decision")["split_decision_extra_conservative"])

    def test_097_context_buckets_preserved(self):
        self.assertEqual(evaluate_combat_impact_calibration({"striking_bucket": "high_volume"}, market_type="moneyline")["calibration_buckets"]["striking_bucket"], "high_volume")

    def test_098_fake_phase_claim_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["phase_control_context"], "phase_control_allowed": False}, film_tracking_context={"claimed_phase_control": True})
        self.assertIn("phase_control_missing_but_claimed", red["red_team_reasons"])

    def test_099_fake_punch_tracking_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["film_tracking_context"], "punch_tracking_not_fabricated": True}, film_tracking_context={"claimed_punch_tracking": True})
        self.assertIn("punch_tracking_missing_but_claimed", red["red_team_reasons"])

    def test_100_fake_grappling_control_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["ground_control_context"]}, grappling_control_impact={"limited_proxy": True}, film_tracking_context={"claimed_grappling_control": True})
        self.assertIn("grappling_control_missing_but_claimed", red["red_team_reasons"])

    def test_101_fake_durability_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["damage_durability_context"], "damage_durability_allowed": False}, film_tracking_context={"claimed_durability": True})
        self.assertIn("durability_missing_but_claimed", red["red_team_reasons"])

    def test_102_chin_record_only_downgraded(self):
        red = evaluate_combat_impact_red_team(damage_durability_context={"no_bet_reasons": ["chin_not_inferred_from_record_only"]})
        self.assertIn("chin_claim_from_record_only", red["red_team_reasons"])

    def test_103_fake_injury_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["injury_medical_context"]}, film_tracking_context={"claimed_injury_status": True})
        self.assertIn("injury_status_missing_but_claimed", red["red_team_reasons"])

    def test_104_fake_weight_cut_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["weight_cut_context"]}, film_tracking_context={"claimed_weight_cut": True})
        self.assertIn("weight_cut_missing_but_claimed", red["red_team_reasons"])

    def test_105_fake_camp_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["camp_context"]}, film_tracking_context={"claimed_camp_context": True})
        self.assertIn("camp_context_missing_but_claimed", red["red_team_reasons"])

    def test_106_fake_referee_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["referee_context"]}, film_tracking_context={"claimed_referee_tendency": True})
        self.assertIn("referee_tendency_missing_but_claimed", red["red_team_reasons"])

    def test_107_fake_judge_downgraded(self):
        red = evaluate_combat_impact_red_team(data_availability={"missing_field_groups": ["judging_context"]}, film_tracking_context={"claimed_judge_tendency": True})
        self.assertIn("judge_tendency_missing_but_claimed", red["red_team_reasons"])

    def test_108_small_finish_overfit(self):
        red = evaluate_combat_impact_red_team(striking_impact={"ko_tko_relevance_modifier": 80, "insufficient_sample": True})
        self.assertIn("small_sample_finish_rate_overfit", red["red_team_reasons"])

    def test_109_knockdown_overfit(self):
        red = evaluate_combat_impact_red_team(striking_impact={"no_bet_reasons": ["knockdown_average_sample_capped"]})
        self.assertIn("knockdown_rate_overfit", red["red_team_reasons"])

    def test_110_submission_overfit(self):
        red = evaluate_combat_impact_red_team(grappling_control_impact={"submission_relevance_modifier": 80, "insufficient_sample": True})
        self.assertIn("submission_rate_overfit", red["red_team_reasons"])

    def test_111_age_curve_overfit(self):
        red = evaluate_combat_impact_red_team(availability_context={"age_curve_risk_score": 80}, source_payload={"claimed_age_curve_edge": True})
        self.assertIn("age_curve_overfit", red["red_team_reasons"])

    def test_112_layoff_narrative_overfit(self):
        red = evaluate_combat_impact_red_team(availability_context={"layoff_risk_score": 80})
        self.assertIn("layoff_narrative_overfit", red["red_team_reasons"])

    def test_113_rivalry_narrative_overfit(self):
        red = evaluate_combat_impact_red_team(incentive_context={"narrative_overfit_risk": "high"}, source_payload={"rivalry_context": 1})
        self.assertIn("rivalry_narrative_overfit", red["red_team_reasons"])

    def test_114_exact_round_overconfidence(self):
        red = evaluate_combat_impact_red_team(market_type="exact_round", calibration={"calibration_status": "insufficient_data"})
        self.assertIn("exact_round_overconfidence", red["red_team_reasons"])

    def test_115_split_decision_overconfidence(self):
        red = evaluate_combat_impact_red_team(market_type="split_decision", calibration={"calibration_status": "insufficient_data"})
        self.assertIn("split_decision_overconfidence", red["red_team_reasons"])

    def test_116_five_round_cardio_overclaim(self):
        red = evaluate_combat_impact_red_team(pace_cardio_context={"five_round_readiness_score": 0}, source_payload={"scheduled_rounds": 5}, film_tracking_context={"claimed_five_round_cardio": True})
        self.assertIn("five_round_cardio_overclaim", red["red_team_reasons"])

    def test_117_boxing_mma_confusion(self):
        red = evaluate_combat_impact_red_team(ruleset_referee_judging_context={"ruleset": "boxing"}, grappling_control_impact={"grappling_impact_score": 60})
        self.assertIn("boxing_mma_context_confusion", red["red_team_reasons"])

    def test_118_calibration_missing_prevents_active(self):
        self.assertNotEqual(_diag("method_of_victory")["recommended_review_status"], "ACTIVE_REVIEW")


class TestCombatSafetyAndRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_119_readiness_provider_write_false(self):
        self.assertFalse(self.client.get("/api/automation/combat-impact-readiness").json()["provider_write"])

    def test_120_diagnostics_execution_false(self):
        self.assertFalse(self.client.post("/api/automation/combat-impact-diagnostics", json={"sport": "mma", "bout_context": _bout(), "fighter_a_context": _fa(), "fighter_b_context": _fb()}).json()["execution_allowed"])

    def test_121_dry_run_false_rejected(self):
        self.assertEqual(self.client.post("/api/automation/combat-impact-diagnostics", json={"dry_run": False}).status_code, 400)

    def test_122_no_order_payload_survives_compaction(self):
        payload = _diag("moneyline")
        payload["order_payload"] = {"x": 1}
        compact = compact_combat_impact_diagnostics_response(payload)
        self.assertNotIn("order_payload", compact)

    def test_123_no_bet_slip_survives_compaction(self):
        payload = _diag("moneyline")
        payload["bet_slip"] = {"x": 1}
        compact = compact_combat_impact_diagnostics_response(payload)
        self.assertNotIn("bet_slip", compact)

    def test_124_secrets_raw_payload_redacted(self):
        payload = _diag("moneyline")
        payload["api_key"] = "sk-secret"
        payload["raw_payload"] = {"x": 1}
        compact = compact_combat_impact_diagnostics_response(payload)
        self.assertNotIn("api_key", compact)
        self.assertNotIn("raw_payload", compact)

    def test_125_ai_red_team_cannot_promote_execution(self):
        red = evaluate_combat_impact_red_team(calibration={"calibration_status": "insufficient_data"})
        self.assertNotEqual(red["recommended_action_adjustment"], "EXECUTE")
        self.assertFalse(red["execution_allowed"])

    def test_126_health_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/health").status_code, 200)

    def test_127_security_readiness_passes(self):
        self.assertEqual(self.client.get("/api/automation/security-readiness").status_code, 200)

    def test_128_strategy_readiness_passes(self):
        self.assertEqual(self.client.get("/api/automation/strategy-readiness").status_code, 200)

    def test_129_advanced_red_team_passes(self):
        self.assertEqual(self.client.get("/api/automation/advanced-red-team-report").status_code, 200)

    def test_130_extreme_randomness_passes(self):
        self.assertEqual(self.client.get("/api/automation/extreme-randomness-report").status_code, 200)

    def test_131_basketball_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/basketball-player-impact-readiness").status_code, 200)

    def test_132_football_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/football-impact-readiness").status_code, 200)

    def test_133_baseball_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/baseball-impact-readiness").status_code, 200)

    def test_134_hockey_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/hockey-impact-readiness").status_code, 200)

    def test_135_soccer_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/soccer-impact-readiness").status_code, 200)

    def test_136_golf_endpoint_passes(self):
        self.assertEqual(self.client.get("/api/automation/golf-impact-readiness").status_code, 200)

    def test_137_tennis_endpoint_if_present(self):
        response = self.client.get("/api/automation/tennis-impact-readiness")
        if response.status_code != 404:
            self.assertEqual(response.status_code, 200)

    def test_138_combat_malformed_payload_not_500(self):
        response = self.client.post("/api/automation/combat-impact-diagnostics", json={"sport": "mma", "bout_context": "bad"})
        self.assertLess(response.status_code, 500)

    def test_139_limited_public_data_no_fake_advanced_claims(self):
        result = self.client.post(
            "/api/automation/combat-impact-diagnostics",
            json={
                "sport": "mma",
                "market_type": "over_rounds",
                "bout_context": _bout(weight_class="welterweight"),
                "fighter_a_context": {"fighter_name": "A"},
                "fighter_b_context": {"fighter_name": "B"},
                "striking_context": {"fighter_a_significant_strikes_landed_per_minute": 3.4, "fighter_b_significant_strikes_landed_per_minute": 2.9},
                "calibration_context": {"matched_outcomes_count": 0},
            },
        ).json()
        self.assertFalse(result["data_availability"]["phase_control_not_fabricated"] is False)
        self.assertFalse(result["damage_durability_context"]["durability_fabricated"])
        self.assertFalse(result["availability_context"]["injury_status_fabricated"])
        self.assertFalse(result["availability_context"]["weight_cut_fabricated"])
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_140_compact_output_safety_locked(self):
        compact = compact_combat_impact_diagnostics_response(_diag("moneyline"))
        self.assertFalse(compact["provider_write"])
        self.assertFalse(compact["execution_allowed"])
        self.assertTrue(compact["compact_response"])


if __name__ == "__main__":
    unittest.main()
