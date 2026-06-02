import json
import tempfile
import unittest

from automation_scheduler.execution_gatekeeper import evaluate_future_execution_eligibility
from automation_scheduler.hard_gate_policy import evaluate_hard_gates
from automation_scheduler.strategy_disagreement import load_strategy_disagreements
from automation_scheduler.strategy_maturity import evaluate_strategy_maturity
from automation_scheduler.strategy_promotion import evaluate_strategy_promotion
from automation_scheduler.strategy_registry import get_strategy_registry
from automation_scheduler.strategy_router import route_strategies
from automation_scheduler.strategy_score_aggregator import aggregate_strategy_scores


def _stock_candidate(**extra):
    row = {
        "candidate_id": "stock-1",
        "asset_type": "stock",
        "market_type": "equity",
        "provider": "internal_deterministic",
        "price": 4.25,
        "volume": 1_200_000,
        "float_shares": 8_000_000,
        "relative_volume": 4.1,
        "liquidity_tier": "adequate",
        "data_resolution": "1m",
        "market_valid": True,
        "data_integrity_passed": True,
    }
    row.update(extra)
    return row


def _kalshi_candidate(**extra):
    row = {
        "candidate_id": "kalshi-1",
        "asset_type": "prediction_market",
        "market_type": "prediction_market",
        "provider": "internal_deterministic",
        "yes_bid": 42,
        "yes_ask": 45,
        "market_valid": True,
        "data_integrity_passed": True,
    }
    row.update(extra)
    return row


def _sports_candidate(**extra):
    row = {
        "candidate_id": "prop-1",
        "asset_type": "sportsbook",
        "market_type": "sports_player_props",
        "provider": "internal_deterministic",
        "sport": "basketball",
        "league": "nba",
        "market_valid": True,
        "data_integrity_passed": True,
    }
    row.update(extra)
    return row


def _crypto_candidate(**extra):
    row = {
        "candidate_id": "crypto-1",
        "asset_type": "crypto",
        "market_type": "crypto_spot",
        "provider": "internal_deterministic",
        "price": 100.0,
        "volume": 2_000_000,
        "liquidity_tier": "adequate",
        "data_resolution": "1m",
        "market_valid": True,
        "data_integrity_passed": True,
    }
    row.update(extra)
    return row


class TestHardGatePolicy(unittest.TestCase):
    def test_missing_owner_approval_blocks_execution(self):
        result = evaluate_hard_gates(_stock_candidate(), idempotency_key="k1", execution_mode="sandbox_owner_approved")
        self.assertIn("owner_approval_valid", result["failed_hard_gates"])
        self.assertFalse(result["execution_allowed"])

    def test_kill_switch_blocks_execution(self):
        result = evaluate_hard_gates(_stock_candidate(), idempotency_key="k1", execution_mode="sandbox_owner_approved")
        self.assertIn("kill_switch_inactive", result["failed_hard_gates"])

    def test_provider_write_false_blocks_execution(self):
        result = evaluate_hard_gates(_stock_candidate(), idempotency_key="k1", execution_mode="sandbox_owner_approved")
        self.assertIn("provider_write_allowed", result["failed_hard_gates"])

    def test_execution_flag_false_blocks_execution(self):
        result = evaluate_hard_gates(_stock_candidate(), idempotency_key="k1", execution_mode="sandbox_owner_approved")
        self.assertIn("global_execution_enabled", result["failed_hard_gates"])
        self.assertIn("provider_execution_enabled", result["failed_hard_gates"])

    def test_risk_limit_failure_blocks_execution(self):
        result = evaluate_hard_gates(_stock_candidate(), idempotency_key="k1", execution_mode="sandbox_owner_approved")
        self.assertIn("risk_limits_passed", result["failed_hard_gates"])

    def test_missing_audit_ledger_blocks_execution(self):
        result = evaluate_hard_gates(
            _stock_candidate(),
            idempotency_key="k1",
            execution_mode="sandbox_owner_approved",
            gate_overrides={"audit_ledger_write_ok": False},
        )
        self.assertIn("audit_ledger_write_ok", result["failed_hard_gates"])

    def test_replay_nonce_blocks_execution(self):
        result = evaluate_hard_gates(
            _stock_candidate(replay_detected=True),
            idempotency_key="k1",
            execution_mode="sandbox_owner_approved",
            gate_overrides={
                "global_execution_enabled": True,
                "provider_execution_enabled": True,
                "provider_write_allowed": True,
                "owner_approval_valid": True,
                "kill_switch_inactive": True,
                "risk_limits_passed": True,
                "audit_ledger_write_ok": True,
                "dry_run_promotion_allowed": True,
            },
        )
        self.assertIn("replay_protection_passed", result["failed_hard_gates"])


class TestStrategyRoutingAndRegistry(unittest.TestCase):
    def test_stock_candidate_routes_to_stock_strategies(self):
        routed = route_strategies(_stock_candidate())
        selected = set(routed["selected_strategy_ids"])
        self.assertIn("candlestick_liquidity", selected)
        self.assertIn("low_float_momentum", selected)
        self.assertIn("balance_sheet_risk", selected)
        self.assertIn("manifold_nearest_neighbor", selected)
        self.assertIn("monte_carlo_risk", selected)
        self.assertIn("deepseek_red_team", selected)

    def test_kalshi_candidate_routes_to_prediction_market_strategies(self):
        routed = route_strategies(_kalshi_candidate())
        selected = set(routed["selected_strategy_ids"])
        self.assertIn("prediction_market_liquidity", selected)
        self.assertIn("settlement_uncertainty", selected)
        self.assertIn("manifold_nearest_neighbor", selected)
        self.assertIn("deepseek_red_team", selected)

    def test_sports_prop_routes_to_game_script_strategies(self):
        routed = route_strategies(_sports_candidate(sport="football", league="nfl"))
        selected = set(routed["selected_strategy_ids"])
        self.assertIn("sportsbook_game_script", selected)
        self.assertIn("sports_prop_correlation", selected)
        self.assertIn("manifold_nearest_neighbor", selected)
        self.assertIn("deepseek_red_team", selected)

    def test_basketball_prop_routes_to_player_impact_if_available(self):
        routed = route_strategies(_sports_candidate())
        self.assertIn("basketball_player_impact", set(routed["selected_strategy_ids"]))

    def test_crypto_candidate_routes_to_crypto_strategies(self):
        routed = route_strategies(_crypto_candidate())
        selected = set(routed["selected_strategy_ids"])
        self.assertIn("candlestick_liquidity", selected)
        self.assertIn("manifold_nearest_neighbor", selected)
        self.assertIn("monte_carlo_risk", selected)
        self.assertIn("deepseek_red_team", selected)

    def test_unsupported_strategy_is_skipped_not_crashed(self):
        routed = route_strategies({"candidate_id": "bond-1", "asset_type": "bond_rate", "market_type": "rates", "provider": "internal_deterministic"})
        self.assertTrue(routed["ok"])
        self.assertIn("candlestick_liquidity", set(routed["skipped_strategy_ids"]))

    def test_strategy_defaults_are_safe(self):
        registry = get_strategy_registry()
        for row in registry.values():
            self.assertFalse(row["provider_write"])
            self.assertFalse(row["execution_allowed"])
            self.assertFalse(row["live_execution_enabled"])
            self.assertFalse(row["affects_execution"])

    def test_research_only_strategy_cannot_affect_final_action(self):
        row = get_strategy_registry()["information_theory"]
        maturity = evaluate_strategy_maturity(row, candidate=_stock_candidate())
        self.assertTrue(maturity["research_only_cannot_control_final_action"])
        self.assertFalse(maturity["can_affect_ranking"])

    def test_calibration_only_strategy_cannot_execute(self):
        row = get_strategy_registry()["sports_prop_correlation"]
        maturity = evaluate_strategy_maturity(row, candidate=_sports_candidate())
        self.assertTrue(maturity["calibration_only_cannot_execute"])
        self.assertFalse(maturity["can_affect_execution"])

    def test_missing_optional_strategy_output_does_not_block_review(self):
        result = aggregate_strategy_scores(
            _stock_candidate(),
            routed={"selected_strategies": [{"strategy_id": "rule_scoring", "strategy_family": "deterministic_rule_scoring", "maturity_status": "active_review", "can_affect_review": True}]},
            strategy_outputs={"rule_scoring": {"score": 78, "confidence_score": 70}},
        )
        self.assertIn(result["recommended_review_status"], {"WATCHLIST_REVIEW", "ACTIVE_REVIEW"})

    def test_missing_required_inputs_block_only_that_strategy(self):
        routed = route_strategies(_stock_candidate(price=None))
        self.assertIn("low_float_momentum", set(routed["blocked_strategy_ids"]))
        self.assertIn("manifold_nearest_neighbor", set(routed["selected_strategy_ids"]))


class TestStrategyAggregation(unittest.TestCase):
    def test_one_strong_calibrated_strategy_can_increase_review_priority(self):
        result = aggregate_strategy_scores(
            _kalshi_candidate(),
            routed={"selected_strategies": [{"strategy_id": "prediction_market_liquidity", "strategy_family": "prediction_market_liquidity", "maturity_status": "active_ranking", "can_affect_review": True, "can_affect_ranking": True}]},
            strategy_outputs={"prediction_market_liquidity": {"score": 88, "confidence_score": 78, "calibration_support_score": 72, "liquidity_risk_score": 20, "trap_risk_score": 18}},
        )
        self.assertEqual(result["recommended_review_status"], "ACTIVE_REVIEW")
        self.assertFalse(result["execution_allowed"])

    def test_conflicting_strategies_create_disagreement_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = aggregate_strategy_scores(
                _stock_candidate(),
                routed={
                    "selected_strategies": [
                        {"strategy_id": "candlestick_liquidity", "strategy_family": "candlestick_liquidity", "maturity_status": "active_review", "can_affect_review": True},
                        {"strategy_id": "deepseek_red_team", "strategy_family": "deepseek_red_team", "maturity_status": "active_review", "can_affect_review": True},
                    ]
                },
                strategy_outputs={
                    "candlestick_liquidity": {"score": 86, "confidence_score": 74},
                    "deepseek_red_team": {"recommended_action": "NO_TRADE", "red_team_warning": True, "red_team_penalty": 60},
                },
                create_disagreements=True,
                base_data_dir=tmp,
            )
            queue = load_strategy_disagreements(base_data_dir=tmp)
        self.assertEqual(result["disagreement_records_created"], 1)
        self.assertEqual(queue["count"], 1)
        self.assertFalse(queue["items"][0]["provider_write"])

    def test_red_team_warning_downgrades_priority(self):
        result = aggregate_strategy_scores(
            _stock_candidate(),
            routed={
                "selected_strategies": [
                    {"strategy_id": "candlestick_liquidity", "strategy_family": "candlestick_liquidity", "maturity_status": "active_review", "can_affect_review": True},
                    {"strategy_id": "deepseek_red_team", "strategy_family": "deepseek_red_team", "maturity_status": "active_review", "can_affect_review": True},
                ]
            },
            strategy_outputs={
                "candlestick_liquidity": {"score": 86, "confidence_score": 74},
                "deepseek_red_team": {"recommended_action": "NO_TRADE", "red_team_warning": True, "red_team_penalty": 35},
            },
        )
        self.assertEqual(result["recommended_review_status"], "WATCHLIST_REVIEW")

    def test_fatal_safety_blocker_overrides_optimism(self):
        result = aggregate_strategy_scores(
            _kalshi_candidate(),
            routed={"selected_strategies": [{"strategy_id": "prediction_market_liquidity", "strategy_family": "prediction_market_liquidity", "maturity_status": "active_ranking", "can_affect_review": True, "can_affect_ranking": True}]},
            strategy_outputs={"prediction_market_liquidity": {"score": 95, "confidence_score": 90, "provider_write": True}},
        )
        self.assertEqual(result["recommended_review_status"], "NO_BET")
        self.assertEqual(result["safety_penalty"], 100.0)
        self.assertFalse(result["provider_write"])

    def test_no_universal_strategy_agreement_required_for_review(self):
        result = aggregate_strategy_scores(
            _stock_candidate(),
            routed={
                "selected_strategies": [{"strategy_id": "candlestick_liquidity", "strategy_family": "candlestick_liquidity", "maturity_status": "active_review", "can_affect_review": True}],
                "blocked_strategies": [{"strategy_id": "markov_chain"}],
            },
            strategy_outputs={"candlestick_liquidity": {"score": 80, "confidence_score": 70}},
        )
        self.assertIn(result["recommended_review_status"], {"WATCHLIST_REVIEW", "ACTIVE_REVIEW"})
        self.assertFalse(result["universal_strategy_agreement_required"])


class TestPromotionAndFutureExecution(unittest.TestCase):
    def test_insufficient_sample_blocks_promotion(self):
        strategy = get_strategy_registry()["candlestick_liquidity"]
        result = evaluate_strategy_promotion(strategy, {"sample_size": 5, "minimum_sample_size": 30}, context_candidate=_stock_candidate())
        self.assertEqual(result["promotion_status"], "not_ready")

    def test_strong_outcome_evidence_promotes_to_active_review(self):
        strategy = get_strategy_registry()["candlestick_liquidity"]
        result = evaluate_strategy_promotion(
            strategy,
            {"sample_size": 60, "minimum_sample_size": 30, "outcome_coverage": 0.5, "calibration_error": 0.08, "false_positive_rate": 0.2, "expected_value": 0.04, "average_closing_line_value": 0.01},
            context_candidate=_stock_candidate(),
        )
        self.assertEqual(result["promotion_status"], "promote_to_active_review")

    def test_bad_false_positive_rate_demotes_strategy(self):
        strategy = get_strategy_registry()["candlestick_liquidity"]
        result = evaluate_strategy_promotion(
            strategy,
            {"sample_size": 80, "minimum_sample_size": 30, "outcome_coverage": 0.6, "calibration_error": 0.08, "false_positive_rate": 0.5, "expected_value": 0.02},
            context_candidate=_stock_candidate(),
        )
        self.assertEqual(result["promotion_status"], "demote_to_calibration_only")

    def test_strategy_can_be_promoted_for_one_context_and_blocked_in_another(self):
        strategy = get_strategy_registry()["candlestick_liquidity"]
        promoted = evaluate_strategy_promotion(
            strategy,
            {"sample_size": 60, "minimum_sample_size": 30, "outcome_coverage": 0.5, "calibration_error": 0.08, "false_positive_rate": 0.2, "expected_value": 0.04, "average_closing_line_value": 0.01},
            context_candidate=_stock_candidate(session="morning"),
        )
        blocked = evaluate_strategy_promotion(strategy, {"sample_size": 4, "minimum_sample_size": 30}, context_candidate=_stock_candidate(asset_type="etf", market_type="equity"))
        self.assertEqual(promoted["promotion_status"], "promote_to_active_review")
        self.assertEqual(blocked["promotion_status"], "not_ready")
        self.assertNotEqual(promoted["context_bucket"]["context_key"], blocked["context_bucket"]["context_key"])

    def test_future_execution_eligibility_remains_false_by_default(self):
        strategy = get_strategy_registry()["prediction_market_liquidity"]
        result = evaluate_strategy_promotion(
            strategy,
            {"sample_size": 300, "minimum_sample_size": 30, "outcome_coverage": 0.9, "calibration_error": 0.04, "false_positive_rate": 0.1, "expected_value": 0.03, "average_closing_line_value": 0.01, "drawdown": 0.1, "stability_across_time": 0.8, "stability_across_providers": 0.8},
            context_candidate=_kalshi_candidate(),
        )
        self.assertEqual(result["promotion_status"], "promote_to_active_ranking")
        self.assertFalse(result["future_execution_eligible"])

    def test_future_execution_eligible_does_not_imply_current_execution_allowed(self):
        result = evaluate_future_execution_eligibility(
            _kalshi_candidate(),
            aggregate={"weighted_score": 95, "calibration_support_score": 95, "liquidity_risk_score": 10, "trap_risk_score": 10},
            hard_gate_result={"failed_hard_gates": [], "hard_gate_status": "passed_future_only"},
        )
        self.assertTrue(result["future_execution_eligible"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["provider_write"])

    def test_current_execution_remains_blocked_unless_all_hard_gates_pass(self):
        result = evaluate_future_execution_eligibility(
            _kalshi_candidate(),
            aggregate={"weighted_score": 95, "calibration_support_score": 95, "liquidity_risk_score": 10, "trap_risk_score": 10},
        )
        self.assertIn("hard_security_gate_locked", result["future_execution_blockers"])
        self.assertFalse(result["execution_allowed"])

    def test_ai_cannot_set_future_execution_eligible(self):
        result = evaluate_future_execution_eligibility(_stock_candidate(future_execution_eligible=True), actor_type="ai_provider")
        self.assertIn("ai_cannot_set_future_execution_eligible", result["future_execution_blockers"])
        self.assertFalse(result["future_execution_eligible"])

    def test_ai_cannot_set_execution_allowed(self):
        result = evaluate_future_execution_eligibility(_stock_candidate(execution_allowed=True), actor_type="ai_provider")
        self.assertIn("ai_cannot_set_execution_allowed", result["future_execution_blockers"])
        self.assertFalse(result["execution_allowed"])


class TestStrategySecurity(unittest.TestCase):
    def test_no_secrets_or_raw_payloads_exposed(self):
        result = aggregate_strategy_scores(
            _stock_candidate(api_key="sk-should-not-appear-1234567890", raw_payload={"drop": True}, provider_payload={"drop": True}),
            routed={"selected_strategies": [{"strategy_id": "rule_scoring", "strategy_family": "deterministic_rule_scoring", "maturity_status": "active_review", "can_affect_review": True}]},
            strategy_outputs={"rule_scoring": {"score": 78}},
        )
        text = json.dumps(result)
        self.assertNotIn("sk-should-not-appear", text)
        self.assertNotIn('"raw_payload":', text)
        self.assertNotIn('"provider_payload":', text)
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])

    def test_no_order_payloads_or_bet_slips_generated(self):
        result = aggregate_strategy_scores(
            _kalshi_candidate(),
            routed={"selected_strategies": [{"strategy_id": "prediction_market_liquidity", "strategy_family": "prediction_market_liquidity", "maturity_status": "active_ranking", "can_affect_review": True}]},
            strategy_outputs={"prediction_market_liquidity": {"score": 90, "order_payload": {"side": "buy"}, "bet_slip": {"stake": 50}}},
        )
        text = json.dumps(result).lower()
        self.assertNotIn("order_payload", text)
        self.assertNotIn("bet_slip", text)
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
