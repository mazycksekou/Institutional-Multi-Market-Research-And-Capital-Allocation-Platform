import unittest

from fastapi.testclient import TestClient

from automation_scheduler.response_compactor import compact_tennis_impact_diagnostics_response, redact_and_limit_payload
from automation_scheduler.tennis_availability_context import evaluate_tennis_availability_context
from automation_scheduler.tennis_data_availability import evaluate_tennis_data_availability
from automation_scheduler.tennis_format_markov_context import evaluate_tennis_format_markov_context
from automation_scheduler.tennis_impact_calibration import evaluate_tennis_impact_calibration
from automation_scheduler.tennis_impact_readiness import build_tennis_impact_readiness
from automation_scheduler.tennis_impact_red_team import evaluate_tennis_impact_red_team
from automation_scheduler.tennis_impact_report import build_tennis_impact_diagnostics
from automation_scheduler.tennis_incentive_context import evaluate_tennis_incentive_context
from automation_scheduler.tennis_market_relevance import evaluate_tennis_market_relevance
from automation_scheduler.tennis_matchup_context import evaluate_tennis_matchup_context
from automation_scheduler.tennis_pressure_tiebreak_context import evaluate_tennis_pressure_tiebreak_context
from automation_scheduler.tennis_return_impact import evaluate_tennis_return_impact
from automation_scheduler.tennis_serve_impact import evaluate_tennis_serve_impact
from automation_scheduler.tennis_surface_context import evaluate_tennis_surface_context
from tests.support.action_imports import app


def _match_context(**extra):
    row = {
        "tour": "atp",
        "tournament": "sample_event",
        "surface": "hard",
        "best_of": 3,
    }
    row.update(extra)
    return row


def _player_a_context(**extra):
    row = {
        "player_a_id": "player_a",
        "player_a_name": "Sample Player A",
        "player_a_ranking_proxy": 18,
    }
    row.update(extra)
    return row


def _player_b_context(**extra):
    row = {
        "player_b_id": "player_b",
        "player_b_name": "Sample Player B",
        "player_b_ranking_proxy": 32,
    }
    row.update(extra)
    return row


def _serve_context(**extra):
    row = {
        "player_a_hold_percentage": 0.84,
        "player_b_hold_percentage": 0.81,
        "player_a_first_serve_percentage": 0.63,
        "player_b_first_serve_percentage": 0.61,
        "player_a_first_serve_points_won": 0.73,
        "player_b_first_serve_points_won": 0.70,
        "player_a_second_serve_points_won": 0.53,
        "player_b_second_serve_points_won": 0.50,
        "player_a_ace_rate": 0.095,
        "player_b_ace_rate": 0.082,
        "player_a_double_fault_rate": 0.034,
        "player_b_double_fault_rate": 0.041,
        "break_points_saved": 0.63,
        "sample_size": 40,
    }
    row.update(extra)
    return row


def _return_context(**extra):
    row = {
        "player_a_break_percentage": 0.24,
        "player_b_break_percentage": 0.21,
        "player_a_return_points_won": 0.392,
        "player_b_return_points_won": 0.374,
        "first_serve_return_points_won": 0.31,
        "second_serve_return_points_won": 0.54,
        "break_points_created_rate": 0.22,
        "break_points_converted": 0.41,
        "sample_size": 40,
    }
    row.update(extra)
    return row


def _surface_context(**extra):
    row = {
        "surface": "hard",
        "indoor": False,
        "player_a_surface_win_rate": 0.61,
        "player_b_surface_win_rate": 0.55,
        "player_a_surface_hold_rate": 0.83,
        "player_b_surface_hold_rate": 0.79,
        "player_a_surface_break_rate": 0.25,
        "player_b_surface_break_rate": 0.21,
        "sample_size_surface": 42,
    }
    row.update(extra)
    return row


def _format_context(**extra):
    row = {
        "best_of": 3,
        "player_a_hold_probability": 0.84,
        "player_b_hold_probability": 0.81,
        "player_a_break_probability": 0.24,
        "player_b_break_probability": 0.21,
        "tiebreak_probability": 0.34,
        "first_set_tiebreak_probability": 0.28,
        "match_win_probability": 0.56,
        "set_win_probability": 0.55,
        "total_games_projection": 23.8,
        "game_handicap_projection": -2.5,
        "sample_size": 40,
    }
    row.update(extra)
    return row


def _pressure_context(**extra):
    row = {
        "break_points_saved": 0.63,
        "break_points_converted": 0.41,
        "pressure_points_won": 0.53,
        "tiebreak_win_rate": 0.56,
        "tiebreak_points_won": 0.52,
        "first_set_tiebreak_rate": 0.23,
        "tiebreaks_played_rate": 0.28,
        "close_set_win_rate": 0.54,
        "first_set_win_rate": 0.55,
        "recent_tiebreak_sample": 16,
        "long_term_tiebreak_sample": 40,
    }
    row.update(extra)
    return row


def _matchup_context(**extra):
    row = {
        "player_a_handedness": "R",
        "player_b_handedness": "L",
        "lefty_vs_righty_context": 0.56,
        "backhand_weakness_proxy": 0.62,
        "forehand_strength_proxy": 0.66,
        "return_position": 0.55,
        "serve_direction_preference": 0.60,
        "short_rally_win_rate": 0.54,
        "medium_rally_win_rate": 0.52,
        "long_rally_win_rate": 0.51,
        "baseline_consistency_proxy": 0.60,
        "winner_error_ratio": 1.1,
        "movement_defense_score": 0.58,
        "previous_head_to_head_context": {"matches": 3, "win_rate": 0.67},
    }
    row.update(extra)
    return row


def _availability_context(**extra):
    row = {
        "injury_status": "healthy",
        "withdrawal_risk": 0.03,
        "recent_match_minutes": 112,
        "recent_sets_played": 3,
        "matches_last_7_days": 2,
        "rest_days": 2,
        "travel_distance": 500,
        "time_zone_change": 1,
    }
    row.update(extra)
    return row


def _incentive_context(**extra):
    row = {
        "ranking_points_context": "relevant",
        "race_points_context": "relevant",
        "home_country_context": "neutral",
    }
    row.update(extra)
    return row


def _calibration_context(**extra):
    row = {"matched_outcomes_count": 0}
    row.update(extra)
    return row


def _full_report(**overrides):
    payload = {
        "sport": "tennis",
        "market_type": "total_games",
        "match_context": _match_context(),
        "player_a_context": _player_a_context(),
        "player_b_context": _player_b_context(),
        "serve_context": _serve_context(),
        "return_context": _return_context(),
        "surface_context": _surface_context(),
        "format_context": _format_context(),
        "pressure_context": _pressure_context(),
        "tiebreak_context": _pressure_context(),
        "matchup_context": _matchup_context(),
        "availability_context": _availability_context(),
        "incentive_context": _incentive_context(),
        "calibration_context": _calibration_context(),
    }
    payload.update(overrides)
    return build_tennis_impact_diagnostics(**payload)


def _red_team_with_claims(claims, **extra):
    data = evaluate_tennis_data_availability("tennis", market_type=extra.pop("market_type", "moneyline"))
    calibration = evaluate_tennis_impact_calibration({"matched_outcomes_count": 0})
    source_payload = {"claimed_metrics": list(claims), **extra.pop("source_payload", {})}
    return evaluate_tennis_impact_red_team(
        market_type=extra.pop("market", "moneyline"),
        data_availability=data,
        surface_context=extra.pop("surface_context", {}),
        format_markov_context=extra.pop("format_markov_context", {}),
        matchup_context=extra.pop("matchup_context", {}),
        pressure_tiebreak_context=extra.pop("pressure_tiebreak_context", {}),
        availability_context=extra.pop("availability_context", {}),
        incentive_context=extra.pop("incentive_context", {}),
        calibration=extra.pop("calibration", calibration),
        source_payload=source_payload,
    )


class TestTennisImpactIntelligence(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_001_tennis_tier_0_returns_data_insufficient(self):
        report = build_tennis_impact_diagnostics(sport="tennis", market_type="moneyline")
        self.assertEqual(report["data_tier"], 0)
        self.assertEqual(report["recommended_review_status"], "DATA_INSUFFICIENT")

    def test_002_missing_point_by_point_data_does_not_fail(self):
        report = _full_report(point_context={})
        self.assertTrue(report["ok"])
        self.assertFalse(report["point_level_allowed"])

    def test_003_missing_tracking_data_does_not_fail(self):
        report = _full_report(tracking_context={}, matchup_context=_matchup_context(return_position=None))
        self.assertTrue(report["ok"])
        self.assertFalse(report["tracking_level_allowed"])

    def test_004_missing_serve_placement_does_not_fail(self):
        result = evaluate_tennis_serve_impact(_serve_context())
        self.assertFalse(result["serve_placement_fabricated"])
        self.assertIn("serve_placement_wide_rate", result["missing_inputs"])

    def test_005_missing_serve_speed_does_not_fail(self):
        result = evaluate_tennis_serve_impact(_serve_context())
        self.assertFalse(result["serve_speed_fabricated"])
        self.assertIn("serve_speed_average", result["missing_inputs"])

    def test_006_missing_return_position_does_not_fail(self):
        result = evaluate_tennis_matchup_context(_matchup_context(return_position=None))
        self.assertFalse(result["execution_allowed"])
        self.assertIn("return_position", result["missing_inputs"])

    def test_007_missing_shot_pattern_does_not_fail(self):
        result = evaluate_tennis_matchup_context({})
        self.assertFalse(result["shot_pattern_fabricated"])
        self.assertIn("shot_pattern_missing_no_style_claim", result["no_bet_reasons"])

    def test_008_missing_court_speed_does_not_fail(self):
        result = evaluate_tennis_surface_context(_surface_context(court_speed_index=None))
        self.assertFalse(result["court_speed_fabricated"])
        self.assertIn("court_speed_missing_no_court_speed_claim", result["no_bet_reasons"])

    def test_009_missing_ball_type_does_not_fail(self):
        result = evaluate_tennis_surface_context(_surface_context(ball_type=None))
        self.assertFalse(result["ball_type_fabricated"])
        self.assertIn("ball_type_missing_no_ball_type_claim", result["no_bet_reasons"])

    def test_010_missing_injury_retirement_data_does_not_fail(self):
        result = evaluate_tennis_availability_context({})
        self.assertFalse(result["injury_status_fabricated"])
        self.assertFalse(result["retirement_risk_fabricated"])

    def test_011_tier_1_basic_data_caps_confidence(self):
        data = evaluate_tennis_data_availability(
            "tennis",
            market_type="moneyline",
            match_context=_match_context(),
            player_a_context=_player_a_context(),
            player_b_context=_player_b_context(),
        )
        self.assertEqual(data["data_tier"], 1)
        self.assertLessEqual(data["confidence_cap"], 42.0)

    def test_012_tier_2_serve_return_summary_enables_limited_diagnostics(self):
        data = evaluate_tennis_data_availability(
            "tennis",
            market_type="total_games",
            match_context=_match_context(),
            player_a_context=_player_a_context(),
            player_b_context=_player_b_context(),
            serve_context={"hold_percentage": 0.82, "first_serve_percentage": 0.63, "sample_size": 40},
            return_context={"break_percentage": 0.23, "return_points_won": 0.39, "sample_size": 40},
        )
        self.assertEqual(data["data_tier"], 2)
        self.assertTrue(data["serve_return_allowed"])

    def test_013_tier_3_surface_point_pressure_data_enables_stronger_diagnostics(self):
        data = evaluate_tennis_data_availability(
            "tennis",
            market_type="game_handicap",
            match_context=_match_context(),
            player_a_context=_player_a_context(),
            player_b_context=_player_b_context(),
            serve_context=_serve_context(surface_adjusted_hold_rate=0.84),
            return_context=_return_context(surface_adjusted_break_rate=0.24),
            pressure_context=_pressure_context(),
            point_context={"point_by_point": [{"server": "a", "winner": "a"}]},
        )
        self.assertEqual(data["data_tier"], 3)
        self.assertTrue(data["serve_return_allowed"])

    def test_014_tier_4_tracking_shot_pattern_optional_never_required(self):
        data = evaluate_tennis_data_availability(
            "tennis",
            match_context=_match_context(),
            player_a_context=_player_a_context(),
            player_b_context=_player_b_context(),
            tracking_context={"tracking_context": True, "serve_speed_average": 121},
        )
        self.assertEqual(data["data_tier"], 4)
        self.assertTrue(data["tracking_level_allowed"])

    def test_015_hold_percentage_affects_serve_score(self):
        low = evaluate_tennis_serve_impact(_serve_context(player_a_hold_percentage=0.68, player_b_hold_percentage=0.68))
        high = evaluate_tennis_serve_impact(_serve_context(player_a_hold_percentage=0.88, player_b_hold_percentage=0.86))
        self.assertGreater(high["hold_stability_score"], low["hold_stability_score"])

    def test_016_first_serve_percentage_affects_serve_stability(self):
        low = evaluate_tennis_serve_impact(_serve_context(player_a_first_serve_percentage=0.54, player_b_first_serve_percentage=0.54))
        high = evaluate_tennis_serve_impact(_serve_context(player_a_first_serve_percentage=0.70, player_b_first_serve_percentage=0.68))
        self.assertGreater(high["first_serve_score"], low["first_serve_score"])

    def test_017_first_serve_points_won_affects_serve_quality(self):
        low = evaluate_tennis_serve_impact(_serve_context(player_a_first_serve_points_won=0.63, player_b_first_serve_points_won=0.63))
        high = evaluate_tennis_serve_impact(_serve_context(player_a_first_serve_points_won=0.80, player_b_first_serve_points_won=0.77))
        self.assertGreater(high["first_serve_score"], low["first_serve_score"])

    def test_018_second_serve_points_won_affects_break_risk_protection(self):
        low = evaluate_tennis_serve_impact(_serve_context(player_a_second_serve_points_won=0.44, player_b_second_serve_points_won=0.44))
        high = evaluate_tennis_serve_impact(_serve_context(player_a_second_serve_points_won=0.58, player_b_second_serve_points_won=0.56))
        self.assertGreater(high["second_serve_resilience_score"], low["second_serve_resilience_score"])

    def test_019_ace_rate_affects_ace_tiebreak_total_relevance(self):
        low = evaluate_tennis_serve_impact(_serve_context(player_a_ace_rate=0.03, player_b_ace_rate=0.03))
        high = evaluate_tennis_serve_impact(_serve_context(player_a_ace_rate=0.14, player_b_ace_rate=0.12))
        self.assertGreater(high["ace_prop_relevance"], low["ace_prop_relevance"])

    def test_020_double_fault_rate_affects_volatility_and_break_risk(self):
        result = evaluate_tennis_serve_impact(_serve_context(player_a_double_fault_rate=0.08, player_b_double_fault_rate=0.08))
        self.assertGreaterEqual(result["double_fault_risk_score"], 90)
        self.assertIn("double_fault_risk_increases_break_volatility", result["no_bet_reasons"])

    def test_021_break_points_saved_is_sample_size_capped(self):
        result = evaluate_tennis_serve_impact(_serve_context(break_points_saved=0.70, sample_size=12))
        self.assertIn("break_points_saved_sample_size_capped", result["no_bet_reasons"])

    def test_022_missing_serve_placement_does_not_fabricate_placement(self):
        result = evaluate_tennis_serve_impact(_serve_context())
        self.assertFalse(result["serve_placement_fabricated"])

    def test_023_missing_serve_speed_does_not_fabricate_speed(self):
        result = evaluate_tennis_serve_impact(_serve_context())
        self.assertFalse(result["serve_speed_fabricated"])

    def test_024_limited_hold_only_proxy_is_confidence_capped(self):
        result = evaluate_tennis_serve_impact({"hold_percentage": 0.82, "sample_size": 40})
        self.assertTrue(result["limited_proxy"])
        self.assertEqual(result["confidence_cap_reason"], "hold_percentage_limited_proxy_confidence_capped")

    def test_025_break_percentage_affects_return_score(self):
        low = evaluate_tennis_return_impact(_return_context(player_a_break_percentage=0.13, player_b_break_percentage=0.13))
        high = evaluate_tennis_return_impact(_return_context(player_a_break_percentage=0.34, player_b_break_percentage=0.32))
        self.assertGreater(high["break_threat_score"], low["break_threat_score"])

    def test_026_return_points_won_affects_break_threat(self):
        low = evaluate_tennis_return_impact(_return_context(player_a_return_points_won=0.34, player_b_return_points_won=0.34))
        high = evaluate_tennis_return_impact(_return_context(player_a_return_points_won=0.45, player_b_return_points_won=0.43))
        self.assertGreater(high["return_impact_score"], low["return_impact_score"])

    def test_027_first_serve_return_points_won_works_where_supplied(self):
        result = evaluate_tennis_return_impact(_return_context(first_serve_return_points_won=0.38))
        self.assertGreater(result["first_serve_return_score"], 70)

    def test_028_second_serve_attack_works_where_supplied(self):
        result = evaluate_tennis_return_impact(_return_context(second_serve_return_points_won=0.60))
        self.assertGreater(result["second_serve_attack_score"], 70)

    def test_029_break_points_converted_is_volatility_capped(self):
        result = evaluate_tennis_return_impact(_return_context(break_points_converted=0.48))
        self.assertIn("break_point_conversion_sample_size_capped", evaluate_tennis_return_impact(_return_context(break_points_converted=0.48, sample_size=15))["no_bet_reasons"])
        self.assertGreater(result["break_point_conversion_score"], 0)

    def test_030_missing_return_depth_does_not_fabricate_return_depth(self):
        result = evaluate_tennis_return_impact(_return_context(return_depth_proxy=None))
        self.assertFalse(result["return_depth_fabricated"])
        self.assertIn("return_depth_proxy", result["missing_inputs"])

    def test_031_strong_return_vs_weak_second_serve_affects_handicap_under(self):
        result = evaluate_tennis_return_impact(_return_context(second_serve_return_points_won=0.60, player_a_break_percentage=0.35, player_b_break_percentage=0.34))
        self.assertIn("strong_return_vs_weak_second_serve_affects_handicap_under", result["no_bet_reasons"])

    def test_032_limited_break_only_proxy_is_confidence_capped(self):
        result = evaluate_tennis_return_impact({"break_percentage": 0.24, "sample_size": 40})
        self.assertTrue(result["limited_proxy"])
        self.assertEqual(result["confidence_cap_reason"], "break_percentage_limited_proxy_confidence_capped")

    def test_033_surface_specific_hold_break_modifies_relevance(self):
        result = evaluate_tennis_surface_context(_surface_context())
        self.assertGreater(result["surface_hold_break_modifier"], 0)

    def test_034_missing_surface_caps_confidence(self):
        result = evaluate_tennis_surface_context(_surface_context(surface=None))
        self.assertIn("surface_missing_caps_surface_matchup", result["no_bet_reasons"])

    def test_035_court_speed_works_only_if_supplied(self):
        missing = evaluate_tennis_surface_context(_surface_context(court_speed_index=None))
        supplied = evaluate_tennis_surface_context(_surface_context(court_speed_index=0.72))
        self.assertEqual(missing["court_speed_fit_score"], 0)
        self.assertGreater(supplied["court_speed_fit_score"], 0)

    def test_036_indoor_outdoor_works_only_if_supplied(self):
        result = evaluate_tennis_surface_context(_surface_context(indoor=True))
        self.assertGreater(result["indoor_outdoor_fit_score"], 50)

    def test_037_altitude_modifies_ace_hold_tiebreak_only_if_supplied(self):
        result = evaluate_tennis_surface_context(_surface_context(altitude=4200))
        self.assertIn("altitude_modifies_ace_hold_tiebreak_only_when_supplied", result["no_bet_reasons"])

    def test_038_ball_type_is_not_fabricated(self):
        result = evaluate_tennis_surface_context(_surface_context(ball_type=None))
        self.assertFalse(result["ball_type_fabricated"])

    def test_039_small_surface_sample_caps_confidence(self):
        result = evaluate_tennis_surface_context(_surface_context(sample_size_surface=8))
        self.assertIn("surface_split_small_sample_capped", result["no_bet_reasons"])

    def test_040_best_of_three_context_works(self):
        result = evaluate_tennis_format_markov_context(_format_context(best_of=3))
        self.assertEqual(result["best_of"], 3)

    def test_041_best_of_five_context_changes_fatigue_score_distribution(self):
        result = evaluate_tennis_format_markov_context(_format_context(best_of=5))
        self.assertEqual(result["best_of"], 5)
        self.assertIn("best_of_five_changes_fatigue_comeback_dynamics", result["no_bet_reasons"])

    def test_042_hold_break_balance_affects_total_games(self):
        result = evaluate_tennis_format_markov_context(_format_context())
        self.assertGreater(result["total_games_relevance_score"], 0)

    def test_043_tiebreak_probability_affects_tiebreak_markets(self):
        low = evaluate_tennis_format_markov_context(_format_context(tiebreak_probability=0.10))
        high = evaluate_tennis_format_markov_context(_format_context(tiebreak_probability=0.60))
        self.assertGreater(high["tiebreak_relevance_score"], low["tiebreak_relevance_score"])

    def test_044_correct_score_is_heavily_calibration_capped(self):
        result = evaluate_tennis_format_markov_context(_format_context(correct_score_distribution={"2_0": 0.42, "2_1": 0.31}))
        self.assertEqual(result["format_confidence_cap"], "correct_score_extra_capped")
        self.assertIn("correct_score_heavily_calibration_capped", result["no_bet_reasons"])

    def test_045_missing_best_of_caps_correct_score_total_sets_confidence(self):
        result = evaluate_tennis_format_markov_context(_format_context(best_of=None))
        self.assertEqual(result["format_confidence_cap"], "best_of_missing")
        self.assertIn("best_of_missing_caps_correct_score_total_sets", result["no_bet_reasons"])

    def test_046_retirement_risk_caps_all_markets_where_supplied(self):
        result = evaluate_tennis_format_markov_context(_format_context(retire_or_walkover_risk=0.75))
        self.assertIn("retirement_risk_caps_all_match_set_game_markets", result["no_bet_reasons"])

    def test_047_markov_distribution_is_not_fabricated_beyond_limited_proxy(self):
        result = evaluate_tennis_format_markov_context({"player_a_hold_probability": 0.84, "player_b_hold_probability": 0.82, "sample_size": 40})
        self.assertFalse(result["markov_distribution_fabricated"])
        self.assertTrue(result["limited_proxy"])

    def test_048_handedness_matchup_works_where_supplied(self):
        result = evaluate_tennis_matchup_context(_matchup_context())
        self.assertGreater(result["handedness_matchup_score"], 0)

    def test_049_missing_handedness_does_not_fabricate_handedness(self):
        result = evaluate_tennis_matchup_context(_matchup_context(player_a_handedness=None, player_b_handedness=None))
        self.assertFalse(result["handedness_fabricated"])
        self.assertIn("handedness_missing_no_handedness_claim", result["no_bet_reasons"])

    def test_050_shot_pattern_matchup_works_where_supplied(self):
        result = evaluate_tennis_matchup_context(_matchup_context())
        self.assertGreater(result["rally_matchup_score"], 0)

    def test_051_missing_shot_pattern_does_not_fabricate_style(self):
        result = evaluate_tennis_matchup_context({})
        self.assertFalse(result["shot_pattern_fabricated"])
        self.assertIn("shot_pattern_missing_no_style_claim", result["no_bet_reasons"])

    def test_052_rally_length_preference_works_where_supplied(self):
        result = evaluate_tennis_matchup_context(_matchup_context(rally_length_preference="short"))
        self.assertGreater(result["rally_matchup_score"], 0)

    def test_053_head_to_head_is_low_weight_and_sample_size_capped(self):
        result = evaluate_tennis_matchup_context(_matchup_context(previous_head_to_head_context={"matches": 2, "win_rate": 1.0}))
        self.assertLess(result["head_to_head_weight"], 0.08)
        self.assertIn("head_to_head_low_weight_sample_capped", result["no_bet_reasons"])

    def test_054_conflicting_matchup_signals_reduce_confidence(self):
        result = evaluate_tennis_matchup_context(
            _matchup_context(
                serve_direction_preference=1.0,
                return_position=0.0,
                short_rally_win_rate=0.58,
                medium_rally_win_rate=0.44,
                long_rally_win_rate=0.44,
            )
        )
        self.assertIn("conflicting_matchup_signals_reduce_confidence", result["no_bet_reasons"])

    def test_055_tiebreak_rate_affects_tiebreak_relevance(self):
        low = evaluate_tennis_pressure_tiebreak_context(_pressure_context(tiebreaks_played_rate=0.08))
        high = evaluate_tennis_pressure_tiebreak_context(_pressure_context(tiebreaks_played_rate=0.38))
        self.assertGreater(high["tiebreak_likelihood_modifier"], low["tiebreak_likelihood_modifier"])

    def test_056_tiebreak_win_rate_is_sample_size_capped(self):
        result = evaluate_tennis_pressure_tiebreak_context(_pressure_context(tiebreak_win_rate=0.60, recent_tiebreak_sample=5, long_term_tiebreak_sample=5))
        self.assertEqual(result["pressure_confidence_cap"], "tiebreak_sample_size_capped")
        self.assertIn("tiebreak_record_sample_size_capped", result["no_bet_reasons"])

    def test_057_break_point_pressure_works_where_supplied(self):
        result = evaluate_tennis_pressure_tiebreak_context(_pressure_context(break_points_saved=0.70, break_points_converted=0.48))
        self.assertGreater(result["break_point_pressure_score"], 0)

    def test_058_close_set_record_is_volatility_capped(self):
        result = evaluate_tennis_pressure_tiebreak_context(_pressure_context(close_set_win_rate=0.42))
        self.assertGreater(result["close_set_volatility_score"], 0)

    def test_059_clutch_narrative_does_not_create_standalone_edge(self):
        result = evaluate_tennis_pressure_tiebreak_context(_pressure_context(clutch_proxy=0.95))
        self.assertFalse(result["clutch_is_standalone_edge"])
        self.assertIn("clutch_proxy_modifier_only_not_standalone_edge", result["no_bet_reasons"])

    def test_060_pressure_double_fault_risk_affects_no_bet_logic(self):
        result = evaluate_tennis_pressure_tiebreak_context(_pressure_context(pressure_double_fault_rate=0.09))
        self.assertIn("pressure_double_fault_risk_no_bet_logic", result["no_bet_reasons"])

    def test_061_injury_uncertainty_caps_all_markets(self):
        result = evaluate_tennis_availability_context(_availability_context(injury_status="questionable"))
        self.assertEqual(result["confidence_cap_reason"], "injury_uncertainty_caps_all_markets")

    def test_062_retirement_risk_creates_hard_warning(self):
        result = evaluate_tennis_availability_context(_availability_context(withdrawal_risk=0.70))
        self.assertIn("retirement_risk_hard_warning", result["no_bet_reasons"])

    def test_063_recent_match_minutes_affects_fatigue(self):
        low = evaluate_tennis_availability_context(_availability_context(recent_match_minutes=70))
        high = evaluate_tennis_availability_context(_availability_context(recent_match_minutes=240))
        self.assertGreater(high["fatigue_score"], low["fatigue_score"])

    def test_064_recent_five_set_match_affects_fatigue(self):
        result = evaluate_tennis_availability_context(_availability_context(five_set_match_recent=True))
        self.assertIn("recent_five_set_match_affects_fatigue", result["no_bet_reasons"])

    def test_065_back_to_back_match_affects_schedule_risk(self):
        result = evaluate_tennis_availability_context(_availability_context(back_to_back_match=True))
        self.assertGreater(result["schedule_load_score"], 0)

    def test_066_surface_change_creates_timing_risk(self):
        result = evaluate_tennis_availability_context(_availability_context(surface_change_recent=True))
        self.assertIn("surface_change_creates_timing_risk", result["no_bet_reasons"])

    def test_067_travel_time_zone_affects_volatility(self):
        high = evaluate_tennis_availability_context(_availability_context(travel_distance=6500, time_zone_change=8))
        self.assertGreater(high["travel_adjustment_score"], 80)

    def test_068_do_not_fabricate_injury_status(self):
        result = evaluate_tennis_availability_context({})
        self.assertFalse(result["injury_status_fabricated"])

    def test_069_incentive_context_is_modifier_only(self):
        result = evaluate_tennis_incentive_context(_incentive_context())
        self.assertEqual(result["incentive_context_status"], "modifier_only")
        self.assertFalse(result["incentive_is_standalone_edge"])

    def test_070_ranking_race_points_modify_only_if_supplied(self):
        result = evaluate_tennis_incentive_context({"ranking_points_context": "relevant", "race_points_context": "relevant"})
        self.assertGreater(result["confidence_modifier"], 0)

    def test_071_home_country_context_is_modifier_only(self):
        result = evaluate_tennis_incentive_context({"home_country_context": "home_event"})
        self.assertFalse(result["incentive_is_standalone_edge"])

    def test_072_retirement_announcement_context_modifies_risk_only_if_supplied(self):
        result = evaluate_tennis_incentive_context({"retirement_announcement_context": "announced"})
        self.assertGreater(result["retirement_or_shutdown_risk"], 0)

    def test_073_narrative_overfit_is_downgraded(self):
        result = evaluate_tennis_incentive_context({"home_country_context": "home_event"})
        self.assertEqual(result["narrative_overfit_risk"], "high")
        self.assertIn("weak_incentive_evidence_narrative_overfit_risk", result["no_bet_reasons"])

    def test_074_moneyline_relevance_links_hold_break_surface_matchup_fatigue(self):
        report = _full_report(market_type="moneyline")
        self.assertIn("moneyline", report["market_relevance"]["moneyline_relevance"])

    def test_075_set_handicap_relevance_links_serve_return_separation_volatility(self):
        report = _full_report(market_type="set_handicap")
        self.assertIn("set_handicap", report["market_relevance"]["handicap_relevance"])

    def test_076_game_handicap_relevance_links_hold_break_game_distribution(self):
        report = _full_report(market_type="game_handicap")
        self.assertIn("game_handicap", report["market_relevance"]["handicap_relevance"])

    def test_077_total_games_relevance_links_hold_rates_tiebreak_surface(self):
        report = _full_report(market_type="total_games")
        self.assertIn("total_games", report["market_relevance"]["total_games_relevance"])

    def test_078_correct_score_relevance_is_heavily_capped(self):
        report = _full_report(market_type="correct_score", format_context=_format_context(correct_score_distribution={"2_0": 0.42}))
        self.assertIn("correct_score", report["market_relevance"]["market_confidence_caps"])

    def test_079_first_set_relevance_links_first_set_hold_break_context(self):
        report = _full_report(market_type="first_set_winner", pressure_context=_pressure_context(first_set_win_rate=0.60))
        self.assertIn("first_set_winner", report["market_relevance"]["set_market_relevance"])

    def test_080_tiebreak_relevance_links_hold_ace_return_court_speed(self):
        report = _full_report(market_type="match_tiebreak_yes_no", surface_context=_surface_context(court_speed_index=0.78))
        self.assertIn("match_tiebreak_yes_no", report["market_relevance"]["tiebreak_relevance"])

    def test_081_ace_prop_relevance_links_ace_rate_serve_surface_return(self):
        report = _full_report(market_type="aces")
        self.assertIn("aces", report["market_relevance"]["player_prop_relevance"])

    def test_082_double_fault_relevance_links_double_faults_pressure_conditions(self):
        report = _full_report(market_type="double_faults", serve_context=_serve_context(player_a_double_fault_rate=0.07))
        self.assertIn("double_faults", report["market_relevance"]["player_prop_relevance"])

    def test_083_break_point_props_link_return_quality_serve_volatility(self):
        report = _full_report(market_type="break_points_created")
        self.assertIn("break_points_created", report["market_relevance"]["player_prop_relevance"])

    def test_084_games_sets_won_relevance_links_match_distribution(self):
        report = _full_report(market_type="sets_won")
        self.assertIn("sets_won", report["market_relevance"]["player_prop_relevance"])

    def test_085_no_labeled_outcomes_returns_insufficient_data(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 0})
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_086_low_sample_returns_insufficient_sample(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 12})
        self.assertTrue(result["insufficient_sample"])

    def test_087_real_labeled_outcomes_enable_partial_calibration(self):
        outcomes = [{"id": f"p{i}", "hit": i % 2 == 0} for i in range(40)]
        result = evaluate_tennis_impact_calibration({"settled_outcomes": outcomes}, market_type="moneyline")
        self.assertEqual(result["calibration_status"], "partial_calibration")

    def test_088_roi_not_emitted_without_real_returns(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 40})
        self.assertNotIn("roi_proxy", result)

    def test_089_clv_not_emitted_without_real_open_close_prices(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 40})
        self.assertNotIn("clv_proxy", result)

    def test_090_slippage_not_emitted_without_real_fill_entry_data(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 40})
        self.assertNotIn("slippage_proxy", result)

    def test_091_correct_score_calibration_is_extra_conservative(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 40}, market_type="correct_score")
        self.assertTrue(result["correct_score_extra_conservative"])
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_092_tiebreak_calibration_is_extra_conservative(self):
        result = evaluate_tennis_impact_calibration({"matched_outcomes_count": 40}, market_type="match_tiebreak_yes_no")
        self.assertTrue(result["tiebreak_extra_conservative"])
        self.assertEqual(result["calibration_status"], "insufficient_data")

    def test_093_context_buckets_are_preserved(self):
        result = evaluate_tennis_impact_calibration(
            {
                "matched_outcomes_count": 40,
                "serve_strength_bucket": "strong",
                "return_strength_bucket": "average",
                "tiebreak_bucket": "high",
                "fatigue_bucket": "low",
            },
            sport="atp",
            market_type="moneyline",
            surface="hard",
            data_tier=2,
        )
        buckets = result["calibration_buckets"]
        self.assertEqual(buckets["sport"], "atp")
        self.assertEqual(buckets["surface"], "hard")
        self.assertEqual(buckets["serve_strength_bucket"], "strong")

    def test_094_fake_serve_placement_claim_is_downgraded(self):
        result = _red_team_with_claims(["serve_placement"])
        self.assertIn("serve_placement_missing_but_claimed", result["red_team_reasons"])

    def test_095_fake_serve_speed_claim_is_downgraded(self):
        result = _red_team_with_claims(["serve_speed"])
        self.assertIn("serve_speed_missing_but_claimed", result["red_team_reasons"])

    def test_096_fake_return_position_claim_is_downgraded(self):
        result = _red_team_with_claims(["return_position"])
        self.assertIn("return_position_missing_but_claimed", result["red_team_reasons"])

    def test_097_fake_shot_pattern_claim_is_downgraded(self):
        result = _red_team_with_claims(["shot_pattern"])
        self.assertIn("shot_pattern_missing_but_claimed", result["red_team_reasons"])

    def test_098_fake_court_speed_claim_is_downgraded(self):
        result = _red_team_with_claims(["court_speed"])
        self.assertIn("court_speed_missing_but_claimed", result["red_team_reasons"])

    def test_099_fake_ball_type_claim_is_downgraded(self):
        result = _red_team_with_claims(["ball_type"])
        self.assertIn("ball_type_missing_but_claimed", result["red_team_reasons"])

    def test_100_fake_injury_claim_is_downgraded(self):
        result = _red_team_with_claims(["injury"])
        self.assertIn("injury_status_missing_but_claimed", result["red_team_reasons"])

    def test_101_fake_retirement_risk_claim_is_downgraded(self):
        result = _red_team_with_claims(["retirement_risk"])
        self.assertIn("retirement_risk_missing_but_claimed", result["red_team_reasons"])

    def test_102_fake_weather_claim_is_downgraded(self):
        result = _red_team_with_claims(["weather"])
        self.assertIn("weather_conditions_missing_but_claimed", result["red_team_reasons"])

    def test_103_surface_split_small_sample_overfit_is_downgraded(self):
        result = _red_team_with_claims([], surface_context=evaluate_tennis_surface_context(_surface_context(sample_size_surface=8)))
        self.assertIn("surface_split_small_sample_overfit", result["red_team_reasons"])

    def test_104_head_to_head_overfit_is_downgraded(self):
        matchup = evaluate_tennis_matchup_context(_matchup_context(previous_head_to_head_context={"matches": 2, "win_rate": 1.0}))
        result = _red_team_with_claims([], matchup_context=matchup, source_payload={"overconfidence_flag": True})
        self.assertIn("head_to_head_overfit", result["red_team_reasons"])

    def test_105_recent_form_overfit_is_downgraded(self):
        result = _red_team_with_claims([], source_payload={"recent_form_weight": 0.6})
        self.assertIn("recent_form_overfit", result["red_team_reasons"])

    def test_106_tiebreak_record_overfit_is_downgraded(self):
        pressure = evaluate_tennis_pressure_tiebreak_context(_pressure_context(tiebreak_win_rate=0.62, recent_tiebreak_sample=5, long_term_tiebreak_sample=5))
        result = _red_team_with_claims([], pressure_tiebreak_context=pressure, source_payload={"overconfidence_flag": True})
        self.assertIn("tiebreak_record_overfit", result["red_team_reasons"])

    def test_107_break_point_conversion_overfit_is_downgraded(self):
        pressure = evaluate_tennis_pressure_tiebreak_context(_pressure_context(break_points_converted=0.50))
        result = _red_team_with_claims([], pressure_tiebreak_context=pressure, source_payload={"overconfidence_flag": True})
        self.assertIn("break_point_conversion_overfit", result["red_team_reasons"])

    def test_108_clutch_narrative_overfit_is_downgraded(self):
        incentive = evaluate_tennis_incentive_context({"home_country_context": "home_event"})
        result = _red_team_with_claims([], incentive_context=incentive)
        self.assertIn("clutch_narrative_overfit", result["red_team_reasons"])

    def test_109_correct_score_overconfidence_is_downgraded(self):
        result = _red_team_with_claims([], market="correct_score", calibration=evaluate_tennis_impact_calibration({"matched_outcomes_count": 0}, market_type="correct_score"))
        self.assertIn("correct_score_overconfidence", result["red_team_reasons"])

    def test_110_retirement_risk_ignored_is_downgraded(self):
        availability = evaluate_tennis_availability_context(_availability_context(withdrawal_risk=0.70))
        result = _red_team_with_claims([], availability_context=availability, source_payload={"ignores_retirement_risk": True})
        self.assertIn("retirement_risk_ignored", result["red_team_reasons"])

    def test_111_best_of_format_confusion_is_downgraded(self):
        fmt = evaluate_tennis_format_markov_context(_format_context(best_of=None))
        result = _red_team_with_claims([], market="correct_score", format_markov_context=fmt)
        self.assertIn("best_of_format_confusion", result["red_team_reasons"])

    def test_112_calibration_missing_prevents_overconfident_active_review(self):
        report = _full_report(market_type="moneyline", calibration_context={"matched_outcomes_count": 0})
        self.assertNotEqual(report["recommended_review_status"], "ACTIVE_REVIEW")
        self.assertEqual(report["calibration_status"], "insufficient_data")

    def test_113_readiness_endpoint_returns_provider_write_false(self):
        response = self.client.get("/api/automation/tennis-impact-readiness")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["provider_write"])

    def test_114_diagnostics_endpoint_returns_execution_allowed_false(self):
        response = self.client.post(
            "/api/automation/tennis-impact-diagnostics",
            json={
                "sport": "tennis",
                "market_type": "total_games",
                "dry_run": True,
                "match_context": _match_context(),
                "player_a_context": _player_a_context(),
                "player_b_context": _player_b_context(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_allowed"])

    def test_115_dry_run_false_is_rejected_or_forced_safe(self):
        response = self.client.post("/api/automation/tennis-impact-diagnostics", json={"dry_run": False})
        self.assertEqual(response.status_code, 400)

    def test_116_no_order_payload_survives_compaction(self):
        compact = compact_tennis_impact_diagnostics_response({"status": "x", "order_payload": {"x": 1}, "provider_write": True})
        self.assertNotIn("order_payload", compact)
        self.assertFalse(compact["provider_write"])

    def test_117_no_bet_slip_survives_compaction(self):
        compact = compact_tennis_impact_diagnostics_response({"status": "x", "bet_slip": {"x": 1}, "execution_allowed": True})
        self.assertNotIn("bet_slip", compact)
        self.assertFalse(compact["execution_allowed"])

    def test_118_secrets_raw_payloads_are_redacted(self):
        redacted = redact_and_limit_payload({"api_key": "secret", "raw_payload": {"x": 1}, "safe": "ok"})
        self.assertEqual(redacted["api_key"], "[redacted]")
        self.assertEqual(redacted["raw_payload"], "[omitted]")
        self.assertEqual(redacted["safe"], "ok")

    def test_119_ai_red_team_output_cannot_promote_execution(self):
        result = _red_team_with_claims(["serve_placement"], source_payload={"recommended_action": "EXECUTE"})
        self.assertFalse(result["execution_allowed"])
        self.assertNotEqual(result["recommended_action_adjustment"], "EXECUTE")

    def test_120_health_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/health").status_code, 200)

    def test_121_security_readiness_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/security-readiness").status_code, 200)

    def test_122_strategy_readiness_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/strategy-readiness").status_code, 200)

    def test_123_advanced_red_team_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/advanced-red-team-report").status_code, 200)

    def test_124_extreme_randomness_endpoint_still_passes(self):
        self.assertEqual(self.client.get("/api/automation/extreme-randomness-report").status_code, 200)

    def test_125_basketball_impact_endpoints_still_pass(self):
        self.assertEqual(self.client.get("/api/automation/basketball-player-impact-readiness").status_code, 200)

    def test_126_football_impact_endpoints_still_pass(self):
        self.assertEqual(self.client.get("/api/automation/football-impact-readiness").status_code, 200)

    def test_127_baseball_impact_endpoints_still_pass(self):
        self.assertEqual(self.client.get("/api/automation/baseball-impact-readiness").status_code, 200)

    def test_128_hockey_impact_endpoints_still_pass(self):
        self.assertEqual(self.client.get("/api/automation/hockey-impact-readiness").status_code, 200)

    def test_129_soccer_impact_endpoints_still_pass(self):
        self.assertEqual(self.client.get("/api/automation/soccer-impact-readiness").status_code, 200)

    def test_130_golf_impact_endpoints_still_pass_if_present(self):
        response = self.client.get("/api/automation/golf-impact-readiness")
        self.assertIn(response.status_code, {200, 404})

    def test_131_tennis_malformed_payload_does_not_500(self):
        response = self.client.post("/api/automation/tennis-impact-diagnostics", json={"sport": 123, "market_type": [], "dry_run": True})
        self.assertNotEqual(response.status_code, 500)

    def test_132_limited_public_data_payload_returns_tier_without_fake_tracking(self):
        report = _full_report(
            market_type="moneyline",
            serve_context={},
            return_context={},
            surface_context={},
            format_context={},
            pressure_context={},
            tiebreak_context={},
            matchup_context={},
            availability_context={},
            incentive_context={},
        )
        self.assertEqual(report["data_tier"], 1)
        self.assertFalse(report["tracking_level_allowed"])
        self.assertFalse(report["serve_impact"]["serve_placement_fabricated"])
        self.assertFalse(report["surface_context"]["court_speed_fabricated"])

    def test_133_full_readiness_contains_supported_aliases_and_safety(self):
        readiness = build_tennis_impact_readiness()
        self.assertIn("tennis", readiness["supported_sports"])
        self.assertIn("atp", readiness["supported_sports"])
        self.assertIn("wta", readiness["supported_sports"])
        self.assertFalse(readiness["provider_write"])
        self.assertFalse(readiness["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
