import asyncio
import unittest

from fastapi import HTTPException

from src.services.streamlit_dashboard_facade import evaluate_incentive_context
from src.automation_scheduler_legacy.basketball_player_impact import evaluate_availability_minutes, run_basketball_player_impact
from src.services.streamlit_dashboard_facade import evaluate_basketball_player_impact_calibration
from src.automation_scheduler_legacy.basketball_player_impact_readiness import build_basketball_player_impact_readiness
from src.services.streamlit_dashboard_facade import evaluate_possession_impact
from src.services.streamlit_dashboard_facade import evaluate_role_context
from src.services.streamlit_dashboard_facade import evaluate_tracking_opportunity
from src.automation_scheduler_legacy.response_compactor import compact_basketball_player_impact_readiness_response, compact_basketball_player_impact_response
from tests.support.action_imports import AutomationBasketballPlayerImpactRequest, automation_basketball_player_impact_endpoint, get_automation_basketball_player_impact_readiness_endpoint


def candidate(**extra):
    data = {
        "sport": "basketball_nba",
        "league": "NBA",
        "player_id": "player-1",
        "player_name": "Sample Guard",
        "team_id": "NYK",
        "opponent_id": "BOS",
        "market_type": "points_prop",
        "possessions_played": 720,
        "on_court_offensive_rating": 121,
        "off_court_offensive_rating": 112,
        "on_court_defensive_rating": 109,
        "off_court_defensive_rating": 114,
        "on_court_net_rating": 12,
        "off_court_net_rating": -2,
        "points_created_per_possession": 1.18,
        "expected_points_added": 0.16,
        "expected_points_allowed_impact": 0.08,
        "shot_quality_created": 0.62,
        "shot_quality_allowed": 0.47,
        "turnover_creation_rate": 0.055,
        "turnover_committed_rate": 0.09,
        "foul_drawn_rate": 0.12,
        "foul_committed_rate": 0.055,
        "offensive_rebound_chance_impact": 0.03,
        "defensive_rebound_chance_impact": 0.04,
        "transition_creation_score": 68,
        "half_court_creation_score": 72,
        "touches": 78,
        "frontcourt_touches": 58,
        "time_of_possession": 7.1,
        "average_seconds_per_touch": 4.8,
        "drives": 18,
        "drive_points": 12,
        "drive_assists": 4,
        "paint_touches": 10,
        "catch_and_shoot_attempts": 5,
        "pull_up_attempts": 8,
        "potential_assists": 14,
        "secondary_assists": 2,
        "passes_made": 62,
        "passes_received": 70,
        "rebound_chances": 8,
        "contested_rebound_chances": 3,
        "box_outs": 2,
        "rim_pressure_score": 74,
        "spacing_gravity_score": 70,
        "shot_contest_quality": 55,
        "help_defense_impact": 52,
        "deflections": 3,
        "role_label": "primary_creator",
        "role_confidence": 86,
        "usage_rate": 31,
        "true_shooting_percentage": 61,
        "effective_field_goal_percentage": 56,
        "assist_rate": 29,
        "turnover_rate": 11,
        "free_throw_rate": 0.31,
        "shot_attempt_rate": 22,
        "three_point_attempt_rate": 0.42,
        "rim_attempt_rate": 0.28,
        "points_per_touch": 0.38,
        "points_per_shot_attempt": 1.25,
        "assist_to_turnover_ratio": 2.8,
        "projected_starting_lineup": ["player-1"],
        "projected_closing_lineup": ["player-1"],
        "lineup_net_rating": 9,
        "lineup_offensive_rating": 120,
        "lineup_defensive_rating": 110,
        "lineup_pace": 99,
        "lineup_spacing_score": 75,
        "lineup_rebounding_score": 54,
        "opponent_pace": 98,
        "opponent_pick_and_roll_defense": 42,
        "opponent_rim_protection": 48,
        "opponent_three_point_allowed_profile": 62,
        "opponent_foul_rate": 0.21,
        "opponent_turnover_rate": 0.16,
        "opponent_turnover_forced_rate": 0.13,
        "opponent_rim_attempt_rate": 0.38,
        "defensive_matchup_rating": 63,
        "game_total": 232,
        "implied_team_total": 118,
        "team_spread": -4.5,
        "blowout_risk": 22,
        "games_played": 54,
        "games_missed": 3,
        "injury_designation": "available",
        "minutes_last_5": [35, 36, 34, 37, 35],
        "minutes_last_10": [34, 35, 35, 36, 34, 35, 33, 36, 35, 34],
        "projected_minutes": 35,
        "minutes_volatility": 2.2,
        "foul_trouble_rate": 0.05,
        "rotation_status": "starter",
        "closing_lineup_status": "closing",
    }
    data.update(extra)
    return data


def settled_records(count=130, market_type="points_prop", sport="basketball_nba"):
    return [
        {
            "sport": sport,
            "player_id": "player-1",
            "team_id": "NYK",
            "opponent_id": "BOS",
            "market_type": market_type,
            "hit": i % 3 != 0,
            "edge": 0.025,
            "closing_line_value": 0.18,
            "calibration_error": 0.07,
            "profit": 1.0 if i % 3 != 0 else -1.0,
        }
        for i in range(count)
    ]


class TestBasketballPlayerImpact(unittest.TestCase):
    def assert_safe(self, payload):
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertFalse(payload["auto_execution"])
        self.assertTrue(payload["human_approval_required"])
        self.assertTrue(payload["owner_approval_required"])
        self.assertFalse(payload["sportsbook_bet_execution_enabled"])

    def test_compact_safe_response_and_no_sensitive_payload(self):
        payload = candidate(
            api_key="sk-test-secret-abcdefghijklmnopqrstuvwxyz",
            raw_payload={"do": "not expose"},
            sportsbook_bet_payload={"stake": 100, "selection": "over"},
            provider_write=True,
        )
        result = run_basketball_player_impact(payload)
        compact = compact_basketball_player_impact_response(result)
        self.assert_safe(compact)
        self.assertEqual(compact["recommended_review_status"], "NO_BET")
        rendered = str(compact)
        self.assertNotIn("sk-test-secret", rendered)
        self.assertNotIn("'stake': 100", rendered)
        self.assertFalse(compact["raw_payload_included"])

    def test_supported_sports_remain_distinct(self):
        readiness = build_basketball_player_impact_readiness()
        self.assertEqual(
            readiness["supported_sports"],
            ["basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaaw"],
        )
        contracts = readiness["sport_contracts"]
        self.assertNotEqual(contracts["basketball_nba"]["sport_contract_id"], contracts["basketball_wnba"]["sport_contract_id"])
        self.assertNotEqual(contracts["basketball_ncaab"]["calibration_bucket_prefix"], contracts["basketball_ncaaw"]["calibration_bucket_prefix"])
        self.assertEqual(run_basketball_player_impact(candidate(sport="ncaawb"))["sport"], "basketball_ncaaw")

    def test_missing_data_returns_data_insufficient_not_500(self):
        result = run_basketball_player_impact({"sport": "basketball_wnba", "player_id": "p"})
        self.assertEqual(result["recommended_review_status"], "DATA_INSUFFICIENT")
        self.assertEqual(result["possession_impact"]["possession_impact_status"], "missing")
        self.assertEqual(result["tracking_opportunity"]["tracking_status"], "missing")
        self.assert_safe(result)

    def test_possession_score_computes_and_confidence_scales_with_sample(self):
        strong = evaluate_possession_impact(candidate(possessions_played=800))
        thin = evaluate_possession_impact(candidate(possessions_played=80))
        missing = evaluate_possession_impact({})
        self.assertGreater(strong["possession_impact_score"], 50)
        self.assertEqual(missing["possession_impact_status"], "missing")
        self.assertGreater(strong["possession_impact_confidence"], thin["possession_impact_confidence"])

    def test_tracking_missing_partial_and_prop_weighting(self):
        full = evaluate_tracking_opportunity(candidate())
        partial = evaluate_tracking_opportunity({"touches": 25})
        missing = evaluate_tracking_opportunity({})
        self.assertEqual(full["tracking_status"], "ok")
        self.assertEqual(partial["tracking_status"], "partial")
        self.assertEqual(missing["tracking_status"], "missing")
        high_tracking = run_basketball_player_impact(candidate(lineup_net_rating=0, defensive_matchup_rating=50), outcome_records=settled_records())
        self.assertGreater(high_tracking["market_relevance_scores"]["points_prop"], high_tracking["market_relevance_scores"]["spread"])

    def test_role_classifier_and_role_adjusted_scores(self):
        primary = evaluate_role_context(candidate(role_label="", usage_rate=32, assist_rate=28))
        shooter = evaluate_role_context(candidate(role_label="spot_up_shooter", usage_rate=15, assist_rate=7, three_point_attempt_rate=0.58))
        missing = evaluate_role_context({})
        changed = evaluate_role_context(candidate(teammate_absence_usage_shift=6))
        self.assertEqual(primary["player_role"], "primary_creator")
        self.assertEqual(shooter["player_role"], "spot_up_shooter")
        self.assertNotEqual(primary["role_adjusted_efficiency_score"], shooter["role_adjusted_efficiency_score"])
        self.assertLess(missing["role_confidence"], 40)
        self.assertTrue(changed["role_change_detected"])

    def test_lineup_matchup_usage_shift_blowout_and_matchup_effects(self):
        injured = run_basketball_player_impact(
            candidate(teammate_injuries=[{"player_id": "p2", "high_usage": True}], teammate_usage_absences=["p2"]),
            outcome_records=settled_records(),
        )
        low_blowout = run_basketball_player_impact(candidate(blowout_risk=5), outcome_records=settled_records())
        high_blowout = run_basketball_player_impact(candidate(blowout_risk=92), outcome_records=settled_records())
        good_matchup = run_basketball_player_impact(candidate(defensive_matchup_rating=80), outcome_records=settled_records())
        bad_matchup = run_basketball_player_impact(candidate(defensive_matchup_rating=25), outcome_records=settled_records())
        missing_lineup = run_basketball_player_impact(candidate(projected_starting_lineup=[]), outcome_records=settled_records())
        self.assertGreater(injured["lineup_matchup_context"]["teammate_absence_usage_shift"], 0)
        self.assertGreater(low_blowout["market_relevance_scores"]["points_prop"], high_blowout["market_relevance_scores"]["points_prop"])
        self.assertGreater(good_matchup["market_relevance_scores"]["points_prop"], bad_matchup["market_relevance_scores"]["points_prop"])
        self.assertEqual(missing_lineup["lineup_matchup_context"]["lineup_matchup_status"], "partial")

    def test_availability_minutes_injury_and_foul_risk(self):
        stable = run_basketball_player_impact(candidate(minutes_volatility=1.0), outcome_records=settled_records())
        volatile = run_basketball_player_impact(candidate(minutes_volatility=13.0), outcome_records=settled_records())
        available = evaluate_availability_minutes(candidate(injury_designation="available"))
        questionable = evaluate_availability_minutes(candidate(injury_designation="questionable"))
        low_foul = run_basketball_player_impact(candidate(foul_trouble_rate=0.02), outcome_records=settled_records())
        high_foul = run_basketball_player_impact(candidate(foul_trouble_rate=0.20), outcome_records=settled_records())
        self.assertGreater(stable["market_relevance_scores"]["points_prop"], volatile["market_relevance_scores"]["points_prop"])
        self.assertGreater(available["availability_score"], questionable["availability_score"])
        self.assertGreater(low_foul["market_relevance_scores"]["blocks_steals_prop"], high_foul["market_relevance_scores"]["blocks_steals_prop"])

    def test_incentives_are_modifiers_not_standalone_edges(self):
        unknown = evaluate_incentive_context({})
        incentive_only = run_basketball_player_impact(
            {
                "sport": "basketball_nba",
                "player_id": "player-1",
                "contract_year": True,
                "points_incentive": {"distance_to_threshold": 0.5},
            }
        )
        baseline = run_basketball_player_impact(candidate(), outcome_records=settled_records())
        pressured = run_basketball_player_impact(
            candidate(
                points_incentive={"distance_to_threshold": 0.5},
                contract_year=True,
                trade_showcase_risk=85,
                team_motivation_context=20,
            ),
            outcome_records=settled_records(),
        )
        self.assertEqual(unknown["incentive_status"], "unknown")
        self.assertNotEqual(incentive_only["recommended_review_status"], "ACTIVE_REVIEW")
        self.assertGreaterEqual(pressured["market_relevance_scores"]["points_prop"], baseline["market_relevance_scores"]["points_prop"])
        self.assertLessEqual(pressured["market_relevance_scores"]["spread"], baseline["market_relevance_scores"]["spread"])
        self.assertIn("player_incentive_may_conflict_with_team_market", pressured["incentive_context"]["incentive_warning_flags"])

    def test_market_relevance_uses_market_specific_inputs(self):
        points = run_basketball_player_impact(candidate(usage_rate=33, touches=88, shot_attempt_rate=25), outcome_records=settled_records())
        assists = run_basketball_player_impact(candidate(potential_assists=18, time_of_possession=8.4, teammate_shot_quality=82), outcome_records=settled_records())
        rebounds = run_basketball_player_impact(candidate(rebound_chances=18, contested_rebound_chances=9, opponent_missed_shot_environment=80), outcome_records=settled_records())
        threes = run_basketball_player_impact(candidate(three_point_attempt_rate=0.62, catch_and_shoot_attempts=10, pull_up_attempts=9), outcome_records=settled_records())
        stocks = run_basketball_player_impact(candidate(deflections=8, help_defense_impact=80, opponent_rim_attempt_rate=0.46, opponent_turnover_rate=0.21), outcome_records=settled_records())
        totals = run_basketball_player_impact(candidate(lineup_pace=104, opponent_pace=103, game_total=248), outcome_records=settled_records())
        self.assertGreater(points["market_relevance_scores"]["points_prop"], 70)
        self.assertGreater(assists["market_relevance_scores"]["assists_prop"], 75)
        self.assertGreater(rebounds["market_relevance_scores"]["rebounds_prop"], 60)
        self.assertGreater(threes["market_relevance_scores"]["threes_prop"], 65)
        self.assertGreater(stocks["market_relevance_scores"]["blocks_steals_prop"], 50)
        self.assertGreater(totals["market_relevance_scores"]["total"], 55)

    def test_calibration_missing_and_market_specific_shape(self):
        missing = evaluate_basketball_player_impact_calibration(candidate(), [])
        calibrated = evaluate_basketball_player_impact_calibration(
            candidate(),
            settled_records(130, "points_prop") + settled_records(105, "spread"),
        )
        self.assertTrue(missing["insufficient_sample"])
        self.assertIn("props", missing["market_specific_calibration"])
        self.assertIn("points_prop", calibrated["market_specific_calibration"])
        self.assertIn("spread", calibrated["market_specific_calibration"])
        self.assertFalse(calibrated["market_specific_calibration"]["points_prop"]["insufficient_sample"])

    def test_readiness_endpoint_lists_feasible_and_not_implemented(self):
        response = asyncio.run(get_automation_basketball_player_impact_readiness_endpoint(verbose=False, include_debug=False, limit=20))
        self.assertIn("possession_level_impact", response["feasible_now"])
        self.assertIn("graph_neural_networks", response["not_implemented"])
        self.assertIn("counterfactual_causal_gans", response["not_implemented"])
        self.assertIn("rl_micro_action_decision_quality", response["not_implemented"])
        self.assertIn("multimodal_foundation_models", response["not_implemented"])
        self.assert_safe(response)

    def test_main_endpoint_returns_compact_safe_response_and_dry_run_gate(self):
        response = asyncio.run(
            automation_basketball_player_impact_endpoint(
                AutomationBasketballPlayerImpactRequest(candidate=candidate(), outcome_records=settled_records()),
                verbose=False,
                include_debug=False,
                limit=20,
            )
        )
        self.assert_safe(response)
        self.assertEqual(response["status"], "basketball_player_impact_complete")
        with self.assertRaises(HTTPException):
            asyncio.run(
                automation_basketball_player_impact_endpoint(
                    AutomationBasketballPlayerImpactRequest(dry_run=False, candidate=candidate()),
                    verbose=False,
                    include_debug=False,
                    limit=20,
                )
            )

    def test_red_team_downgrades_but_cannot_approve_or_create_bet_slip(self):
        weak = run_basketball_player_impact(candidate(possessions_played=None, touches=None), outcome_records=[])
        self.assertIn(weak["red_team"]["player_impact_red_team_status"], {"downgrade", "watch"})
        self.assertFalse(weak["red_team"]["approval_granted"])
        self.assertFalse(weak["red_team"]["bet_slip_created"])
        self.assert_safe(weak["red_team"])

    def test_readiness_compactor_is_safe_and_bounded(self):
        compact = compact_basketball_player_impact_readiness_response(build_basketball_player_impact_readiness(), limit=3)
        self.assertLessEqual(len(compact["feasible_now"]), 3)
        self.assert_safe(compact)


if __name__ == "__main__":
    unittest.main()
