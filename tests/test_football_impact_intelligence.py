import unittest

from fastapi.testclient import TestClient

from automation_scheduler.football_availability_context import evaluate_football_availability_context
from automation_scheduler.football_data_availability import evaluate_football_data_availability
from automation_scheduler.football_impact_calibration import evaluate_football_impact_calibration
from automation_scheduler.football_impact_report import build_football_impact_diagnostics
from automation_scheduler.football_incentive_context import evaluate_football_incentive_context
from automation_scheduler.football_market_relevance import evaluate_football_market_relevance
from automation_scheduler.football_matchup_context import evaluate_football_matchup_context
from automation_scheduler.football_personnel_context import evaluate_football_personnel_context
from automation_scheduler.football_play_drive_impact import evaluate_football_play_drive_impact
from automation_scheduler.football_role_impact import evaluate_football_role_impact
from automation_scheduler.response_compactor import compact_football_impact_diagnostics_response
from main import app


def _nfl_play_context(**extra):
    row = {
        "epa_per_play": 0.08,
        "success_rate": 0.47,
        "explosive_play_rate": 0.12,
        "negative_play_rate": 0.13,
        "third_down_success_rate": 0.43,
        "red_zone_td_rate": 0.58,
        "points_per_drive": 2.3,
        "yards_per_play": 5.9,
        "plays_per_game": 64,
        "turnover_rate": 0.08,
        "penalty_epa": -0.02,
        "plays_sample_size": 420,
    }
    row.update(extra)
    return row


def _qb_context(**extra):
    row = {
        "role": "QB",
        "epa_per_dropback": 0.11,
        "success_rate": 0.48,
        "cpoe": 2.4,
        "pressure_to_sack_rate": 0.17,
        "time_to_throw": 2.71,
        "air_yards_per_attempt": 8.1,
        "deep_attempt_rate": 0.14,
        "turnover_worthy_proxy": 0.03,
        "dropbacks": 320,
        "snap_share_recent": 1.0,
    }
    row.update(extra)
    return row


class TestFootballDataAvailability(unittest.TestCase):
    def test_01_nfl_tier_0_returns_data_insufficient(self):
        result = evaluate_football_data_availability("americanfootball_nfl")
        self.assertEqual(result["data_tier"], 0)
        self.assertEqual(result["recommended_action_adjustment"], "DATA_INSUFFICIENT")

    def test_02_ncaaf_missing_tracking_data_does_not_fail(self):
        result = evaluate_football_data_availability("americanfootball_ncaaf", team_context={"team": "A", "opponent": "B"})
        self.assertEqual(result["sport"], "americanfootball_ncaaf")
        self.assertFalse(result["tracking_level_allowed"])
        self.assertTrue(result["ncaaf_tracking_not_assumed"])

    def test_03_tier_1_basic_data_caps_confidence(self):
        result = build_football_impact_diagnostics(
            sport="americanfootball_nfl",
            market_type="spread",
            team_context={"team": "A", "opponent": "B", "yards_per_game": 360, "points_per_game": 24},
        )
        self.assertEqual(result["data_tier"], 1)
        self.assertEqual(result["play_drive_impact"]["confidence_cap_reason"], "epa_missing_limited_tier_1_proxy")
        self.assertTrue(result["play_drive_impact"]["limited_proxy_used"])

    def test_04_tier_2_play_drive_data_enables_diagnostics(self):
        result = build_football_impact_diagnostics(sport="americanfootball_nfl", market_type="total", play_drive_context=_nfl_play_context())
        self.assertEqual(result["data_tier"], 2)
        self.assertGreater(result["play_drive_impact"]["play_impact_score"], 0)

    def test_05_tier_3_player_participation_enables_role_diagnostics(self):
        result = build_football_impact_diagnostics(
            sport="americanfootball_nfl",
            market_type="player_passing_prop",
            player_context={"role": "QB", "snap_share_recent": 1.0, "dropbacks": 320, "epa_per_dropback": 0.11, "success_rate": 0.48, "cpoe": 2.4},
        )
        self.assertEqual(result["data_tier"], 3)
        self.assertTrue(result["player_level_allowed"])
        self.assertGreater(result["role_impact"]["role_impact_score"], 0)

    def test_06_tier_4_tracking_optional_never_required(self):
        tier3 = evaluate_football_data_availability("americanfootball_nfl", player_context={"role": "WR", "snap_share_recent": 0.9, "target_share": 0.24})
        tier4 = evaluate_football_data_availability("americanfootball_nfl", player_context={"role": "WR", "snap_share_recent": 0.9, "separation_proxy": 1.2})
        self.assertEqual(tier3["data_tier"], 3)
        self.assertFalse(tier3["tracking_level_allowed"])
        self.assertEqual(tier4["data_tier"], 4)


class TestFootballPlayDriveImpact(unittest.TestCase):
    def test_07_epa_success_explosiveness_produce_stable_play_impact(self):
        result = evaluate_football_play_drive_impact(_nfl_play_context())
        self.assertGreater(result["play_impact_score"], 50)
        self.assertGreater(result["explosiveness_score"], 0)

    def test_08_missing_epa_uses_limited_proxy_only_if_allowed(self):
        result = evaluate_football_play_drive_impact({"yards_per_play": 5.8, "points_per_drive": 2.2, "success_rate": 0.45, "plays_sample_size": 300})
        self.assertTrue(result["limited_proxy_used"])
        self.assertEqual(result["confidence_cap_reason"], "epa_missing_limited_tier_1_proxy")
        self.assertFalse(result["epa_fabricated"])

    def test_09_small_sample_flags_insufficient_sample(self):
        result = evaluate_football_play_drive_impact(_nfl_play_context(plays_sample_size=12))
        self.assertTrue(result["insufficient_sample"])
        self.assertEqual(result["confidence_cap_reason"], "sample_too_small")

    def test_10_red_zone_and_third_down_affect_leverage_score(self):
        low = evaluate_football_play_drive_impact(_nfl_play_context(third_down_success_rate=0.28, red_zone_td_rate=0.38))
        high = evaluate_football_play_drive_impact(_nfl_play_context(third_down_success_rate=0.52, red_zone_td_rate=0.72))
        self.assertGreater(high["leverage_score"], low["leverage_score"])

    def test_11_turnovers_and_penalties_reduce_impact(self):
        clean = evaluate_football_play_drive_impact(_nfl_play_context(turnover_rate=0.03, penalty_epa=0.02))
        sloppy = evaluate_football_play_drive_impact(_nfl_play_context(turnover_rate=0.17, penalty_epa=-0.16))
        self.assertGreater(sloppy["turnover_penalty"], clean["turnover_penalty"])
        self.assertGreater(sloppy["penalty_penalty"], clean["penalty_penalty"])


class TestFootballRoleImpact(unittest.TestCase):
    def test_12_qb_role_computes_core_fields(self):
        result = evaluate_football_role_impact(_qb_context())
        self.assertEqual(result["role"], "QB")
        self.assertGreater(result["role_efficiency_score"], 0)
        self.assertIn("passing_yards", result["player_market_relevance"])

    def test_13_rb_role_computes_rush_receiving_role(self):
        result = evaluate_football_role_impact({"role": "RB", "rush_epa": 0.05, "rushing_success_rate": 0.48, "target_share": 0.12, "route_participation": 0.36, "carry_share_recent": 0.58})
        self.assertEqual(result["role"], "RB")
        self.assertIn("rushing_yards", result["player_market_relevance"])

    def test_14_wr_te_role_computes_route_target_air_yard_relevance(self):
        wr = evaluate_football_role_impact({"role": "WR", "route_participation": 0.86, "target_share": 0.26, "air_yard_share": 0.38, "yards_per_route_run": 2.3})
        te = evaluate_football_role_impact({"role": "TE", "route_participation": 0.72, "target_share": 0.19, "air_yard_share": 0.18, "yards_per_route_run": 1.7})
        self.assertIn("receiving_yards", wr["player_market_relevance"])
        self.assertIn("receptions", te["player_market_relevance"])

    def test_15_ol_role_does_not_fabricate_pressure_responsibility(self):
        result = evaluate_football_role_impact({"role": "OL", "snap_share_recent": 0.98})
        self.assertEqual(result["role"], "OL")
        self.assertIn("pressure_allowed_proxy", result["missing_role_inputs"])
        self.assertFalse(result["tracking_metrics_inferred"])

    def test_16_defensive_role_handles_pressure_coverage_run_stop_fields(self):
        edge = evaluate_football_role_impact({"role": "EDGE", "pressure_rate": 0.17, "sack_rate": 0.08, "run_stop_rate": 0.10})
        cb = evaluate_football_role_impact({"role": "CB", "yards_allowed_per_target": 5.5, "explosive_allowed_rate": 0.06, "turnover_play_rate": 0.04})
        self.assertIn("sacks", edge["player_market_relevance"])
        self.assertIn("interceptions", cb["player_market_relevance"])

    def test_17_unknown_role_caps_confidence(self):
        result = evaluate_football_role_impact({"role": "slot_machine", "target_share": 0.2})
        self.assertEqual(result["role"], "unknown")
        self.assertLessEqual(result["role_confidence_cap"], 25)


class TestFootballPersonnelMatchup(unittest.TestCase):
    def test_18_personnel_group_context_works(self):
        result = evaluate_football_personnel_context({"offensive_personnel_rate_11": 0.68, "shotgun_rate": 0.74, "motion_rate": 0.52, "defensive_nickel_rate": 0.70})
        self.assertGreater(result["personnel_fit_score"], 0)

    def test_19_qb_vs_pressure_mismatch_creates_risk(self):
        result = evaluate_football_matchup_context({"qb_pressure_to_sack_rate": 0.27, "opponent_pressure_rate": 0.46, "ol_pressure_allowed_proxy": 0.40})
        self.assertGreaterEqual(result["qb_pressure_risk_score"], 65)
        self.assertIn("qb_vs_pressure_disadvantage", result["mismatch_reasons"])

    def test_20_wr_vs_cb_mismatch_creates_relevance(self):
        result = evaluate_football_matchup_context({"wr_cb_advantage": 15})
        self.assertIn("wr_vs_cb_advantage", result["mismatch_reasons"])
        self.assertIn("receiving_yards", result["market_specific_matchup_notes"])

    def test_21_ol_vs_dl_mismatch_affects_sack_rushing_markets(self):
        result = evaluate_football_matchup_context({"run_block_success_proxy": 0.33, "defensive_run_stop_rate": 0.16, "box_count": 8.5, "dl_pressure_rate": 0.46})
        self.assertIn("ol_vs_dl_run_game_disadvantage", result["mismatch_reasons"])
        self.assertIn("rushing_yards", result["market_specific_matchup_notes"])

    def test_22_weather_wind_modifies_passing_kicking_total_relevance(self):
        result = build_football_impact_diagnostics(
            sport="americanfootball_nfl",
            market_type="total",
            play_drive_context=_nfl_play_context(),
            availability_context={"wind_mph": 22, "injury_status": "healthy"},
        )
        self.assertIn("wind_caps_passing_kicking_total_markets", result["market_relevance"]["no_bet_market_reasons"])
        self.assertIn("total", result["market_relevance"]["weather_adjusted_markets"])

    def test_23_backup_qb_status_creates_market_wide_risk(self):
        result = evaluate_football_availability_context({"starting_qb_status": "backup_starting", "rest_days": 7})
        self.assertGreaterEqual(result["starting_qb_market_risk_score"], 90)
        self.assertIn("starting_qb_change_market_wide_risk", result["market_wide_risk_flags"])


class TestFootballAvailabilityIncentive(unittest.TestCase):
    def test_24_injury_questionable_caps_confidence(self):
        result = evaluate_football_availability_context({"injury_status": "questionable", "practice_status": "limited"})
        self.assertEqual(result["confidence_cap_reason"], "injury_uncertainty_caps_confidence")
        self.assertGreaterEqual(result["injury_risk_score"], 70)

    def test_25_snap_share_instability_caps_prop_confidence(self):
        result = evaluate_football_availability_context({"snap_share_recent": 0.42, "snap_share_trend": -0.25})
        self.assertEqual(result["confidence_cap_reason"], "snap_share_instability_caps_prop_confidence")

    def test_26_short_week_rest_travel_creates_risk_flags(self):
        result = evaluate_football_availability_context({"short_week": True, "rest_days": 3, "travel_distance": 2200})
        self.assertIn("short_week_rest_travel_risk", result["market_wide_risk_flags"])

    def test_27_incentive_context_is_modifier_only(self):
        result = evaluate_football_incentive_context({"contract_year": True, "seeding_motivation": 80})
        self.assertFalse(result["incentive_is_standalone_edge"])
        self.assertEqual(result["incentive_context_status"], "modifier_only")

    def test_28_weak_incentive_evidence_creates_narrative_overfit_risk(self):
        result = evaluate_football_incentive_context({"revenge_narrative_context": 80})
        self.assertEqual(result["narrative_overfit_risk"], "high")
        self.assertIn("weak_incentive_evidence_narrative_overfit_risk", result["no_bet_reasons"])

    def test_29_contract_bonus_missing_does_not_fabricate_threshold(self):
        result = evaluate_football_incentive_context({"contract_year": True})
        self.assertFalse(result["bonus_threshold_fabricated"])
        self.assertFalse(result["known_bonus_threshold_present"])


class TestFootballMarketRelevance(unittest.TestCase):
    def test_30_passing_prop_relevance_links_qb_wr_weather_pressure(self):
        result = evaluate_football_market_relevance(
            market_type="player_passing_prop",
            role_impact={"role": "QB", "role_impact_score": 78, "role_efficiency_score": 72, "role_usage_score": 80},
            matchup_context={"qb_pressure_risk_score": 30, "wr_cb_matchup_score": 75},
            availability_context={"weather_adjustment_score": 10, "wind_risk_score": 5, "snap_stability_score": 95},
            play_drive_impact={"pace_volume_score": 62, "explosiveness_score": 66},
        )
        self.assertGreater(result["selected_market_relevance_score"], 50)
        self.assertIn("passing_yards", result["strongest_market_links"])

    def test_31_rushing_prop_relevance_links_rb_ol_box_game_script(self):
        result = evaluate_football_market_relevance(
            market_type="player_rushing_prop",
            role_impact={"role": "RB", "role_impact_score": 76, "role_usage_score": 82, "role_efficiency_score": 70},
            matchup_context={"ol_dl_run_matchup_score": 78},
            availability_context={"snap_stability_score": 85},
        )
        self.assertGreater(result["market_relevance_scores"]["rushing_yards"], 50)

    def test_32_total_relevance_links_pace_weather_explosive_red_zone(self):
        result = evaluate_football_market_relevance(
            market_type="total",
            play_drive_impact={"pace_volume_score": 78, "play_impact_score": 70, "explosiveness_score": 72, "red_zone_score": 68},
            availability_context={"weather_adjustment_score": 8, "wind_risk_score": 4},
        )
        self.assertGreater(result["market_relevance_scores"]["total"], 50)

    def test_33_spread_relevance_links_unit_mismatch_and_qb_availability(self):
        result = evaluate_football_market_relevance(
            market_type="spread",
            play_drive_impact={"play_impact_score": 70, "drive_impact_score": 72},
            matchup_context={"matchup_advantage_score": 68},
            availability_context={"availability_score": 90, "starting_qb_market_risk_score": 5},
        )
        self.assertGreater(result["market_relevance_scores"]["spread"], 50)

    def test_34_defensive_prop_relevance_links_pressure_snap_coverage(self):
        result = evaluate_football_market_relevance(
            market_type="defensive_prop",
            role_impact={"role": "LB", "role_impact_score": 74, "role_usage_score": 80},
            matchup_context={"matchup_risk_score": 70},
            availability_context={"snap_stability_score": 88},
        )
        self.assertGreater(result["market_relevance_scores"]["defensive_prop"], 50)


class TestFootballCalibrationSafetyAndEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_35_no_labeled_outcomes_returns_insufficient_data(self):
        result = evaluate_football_impact_calibration({}, sport="americanfootball_nfl", market_type="spread", role="QB", data_tier=3)
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_36_low_sample_returns_insufficient_sample(self):
        result = evaluate_football_impact_calibration({"matched_outcomes_count": 10}, sport="americanfootball_nfl", market_type="spread", role="QB", data_tier=3)
        self.assertTrue(result["insufficient_sample"])

    def test_37_real_labeled_outcomes_enable_partial_calibration(self):
        result = evaluate_football_impact_calibration({"matched_outcomes_count": 35}, sport="americanfootball_nfl", market_type="spread", role="QB", data_tier=3)
        self.assertEqual(result["calibration_status"], "partial_calibration")

    def test_38_roi_clv_slippage_not_emitted_without_real_price_data(self):
        result = evaluate_football_impact_calibration({"matched_outcomes_count": 35}, sport="americanfootball_nfl", market_type="spread", role="QB", data_tier=3)
        self.assertNotIn("roi_proxy", result)
        self.assertNotIn("clv_proxy", result)
        self.assertNotIn("slippage_proxy", result)

    def test_39_context_buckets_are_preserved(self):
        result = evaluate_football_impact_calibration(
            {"matched_outcomes_count": 35, "context_bucket": "nfl.spread.qb.wind_low"},
            sport="americanfootball_nfl",
            market_type="spread",
            role="QB",
            data_tier=3,
        )
        self.assertEqual(result["calibration_buckets"]["context_bucket"], "nfl.spread.qb.wind_low")

    def test_40_endpoint_returns_provider_write_false(self):
        response = self.client.post("/api/automation/football-impact-diagnostics", json={"dry_run": True, "sport": "americanfootball_nfl", "market_type": "spread", "play_drive_context": _nfl_play_context()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_41_endpoint_returns_execution_allowed_false(self):
        response = self.client.post("/api/automation/football-impact-diagnostics", json={"dry_run": True, "sport": "americanfootball_nfl", "market_type": "spread"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_42_dry_run_false_is_rejected(self):
        response = self.client.post("/api/automation/football-impact-diagnostics", json={"dry_run": False, "sport": "americanfootball_nfl"})
        self.assertEqual(response.status_code, 400)

    def test_43_no_order_bet_execution_payload_survives_compaction(self):
        result = build_football_impact_diagnostics(
            sport="americanfootball_nfl",
            market_type="spread",
            team_context={"team": "A", "order_payload": {"side": "buy"}, "bet_slip": {"stake": 100}},
        )
        compact = compact_football_impact_diagnostics_response(result)
        rendered = str(compact)
        self.assertNotIn("stake", rendered)
        self.assertNotIn("order_payload", rendered)
        self.assertFalse(compact["provider_write"])

    def test_44_secrets_raw_payloads_are_redacted(self):
        response = self.client.post(
            "/api/automation/football-impact-diagnostics?include_debug=true",
            json={
                "dry_run": True,
                "sport": "americanfootball_nfl",
                "team_context": {"team": "A", "raw_payload": {"x": "drop"}, "api_key": "sk-secretsecretsecret"},
            },
        )
        rendered = str(response.json())
        self.assertNotIn("sk-secretsecretsecret", rendered)
        self.assertNotIn("'raw_payload': {'x': 'drop'}", rendered)
        self.assertFalse(response.json()["raw_payload_included"])
        self.assertFalse(response.json()["secrets_included"])

    def test_45_ai_red_team_output_cannot_promote_execution(self):
        result = build_football_impact_diagnostics(
            sport="americanfootball_nfl",
            market_type="spread",
            team_context={"recommended_action": "EXECUTE", "execution_allowed": True, "team": "A"},
        )
        self.assertNotEqual(result["recommended_action_adjustment"], "EXECUTE")
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["provider_write"])

    def test_46_existing_health_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/health").status_code, 200)

    def test_47_security_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/security-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_48_strategy_readiness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/strategy-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_49_advanced_red_team_endpoint_still_passes(self):
        response = self.client.get("/api/automation/advanced-red-team-report")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_50_extreme_randomness_endpoint_still_passes(self):
        response = self.client.get("/api/automation/extreme-randomness-report")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_51_nfl_ncaaf_malformed_payload_does_not_500(self):
        nfl = self.client.post("/api/automation/football-impact-diagnostics", json={"sport": "americanfootball_nfl", "dry_run": True})
        ncaaf = self.client.post("/api/automation/football-impact-diagnostics", json={"sport": "americanfootball_ncaaf", "dry_run": True, "team_context": {"team": "A"}})
        self.assertEqual(nfl.status_code, 200)
        self.assertEqual(ncaaf.status_code, 200)

    def test_52_missing_player_context_does_not_500(self):
        response = self.client.post("/api/automation/football-impact-diagnostics", json={"sport": "americanfootball_nfl", "dry_run": True, "play_drive_context": _nfl_play_context()})
        self.assertEqual(response.status_code, 200)
        self.assertIn("role_impact", response.json())

    def test_53_missing_play_context_does_not_500(self):
        response = self.client.post("/api/automation/football-impact-diagnostics", json={"sport": "americanfootball_nfl", "dry_run": True, "player_context": _qb_context()})
        self.assertEqual(response.status_code, 200)
        self.assertIn("play_drive_impact", response.json())

    def test_54_ncaaf_limited_public_data_returns_useful_tier_without_fake_tracking(self):
        response = self.client.post(
            "/api/automation/football-impact-diagnostics",
            json={
                "sport": "americanfootball_ncaaf",
                "market_type": "team_total",
                "dry_run": True,
                "team_context": {"team": "A", "opponent": "B", "yards_per_play": 6.1, "points_per_drive": 2.5},
                "play_drive_context": {"success_rate": 0.49, "points_per_drive": 2.5, "yards_per_play": 6.1, "plays_sample_size": 220},
            },
        )
        payload = response.json()
        self.assertIn(payload["data_tier"], {1, 2})
        self.assertFalse(payload["tracking_level_allowed"])
        self.assertFalse(payload["role_impact"]["tracking_metrics_inferred"])

    def test_55_football_impact_readiness_endpoint_supported(self):
        response = self.client.get("/api/automation/football-impact-readiness")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "football_impact_readiness")
        self.assertIn("americanfootball_nfl", payload["supported_sports"])
        self.assertIn("americanfootball_ncaaf", payload["supported_sports"])
        self.assertFalse(payload["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
