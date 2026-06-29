import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.services.streamlit_dashboard_facade import diagnose_extreme_randomness
from src.services.streamlit_dashboard_facade import build_surrogate_baseline_summary, compare_to_random_baseline
from src.services.streamlit_dashboard_facade import evaluate_random_matrix_risk
from src.automation_scheduler_legacy.response_compactor import compact_extreme_randomness_diagnostics_response, compact_extreme_randomness_report_response
from src.services.streamlit_dashboard_facade import get_strategy_registry
from src.services.streamlit_dashboard_facade import classify_tail_event
from src.services.streamlit_dashboard_facade import evaluate_tracy_widom_research
from src.services.streamlit_dashboard_facade import build_universality_research_lane
from tests.support.action_imports import app


class TestExtremeRandomnessDiagnostics(unittest.TestCase):
    def test_extreme_randomness_defaults_to_research_and_red_team_only(self):
        result = diagnose_extreme_randomness({"asset_type": "stock", "estimated_edge": 10})
        self.assertTrue(result["red_team_only"])
        self.assertTrue(result["research_only"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])

    def test_missing_baseline_returns_blocked_insufficient_data(self):
        result = diagnose_extreme_randomness({"asset_type": "stock", "estimated_edge": 25})
        item = result["sample_item"]
        self.assertTrue(item["insufficient_sample"])
        self.assertEqual(item["edge_vs_random_baseline"], "blocked_insufficient_data")
        self.assertEqual(item["blocked_reason"], "baseline_sample_too_small")
        self.assertEqual(item["recommended_action_adjustment"], "request_more_data")

    def test_extreme_signal_without_calibration_increases_caution_not_confidence(self):
        result = diagnose_extreme_randomness(
            {
                "asset_type": "stock",
                "estimated_edge": 25,
                "historical_sample_size": 40,
                "calibration_status": "insufficient_data",
            },
            baseline_values=[0.0] * 39 + [5.0],
        )
        item = result["sample_item"]
        self.assertTrue(item["edge_survives_random_baseline"])
        self.assertEqual(item["recommended_action_adjustment"], "request_more_data")
        self.assertEqual(item["blocked_reason"], "calibration_not_supported")
        self.assertIn("caution", item["red_team_warning"])

    def test_random_baseline_comparison_downgrades_weak_signal(self):
        result = compare_to_random_baseline({"observed_signal": 1.0}, baseline_values=[float(i) for i in range(40)])
        self.assertEqual(result["baseline_support_status"], "ready")
        self.assertFalse(result["edge_survives_random_baseline"])
        self.assertLess(result["edge_quality_score_adjustment"], 0)
        self.assertIn("does_not_clear", result["random_baseline_warning"])

    def test_bootstrap_shuffled_baseline_output_shape(self):
        result = build_surrogate_baseline_summary({"observed_signal": 5.0, "baseline_method": "shuffled_time_windows"}, baseline_values=[0.1] * 40)
        self.assertEqual(result["baseline_method"], "shuffled_time_windows")
        self.assertEqual(result["baseline_sample_size"], 40)
        self.assertIn("shuffled_labels", result["surrogate_methods_available"])
        self.assertIn("bootstrap_baseline", result["surrogate_methods_available"])

    def test_rmt_insufficient_matrix_data_handled_cleanly(self):
        result = evaluate_random_matrix_risk({})
        self.assertEqual(result["rmt_status"], "insufficient_matrix_data")
        self.assertTrue(result["insufficient_matrix_data"])
        self.assertFalse(result["execution_allowed"])

    def test_rmt_largest_eigenvalue_shape_when_matrix_valid(self):
        result = evaluate_random_matrix_risk(
            {
                "correlation_matrix": [
                    [1.0, 0.85, 0.80],
                    [0.85, 1.0, 0.82],
                    [0.80, 0.82, 1.0],
                ],
                "sample_size": 120,
                "dimension_count": 3,
            }
        )
        self.assertEqual(result["rmt_status"], "ready")
        self.assertEqual(result["dimension_count"], 3)
        self.assertIsNotNone(result["largest_eigenvalue"])
        self.assertIsNotNone(result["bulk_edge_estimate"])
        self.assertIn("systemwide_noise_risk", result)

    def test_tracy_widom_not_applicable_without_valid_matrix_setup(self):
        result = evaluate_tracy_widom_research({})
        self.assertEqual(result["tracy_widom_status"], "not_applicable")
        self.assertFalse(result["tw_applicable"])
        self.assertFalse(result["execution_allowed"])

    def test_tracy_widom_missing_dependency_returns_blocked(self):
        with patch('src.automation_scheduler_legacy.tracy_widom_research._has_optional_tw_dependency', return_value=False):
            result = evaluate_tracy_widom_research({"largest_eigenvalue": 2.4, "bulk_edge_estimate": 1.3, "sample_size": 100, "dimension_count": 5})
        self.assertEqual(result["tracy_widom_status"], "blocked_missing_dependency")
        self.assertTrue(result["tw_applicable"])
        self.assertIsNone(result["tw_tail_probability"])

    def test_tail_classifier_prediction_market_fake_edge(self):
        result = classify_tail_event({"asset_type": "prediction_market", "estimated_edge": 15, "liquidity_score": 10, "spread_score": 10})
        self.assertEqual(result["tail_event_type"], "fake_edge_tail_event")
        self.assertTrue(result["no_bet_reasons"])

    def test_tail_classifier_sportsbook_line_shock(self):
        result = classify_tail_event({"asset_type": "sportsbook", "line_move": 80, "injury_news_score": 90})
        self.assertIn(result["tail_event_type"], {"random_extreme", "market_structure_break"})
        self.assertTrue(result["no_bet_reasons"])

    def test_tail_classifier_stock_etf_volatility_shock(self):
        stock = classify_tail_event({"asset_type": "stock", "volatility_score": 90, "relative_volume": 9})
        etf = classify_tail_event({"asset_type": "etf", "volatility_score": 85, "price_move": 15})
        self.assertEqual(stock["tail_event_type"], "volatility_tail_event")
        self.assertEqual(etf["tail_event_type"], "volatility_tail_event")
        self.assertTrue(stock["no_trade_reasons"])

    def test_tail_classifier_crypto_liquidation_event(self):
        result = classify_tail_event({"asset_type": "crypto", "liquidation_cluster_risk": 90, "funding_rate": 0.05})
        self.assertEqual(result["tail_event_type"], "liquidity_tail_event")
        self.assertTrue(result["no_trade_reasons"])

    def test_tail_classifier_bond_rate_macro_shock(self):
        result = classify_tail_event({"asset_type": "bond_rate", "macro_event_score": 90, "yield_change": 0.55})
        self.assertEqual(result["tail_event_type"], "possible_regime_change")
        self.assertTrue(result["no_trade_reasons"])

    def test_universality_research_lane_remains_research_only(self):
        result = build_universality_research_lane(
            [
                {"asset_type": "stock", "tail_event_type": "fake_edge_tail_event"},
                {"asset_type": "crypto", "tail_event_type": "fake_edge_tail_event"},
            ]
        )
        self.assertTrue(result["research_only"])
        self.assertTrue(result["cross_asset_pattern_detected"])
        self.assertFalse(result["affects_execution"])
        self.assertFalse(result["execution_allowed"])

    def test_red_team_layer_can_only_downgrade_or_request_more_data(self):
        result = diagnose_extreme_randomness({"asset_type": "stock", "estimated_edge": 1}, baseline_values=[float(i) for i in range(40)])
        self.assertIn(result["sample_item"]["recommended_action_adjustment"], {"none", "downgrade_review", "no_bet", "no_trade", "request_more_data"})
        self.assertNotIn(result["sample_item"]["recommended_action_adjustment"], {"approve", "buy", "sell", "execute"})

    def test_red_team_layer_cannot_enable_execution_or_provider_writes(self):
        result = diagnose_extreme_randomness(
            {"asset_type": "stock", "estimated_edge": 25, "execution_allowed": True, "provider_write": True},
            baseline_values=[0.0] * 40,
        )
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])
        self.assertFalse(result["sample_item"].get("affects_execution", False))

    def test_no_secrets_or_raw_payloads_exposed(self):
        result = diagnose_extreme_randomness(
            {
                "asset_type": "prediction_market",
                "estimated_edge": 15,
                "liquidity_score": 5,
                "spread_score": 5,
                "api_key": "secret-value",
                "raw_payload": {"must": "drop"},
            },
            baseline_values=[0.0] * 40,
        )
        compact = compact_extreme_randomness_diagnostics_response(result)
        rendered = str(compact)
        self.assertNotIn("secret-value", rendered)
        self.assertNotIn("'raw_payload':", rendered)
        self.assertNotIn("drop", rendered)
        self.assertFalse(compact["raw_payload_included"])
        self.assertFalse(compact["secrets_included"])

    def test_response_compactor_handles_new_fields(self):
        result = diagnose_extreme_randomness({"asset_type": "crypto", "liquidation_cluster_risk": 80, "estimated_edge": 20}, baseline_values=[0.0] * 40)
        compact = compact_extreme_randomness_diagnostics_response(result)
        self.assertEqual(compact["status"], "extreme_randomness_diagnostics_complete")
        self.assertIn("sample_item", compact)
        self.assertIn("random_baseline", compact)
        self.assertIn("tail_event", compact)
        self.assertFalse(compact["provider_write"])

    def test_report_compactor_handles_new_fields(self):
        compact = compact_extreme_randomness_report_response(
            {
                "ok": True,
                "status": "extreme_randomness_report",
                "advanced_math_status": {"tracy_widom": "blocked_missing_dependency"},
                "universality": {"universality_status": "research_only", "research_only": True},
            }
        )
        self.assertEqual(compact["status"], "extreme_randomness_report")
        self.assertTrue(compact["research_only"])
        self.assertFalse(compact["execution_allowed"])

    def test_strategy_registry_entry(self):
        registry = get_strategy_registry()
        strategy = registry["extreme_randomness_red_team"]
        self.assertEqual(strategy["strategy_family"], "tail_risk_random_baseline")
        self.assertEqual(strategy["maturity_status"], "research_only")
        self.assertEqual(strategy["review_queue_effect"], "downgrade_only")
        self.assertEqual(strategy["ranking_effect"], "penalty_only")
        self.assertFalse(strategy["affects_execution"])
        self.assertFalse(strategy["provider_write"])

    def test_extreme_randomness_report_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = TestClient(app).get("/api/automation/extreme-randomness-report")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["red_team_only"])
        self.assertTrue(payload["research_only"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])

    def test_extreme_signal_diagnostics_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = TestClient(app).post(
                    "/api/automation/extreme-signal-diagnostics",
                    json={
                        "dry_run": True,
                        "candidate": {"asset_type": "prediction_market", "estimated_edge": 15, "liquidity_score": 10, "spread_score": 10},
                        "baseline_values": [0.0] * 40,
                    },
                )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "extreme_randomness_diagnostics_complete")
        self.assertEqual(payload["sample_item"]["tail_event_type"], "fake_edge_tail_event")
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["provider_write"])

    def test_extreme_signal_diagnostics_rejects_non_dry_run(self):
        response = TestClient(app).post("/api/automation/extreme-signal-diagnostics", json={"dry_run": False, "candidate": {}})
        self.assertEqual(response.status_code, 400)

    def test_existing_security_flags_present(self):
        result = diagnose_extreme_randomness({"asset_type": "stock", "estimated_edge": 1}, baseline_values=[0.0] * 40)
        self.assertTrue(result["human_approval_required"])
        self.assertTrue(result["owner_approval_required"])
        self.assertFalse(result["auto_execution"])
        self.assertEqual(result["actual_orders_submitted"], 0)
        self.assertEqual(result["actual_bets_submitted"], 0)
        self.assertEqual(result["actual_trades_submitted"], 0)


if __name__ == "__main__":
    unittest.main()
