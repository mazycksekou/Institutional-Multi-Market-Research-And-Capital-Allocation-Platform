import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from automation_scheduler.causal_scaffold import build_causal_scaffold_report, evaluate_causal_hypothesis
from automation_scheduler.cross_asset_intelligence_router import route_cross_asset_intelligence
from automation_scheduler.data_intelligence_registry import build_data_intelligence_registry
from automation_scheduler.deep_learning_research_lanes import build_deep_learning_research_lanes
from automation_scheduler.graph_relationship_mapper import map_graph_relationships
from automation_scheduler.model_maturity_registry import build_mdp_review_policy_scaffold, build_model_maturity_registry, validate_mdp_action_space
from automation_scheduler.representation_feature_builder import build_representation_vector
from automation_scheduler.response_compactor import compact_intelligence_readiness_response
from automation_scheduler.tabular_ml_research import build_tabular_ml_research_lanes
from automation_scheduler.intelligence_readiness_report import build_intelligence_readiness_report
from main import app


class TestDataIntelligenceStack(unittest.TestCase):
    def test_data_intelligence_registry_creation(self):
        registry = build_data_intelligence_registry(total_labeled_outcomes=0)
        self.assertTrue(registry["ok"])
        self.assertIn("prediction_markets", registry["supported_domains"])
        self.assertIn("deterministic_representation_vectors", registry["build_now"])
        self.assertFalse(registry["provider_write"])
        self.assertFalse(registry["execution_allowed"])
        self.assertFalse(registry["live_execution_enabled"])

    def test_model_maturity_status_defaults_and_required_fields(self):
        registry = build_model_maturity_registry(total_labeled_outcomes=0)
        required = {
            "model_family",
            "model_name",
            "asset_type",
            "market_type",
            "model_maturity_status",
            "data_requirement_level",
            "compute_requirement_level",
            "interpretability_score",
            "current_sample_size",
            "required_sample_size",
            "outcome_coverage",
            "calibration_status",
            "insufficient_sample",
            "blocked_reason",
            "research_only",
            "affects_review_queue",
            "affects_execution",
            "provider_write",
            "execution_allowed",
            "live_execution_enabled",
            "human_approval_required",
        }
        for model in registry["models"]:
            self.assertTrue(required.issubset(model.keys()))
            self.assertFalse(model["provider_write"])
            self.assertFalse(model["execution_allowed"])
            self.assertFalse(model["live_execution_enabled"])
            self.assertFalse(model["affects_execution"])

    def test_research_only_models_cannot_affect_review_queue_or_execution(self):
        registry = build_model_maturity_registry(total_labeled_outcomes=10000)
        research_models = [row for row in registry["models"] if row["research_only"]]
        self.assertGreaterEqual(len(research_models), 7)
        for model in research_models:
            self.assertFalse(model["affects_review_queue"])
            self.assertFalse(model["affects_execution"])
            self.assertFalse(model["execution_allowed"])

    def test_xgboost_lightgbm_blocked_when_outcomes_insufficient(self):
        lanes = build_tabular_ml_research_lanes(total_labeled_outcomes=25)
        by_name = {row["model_name"]: row for row in lanes["lanes"]}
        self.assertEqual(by_name["XGBoost Calibration Lane"]["model_status"], "blocked_insufficient_data")
        self.assertEqual(by_name["LightGBM Calibration Lane"]["model_status"], "blocked_insufficient_data")
        self.assertEqual(by_name["Tabular Foundation Model Research Lane"]["model_status"], "research_only")
        self.assertFalse(lanes["training_enabled"])
        self.assertFalse(lanes["execution_allowed"])

    def test_mdp_action_space_rejects_execution_actions(self):
        validation = validate_mdp_action_space(["ACTIVE_REVIEW", "BUY", "PLACE_BET", "SUBMIT_ORDER", "NO_TRADE"])
        self.assertIn("ACTIVE_REVIEW", validation["accepted_actions"])
        self.assertIn("NO_TRADE", validation["accepted_actions"])
        self.assertIn("BUY", validation["forbidden_actions_rejected"])
        self.assertIn("PLACE_BET", validation["forbidden_actions_rejected"])
        self.assertIn("SUBMIT_ORDER", validation["forbidden_actions_rejected"])
        scaffold = build_mdp_review_policy_scaffold(current_sample_size=10, allowed_actions=["ACTIVE_REVIEW", "EXECUTE"])
        self.assertIn("EXECUTE", scaffold["forbidden_actions_rejected"])
        self.assertFalse(scaffold["execution_allowed"])

    def test_causal_scaffold_not_ready_and_flags_confounding_risk(self):
        result = evaluate_causal_hypothesis(
            {
                "causal_hypothesis_id": "test",
                "treatment_variable": "injury_confirmed",
                "outcome_variable": "usage",
                "confounders": ["baseline_usage", "pace", "opponent_defense"],
            },
            records=[{"injury_confirmed": True, "usage": 1}],
            minimum_required_sample_size=50,
        )
        self.assertEqual(result["causal_status"], "not_ready")
        self.assertTrue(result["insufficient_sample"])
        self.assertGreaterEqual(result["confounding_risk_score"], 0.70)
        self.assertFalse(result["recommendation_impact_allowed"])
        report = build_causal_scaffold_report(records=[])
        self.assertEqual(report["causal_status"], "not_ready")
        self.assertFalse(report["execution_allowed"])

    def test_feature_vector_builder_works_across_asset_classes(self):
        rows = [
            {"asset_type": "prediction_market", "yes_price": 0.54, "volume": 100, "open_interest": 200},
            {"sport": "nba", "league": "NBA", "odds": -110, "line_movement_score": 70},
            {"asset_type": "stock", "symbol": "ABC", "price": 8, "relative_volume": 7, "float_shares": 5_000_000},
            {"asset_type": "crypto", "symbol": "BTC", "volume_24h": 500_000_000, "funding_rate": 0.01},
            {"asset_type": "bond_rate", "yield_change": 0.6, "macro_event_score": 80},
        ]
        asset_types = [build_representation_vector(row)["asset_type"] for row in rows]
        self.assertEqual(asset_types, ["prediction_market", "sportsbook", "stock", "crypto", "bond_rate"])
        for row in rows:
            vector = build_representation_vector(row)
            self.assertGreater(vector["embedding_dimension"], 0)
            self.assertFalse(vector["provider_write"])
            self.assertFalse(vector["execution_allowed"])

    def test_graph_relationship_mapper_compact_and_safe(self):
        graph = map_graph_relationships(
            {
                "asset_type": "prediction_market",
                "bid_ask_spread": 0.20,
                "spread_score": 20,
                "settlement_uncertainty_score": 80,
                "raw_payload": {"must": "drop"},
                "api_key": "secret-value",
            }
        )
        self.assertGreater(graph["graph_node_count"], 0)
        self.assertGreater(graph["graph_edge_count"], 0)
        self.assertTrue(graph["relationship_paths"])
        self.assertFalse(graph["provider_write"])
        self.assertFalse(graph["execution_allowed"])
        rendered = str(graph)
        self.assertNotIn("'raw_payload':", rendered)
        self.assertNotIn("drop", rendered)
        self.assertNotIn("secret-value", rendered)

    def test_deep_learning_lanes_are_research_only_disabled(self):
        lanes = build_deep_learning_research_lanes()
        self.assertFalse(lanes["training_enabled"])
        for lane in lanes["lanes"]:
            self.assertTrue(lane["research_only"])
            self.assertTrue(lane["disabled"])
            self.assertFalse(lane["affects_review_queue"])
            self.assertFalse(lane["affects_execution"])

    def test_readiness_separates_feasible_later_and_research_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_intelligence_readiness_report(base_data_dir=tmp)
        self.assertIn("deterministic_representation_vectors", report["feasible_now"])
        self.assertIn("xgboost_calibration", report["feasible_later"])
        self.assertIn("lstm", report["research_only"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["live_execution_enabled"])

    def test_fatal_safety_blockers_override_model_optimism(self):
        routed = route_cross_asset_intelligence(
            {
                "asset_type": "stock",
                "symbol": "ABC",
                "liquidity_score": 95,
                "confidence_score": 95,
                "estimated_edge": 0.20,
                "execution_allowed": True,
                "action": "BUY",
            },
            total_labeled_outcomes=1000,
        )
        self.assertTrue(routed["safety_override_applied"])
        self.assertFalse(routed["affects_review_queue"])
        self.assertEqual(routed["final_review_action"], "NO_TRADE_SESSION_LOCK")
        self.assertLess(routed["final_review_adjustment"], 0)
        self.assertFalse(routed["execution_allowed"])

    def test_compact_response_safety_and_no_provider_write_regression(self):
        compact = compact_intelligence_readiness_response(
            {
                "ok": True,
                "status": "intelligence_readiness",
                "provider_write": True,
                "execution_allowed": True,
                "live_execution_enabled": True,
                "active_review_models": ["a"] * 20,
                "research_only": ["lstm"],
                "safety_status": {"kill_switches_active": True},
            },
            limit=5,
        )
        self.assertEqual(len(compact["active_review_models"]), 5)
        self.assertFalse(compact["provider_write"])
        self.assertFalse(compact["execution_allowed"])
        self.assertFalse(compact["live_execution_enabled"])
        self.assertTrue(compact["human_approval_required"])
        self.assertFalse(compact["raw_payload_included"])

    def test_intelligence_readiness_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = TestClient(app).get("/api/automation/intelligence-readiness?limit=20")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "intelligence_readiness")
        self.assertIn("feasible_now", payload)
        self.assertIn("feasible_later", payload)
        self.assertIn("research_only", payload)
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertNotIn("provider_payload", str(payload).lower())


if __name__ == "__main__":
    unittest.main()
