import tempfile
import unittest

from fastapi.testclient import TestClient

from automation_scheduler.candlestick_manifold_detector import map_candlestick_context
from automation_scheduler.cross_asset_manifold_router import run_cross_asset_manifold_review
from automation_scheduler.manifold_calibration import build_manifold_calibration_bucket, compute_historical_cluster_stats
from automation_scheduler.manifold_cluster_registry import load_cluster_registry, write_cluster_registry
from automation_scheduler.manifold_feature_builder import FEATURE_VECTOR_VERSION, build_manifold_feature_vector
from automation_scheduler.market_state_manifold import map_market_state, nearest_historical_neighbors
from automation_scheduler.response_compactor import compact_manifold_map_response
from automation_scheduler.sportsbook_manifold_mapper import map_sportsbook_full_board
from src.services.execution_service import detect_manifold_trap, simulate_execution
from tests.support.action_imports import app


class TestMarketStateManifold(unittest.TestCase):
    def _tmp(self):
        return tempfile.TemporaryDirectory()

    def _crypto_breakout(self):
        return {
            "asset_type": "crypto",
            "market_type": "spot",
            "symbol": "BTC",
            "liquidity_score": 88,
            "spread_score": 92,
            "volume_24h": 900_000_000,
            "orderbook_depth_1pct": 80_000_000,
            "trend_score": 80,
            "price_momentum_score": 78,
            "confidence_score": 70,
        }

    def test_cross_asset_feature_vector_creation(self):
        payload = build_manifold_feature_vector(self._crypto_breakout())
        self.assertEqual(payload["feature_vector_version"], FEATURE_VECTOR_VERSION)
        self.assertEqual(payload["asset_type"], "crypto")
        self.assertEqual(payload["normalized_features"]["asset_type_crypto"], 1.0)
        self.assertEqual(len(payload["feature_vector"]), len(payload["weighted_feature_vector"]))

    def test_feature_normalization(self):
        payload = build_manifold_feature_vector({"asset_type": "stock", "model_probability": 58, "confidence_score": 82, "estimated_edge": 6})
        features = payload["normalized_features"]
        self.assertEqual(features["model_probability"], 0.58)
        self.assertEqual(features["confidence_score"], 0.82)
        self.assertAlmostEqual(features["estimated_edge"], 0.65)

    def test_missing_feature_handling(self):
        with self._tmp() as tmp:
            result = map_market_state({}, base_data_dir=tmp)
        self.assertTrue(result["missing_features"])
        self.assertIn(result["recommended_action"], {"DATA_INSUFFICIENT", "LOW_PRIORITY_REVIEW", "NO_REVIEW"})
        self.assertFalse(result["execution_allowed"])

    def test_prediction_market_mapping(self):
        with self._tmp() as tmp:
            result = map_market_state(
                {
                    "asset_type": "prediction_market",
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "yes_price": 0.52,
                    "implied_probability": 0.52,
                    "estimated_edge": 0.18,
                    "liquidity_score": 20,
                    "spread_score": 20,
                    "pricing_quality_score": 30,
                    "confidence_score": 80,
                    "stale_market_score": 80,
                },
                base_data_dir=tmp,
            )
        self.assertEqual(result["asset_type"], "prediction_market")
        self.assertIn(result["manifold_cluster_name"], {"low_liquidity_stale_pricing_zone", "wide_spread_fake_edge_zone", "high_confidence_poor_liquidity_zone"})
        self.assertTrue(result["insufficient_sample"])

    def test_sportsbook_full_board_game_script_mapping(self):
        with self._tmp() as tmp:
            result = map_sportsbook_full_board(
                [
                    {"sport": "nba", "league": "NBA", "market_type": "total", "game_script_score": 90, "line_movement_score": 84, "liquidity_score": 75},
                    {"sport": "nba", "league": "NBA", "market_type": "prop", "prop_context_score": 85, "live_latency_score": 82, "stale_data_risk": 80},
                ],
                base_data_dir=tmp,
            )
        self.assertEqual(result["items_mapped"], 2)
        self.assertIn("game_script_cluster_counts", result)
        self.assertFalse(result["execution_allowed"])

    def test_stock_candlestick_liquidity_mapping(self):
        with self._tmp() as tmp:
            result = map_candlestick_context(
                {
                    "asset_type": "stock",
                    "symbol": "TEST",
                    "market_type": "equity",
                    "candlestick_pattern_id": "bullish_engulfing",
                    "pattern_quality_score": 82,
                    "relative_volume": 6,
                    "liquidity_score": 82,
                    "spread_score": 88,
                    "vwap_context_score": 86,
                    "trend_score": 78,
                },
                base_data_dir=tmp,
            )
        self.assertEqual(result["pattern_id"], "bullish_engulfing")
        self.assertIn("pattern_context_reliability_score", result)
        self.assertFalse(result["execution_allowed"])

    def test_crypto_liquidity_breakout_mapping(self):
        with self._tmp() as tmp:
            result = map_market_state(self._crypto_breakout(), base_data_dir=tmp)
        self.assertEqual(result["asset_type"], "crypto")
        self.assertEqual(result["manifold_cluster_name"], "liquid_breakout_continuation")
        self.assertEqual(result["recommended_unit_size"], 0)

    def test_bond_rate_macro_event_mapping(self):
        with self._tmp() as tmp:
            result = map_market_state(
                {"asset_type": "bond_rate", "market_type": "rates", "yield_change": 1.3, "macro_event_score": 90, "rate_volatility_score": 85, "liquidity_score": 70, "spread_score": 75},
                base_data_dir=tmp,
            )
        self.assertEqual(result["manifold_family"], "bond_rate_macro")
        self.assertIn(result["asset_type"], {"bond_rate", "etf", "major_asset"})

    def test_nearest_neighbor_lookup(self):
        feature = build_manifold_feature_vector(self._crypto_breakout())
        neighbors = nearest_historical_neighbors(feature, [{"weighted_feature_vector": feature["weighted_feature_vector"], "final_outcome": "win"}])
        self.assertEqual(neighbors["nearest_historical_neighbors"], 1)
        self.assertEqual(neighbors["nearest_neighbor_distance"], 0.0)

    def test_nearest_neighbors_require_labeled_outcomes(self):
        feature = build_manifold_feature_vector(self._crypto_breakout())
        unlabeled = [{"weighted_feature_vector": feature["weighted_feature_vector"], "historical_roi": 0.99}]
        self.assertEqual(nearest_historical_neighbors(feature, unlabeled)["nearest_historical_neighbors"], 0)
        labeled = [{"weighted_feature_vector": feature["weighted_feature_vector"], "return_pct": 1.5}]
        self.assertEqual(nearest_historical_neighbors(feature, labeled)["nearest_historical_neighbors"], 1)

    def test_cluster_registry_read_write(self):
        with self._tmp() as tmp:
            registry = load_cluster_registry(base_data_dir=tmp, create_if_missing=False)
            storage = write_cluster_registry(registry, base_data_dir=tmp)
            loaded = load_cluster_registry(base_data_dir=tmp)
        self.assertGreater(storage["cluster_count"], 0)
        self.assertGreater(loaded["cluster_count"], 0)

    def test_cluster_reliability_scoring_uses_sample_stats(self):
        with self._tmp() as tmp:
            result = map_market_state(
                self._crypto_breakout(),
                calibration_report={
                    "clusters": {
                        "crypto_liquid_breakout_continuation_001": {
                            "sample_size": 40,
                            "outcome_coverage": 0.9,
                            "win_rate": 0.58,
                            "historical_roi": 0.035,
                            "profit_factor": 1.4,
                            "calibration_error": 0.05,
                            "insufficient_sample": False,
                        }
                    }
                },
                base_data_dir=tmp,
            )
        self.assertFalse(result["insufficient_sample"])
        self.assertEqual(result["historical_win_rate"], 0.58)
        self.assertGreater(result["cluster_reliability_score"], 50)
        self.assertEqual(result["nearest_historical_neighbors"], 0)
        self.assertEqual(result["calibration_sample_size"], 40)

    def test_prototype_cluster_cannot_report_metrics_ready(self):
        with self._tmp() as tmp:
            registry = load_cluster_registry(base_data_dir=tmp, create_if_missing=False)
            for cluster in registry["clusters"]:
                cluster["historical_stats"] = {
                    "sample_size": 100,
                    "outcome_coverage": 1.0,
                    "win_rate": 0.99,
                    "historical_roi": 0.50,
                    "profit_factor": 12.0,
                    "insufficient_sample": False,
                }
            result = map_market_state({"asset_type": "prediction_market", "liquidity_score": 80, "spread_score": 80}, registry=registry, base_data_dir=tmp)
        self.assertTrue(result["insufficient_sample"])
        self.assertEqual(result["calibration_status"], "insufficient_data")
        self.assertIsNone(result["historical_win_rate"])
        self.assertIsNone(result["historical_roi"])
        self.assertEqual(result["cluster_reliability_score"], 0.0)

    def test_historical_metrics_require_real_labeled_outcomes(self):
        records = [
            {"manifold_cluster_id": "cluster_a", "outcome_status": "settled", "historical_roi": 0.90}
            for _ in range(40)
        ]
        stats = compute_historical_cluster_stats(records)
        self.assertTrue(stats["cluster_a"]["insufficient_sample"])
        self.assertIsNone(stats["cluster_a"]["historical_roi"])

        labeled = [
            {"manifold_cluster_id": "cluster_a", "outcome_status": "settled", "final_outcome": "win", "return_pct": 2.0}
            for _ in range(40)
        ]
        labeled_stats = compute_historical_cluster_stats(labeled)
        self.assertFalse(labeled_stats["cluster_a"]["insufficient_sample"])
        self.assertEqual(labeled_stats["cluster_a"]["win_rate"], 1.0)
        self.assertIsNotNone(labeled_stats["cluster_a"]["historical_roi"])

    def test_out_of_distribution_detection(self):
        with self._tmp() as tmp:
            result = map_market_state({"asset_type": "stock", "outlier_score": 100, "liquidity_score": 0, "spread_score": 0, "risk_score": 100}, base_data_dir=tmp)
        self.assertIn(result["out_of_distribution_risk"], {"high", "extreme"})
        self.assertLessEqual(result["confidence_adjustment"], 0)

    def test_insufficient_neighbor_sample_behavior(self):
        with self._tmp() as tmp:
            result = map_market_state(self._crypto_breakout(), base_data_dir=tmp)
        self.assertEqual(result["nearest_historical_neighbors"], 0)
        self.assertTrue(result["insufficient_sample"])
        self.assertIsNone(result["historical_roi"])

    def test_no_bet_trap_detection(self):
        trap = detect_manifold_trap(
            asset_type="prediction_market",
            cluster_id="prediction_wide_spread_fake_edge_001",
            cluster_name="wide_spread_fake_edge_zone",
            normalized_features={"confidence_score": 0.85, "estimated_edge": 0.90, "liquidity_score": 0.20, "spread_score": 0.15},
            cluster_stats={"sample_size": 40, "insufficient_sample": False, "win_rate": 0.40, "historical_roi": -0.05, "false_positive_rate": 0.50, "historical_negative_ev_rate": 0.60},
        )
        self.assertTrue(trap["trap_cluster_detected"])
        self.assertEqual(trap["recommended_action"], "NO_BET")

    def test_no_trade_trap_detection(self):
        trap = detect_manifold_trap(
            asset_type="stock",
            cluster_id="stock_dilution_risk_momentum_trap_009",
            cluster_name="dilution_risk_momentum_trap",
            normalized_features={"confidence_score": 0.82, "estimated_edge": 0.75, "liquidity_score": 0.30, "spread_score": 0.20, "dilution_risk_score": 0.95, "breakout_failure_score": 0.80},
            cluster_stats={"sample_size": 40, "insufficient_sample": False, "win_rate": 0.42, "historical_roi": -0.04, "false_positive_rate": 0.48},
        )
        self.assertTrue(trap["trap_cluster_detected"])
        self.assertEqual(trap["recommended_action"], "NO_TRADE")

    def test_manifold_calibration_bucket_creation(self):
        bucket = build_manifold_calibration_bucket(
            {"asset_type": "crypto", "market_type": "spot", "provider_name": "exchange", "manifold_cluster_id": "crypto_liquid_breakout_continuation_001", "neighbor_sample_size": 42}
        )
        self.assertEqual(bucket["asset_type"], "crypto")
        self.assertEqual(bucket["manifold_cluster_id"], "crypto_liquid_breakout_continuation_001")
        self.assertEqual(bucket["neighbor_count_at_detection"], 42)

    def test_historical_cluster_stats_insufficient_sample_true(self):
        records = [{"manifold_cluster_id": "cluster_a", "outcome_status": "settled", "final_outcome": "win", "return_pct": 1.0} for _ in range(5)]
        stats = compute_historical_cluster_stats(records)
        self.assertTrue(stats["cluster_a"]["insufficient_sample"])
        self.assertIsNone(stats["cluster_a"]["win_rate"])

    def test_delayed_outcome_fields_preserved_in_calibration_bucket(self):
        bucket = build_manifold_calibration_bucket(
            {
                "asset_type": "sportsbook",
                "market_type": "prop",
                "manifold_cluster_id": "sportsbook_stale_prop_line_008",
                "requested_window_seconds": 300,
                "effective_window_seconds": 420,
                "delayed_by_seconds": 120,
                "final_outcome": "loss",
                "line_moved_with_prediction": False,
            }
        )
        self.assertEqual(bucket["requested_window_seconds"], 300)
        self.assertEqual(bucket["effective_window_seconds"], 420)
        self.assertEqual(bucket["delayed_by_seconds"], 120)
        self.assertEqual(bucket["final_outcome"], "loss")

    def test_markov_hmm_context_stub_is_present(self):
        with self._tmp() as tmp:
            result = map_market_state(self._crypto_breakout(), base_data_dir=tmp)
        self.assertEqual(result["markov_hmm_context"]["integration_status"], "not_configured")
        self.assertEqual(result["markov_hmm_context"]["manifold_cluster_id"], result["manifold_cluster_id"])

    def test_review_priority_adjustment(self):
        with self._tmp() as tmp:
            result = map_market_state(self._crypto_breakout(), base_data_dir=tmp)
        self.assertIsInstance(result["review_priority_adjustment"], float)
        self.assertLessEqual(result["review_priority_adjustment"], 18.0)

    def test_fatal_safety_blockers_override_optimism(self):
        item = self._crypto_breakout()
        item["blockers"] = ["fatal_execution_blocker"]
        with self._tmp() as tmp:
            result = map_market_state(item, base_data_dir=tmp)
        self.assertEqual(result["recommended_action"], "NO_TRADE")
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["provider_write"])

    def test_compact_response_safety(self):
        result = {"ok": True, "item": map_market_state({"asset_type": "prediction_market", "provider_payload": {"token": "supersecret"}, "api_key": "supersecret"}, base_data_dir=tempfile.mkdtemp())}
        compact = compact_manifold_map_response(result)
        text = str(compact)
        self.assertNotIn("provider_payload", text)
        self.assertNotIn("supersecret", text)
        self.assertFalse(compact["execution_allowed"])

    def test_no_raw_payload_or_secret_exposure(self):
        with self._tmp() as tmp:
            result = map_market_state({"asset_type": "stock", "provider_payload": {"raw": "drop"}, "auth_token": "hide"}, base_data_dir=tmp)
        text = str(result)
        self.assertNotIn("provider_payload", text)
        self.assertNotIn("hide", text)
        self.assertFalse(result["raw_payload_included"])

    def test_no_execution_provider_write_regression(self):
        with self._tmp() as tmp:
            result = run_cross_asset_manifold_review([self._crypto_breakout()], persist=True, base_data_dir=tmp)
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["provider_write"])
        self.assertEqual(result["execution_allowed_count"], 0)

    def test_manifold_endpoints_compact(self):
        client = TestClient(app)
        response = client.post(
            "/api/automation/manifold-map",
            json={"item": self._crypto_breakout()},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertFalse(payload["auto_execution"])
        self.assertEqual(payload["actual_orders_submitted"], 0)
        self.assertEqual(payload["actual_bets_submitted"], 0)
        self.assertEqual(payload["actual_trades_submitted"], 0)
        self.assertTrue(payload["human_approval_required"])
        self.assertFalse(payload["item"]["auto_execution"])
        self.assertEqual(payload["item"]["actual_orders_submitted"], 0)
        self.assertIn("item", payload)

        review = client.post(
            "/api/automation/cross-asset-manifold-review",
            json={"dry_run": True, "persist": False, "items": [self._crypto_breakout()]},
        )
        self.assertEqual(review.status_code, 200)
        review_payload = review.json()
        self.assertFalse(review_payload["execution_allowed"])
        self.assertFalse(review_payload["provider_write"])
        self.assertFalse(review_payload["live_execution_enabled"])
        self.assertFalse(review_payload["auto_execution"])
        self.assertEqual(review_payload["actual_orders_submitted"], 0)
        self.assertEqual(review_payload["actual_bets_submitted"], 0)
        self.assertEqual(review_payload["actual_trades_submitted"], 0)
        self.assertTrue(review_payload["human_approval_required"])
        forbidden_actions = {"BUY", "SELL", "BET", "ORDER", "PLACE_BET", "PLACE_ORDER", "EXECUTE_TRADE"}
        rendered_actions = {str(item.get("recommended_action", "")).upper() for item in review_payload.get("sample_items", [])}
        self.assertTrue(rendered_actions.isdisjoint(forbidden_actions))

    def test_all_manifold_get_endpoints_preserve_no_execution_flags(self):
        client = TestClient(app)
        for path in (
            "/api/automation/manifold-clusters",
            "/api/automation/manifold-calibration",
            "/api/automation/manifold-no-bet-traps",
        ):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertFalse(payload["provider_write"])
                self.assertFalse(payload["execution_allowed"])
                self.assertFalse(payload["live_execution_enabled"])
                self.assertFalse(payload["auto_execution"])
                self.assertEqual(payload["actual_orders_submitted"], 0)
                self.assertEqual(payload["actual_bets_submitted"], 0)
                self.assertEqual(payload["actual_trades_submitted"], 0)
                self.assertFalse(payload["raw_payload_included"])
                self.assertFalse(payload["secrets_included"])
                self.assertTrue(payload["human_approval_required"])

    def test_existing_institutional_execution_desk_safety_regression(self):
        with self._tmp() as tmp:
            result = simulate_execution(
                {"simulation_only": True, "candidate_id": "candidate-1", "human_command": "simulate_only"},
                records=[{"sidecar_id": "candidate-1", "source_record_id": "candidate-1", "asset_class": "prediction_market", "provider": "kalshi_prediction_market", "liquidity_score": 90, "pricing_quality_score": 90, "risk_score": 10, "execution_allowed": False}],
                calibration_report={"asset_classes": {"prediction_market": {"matched_outcomes_count": 30}}},
                base_data_dir=tmp,
            )
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["actual_order_submitted"])


if __name__ == "__main__":
    unittest.main()
