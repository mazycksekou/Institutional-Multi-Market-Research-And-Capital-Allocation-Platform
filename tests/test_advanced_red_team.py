import json
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.services.streamlit_dashboard_facade import evaluate_advanced_red_team_provider
from src.analytics.advanced_red_team_report import build_advanced_red_team_report
from src.services.streamlit_dashboard_facade import get_advanced_diagnostic_registry, run_advanced_shape_diagnostics
from src.services.streamlit_dashboard_facade import run_bayesian_structural_baseline
from src.services.streamlit_dashboard_facade import run_causal_discovery_research
from src.services.streamlit_dashboard_facade import run_conformal_uncertainty
from src.services.streamlit_dashboard_facade import run_contrastive_embedding_diagnostics, run_nonlinear_embedding_diagnostics
from src.services.streamlit_dashboard_facade import run_dynamical_systems_diagnostics, run_sliding_window_topology
from src.services.streamlit_dashboard_facade import run_information_theory_diagnostics
from src.services.streamlit_dashboard_facade import run_topological_red_team
from tests.support.action_imports import app


def _candidate(**extra):
    row = {
        "candidate_id": "adv-1",
        "asset_type": "prediction_market",
        "market_type": "prediction_market",
        "provider": "internal_deterministic",
        "edge_estimate": 0.08,
        "liquidity_tier": "low",
        "score": 72,
        "time_to_close": 12,
    }
    row.update(extra)
    return row


def _history(count=12):
    return [
        {
            "candidate_id": f"h-{i}",
            "asset_type": "prediction_market",
            "score": 50 + i,
            "edge_estimate": 0.01 * (i % 5),
            "liquidity": 100 + i,
            "time_to_close": 20 - (i % 8),
            "outcome_value": 0.01 * ((i % 3) - 1),
        }
        for i in range(count)
    ]


def _labeled(count=40):
    return [
        {
            "score": 80 if i % 2 else 20,
            "signal": 1 if i % 2 else 0,
            "outcome": "yes" if i % 2 else "no",
            "edge_estimate": 0.05 if i % 2 else -0.02,
            "final_outcome": "win" if i % 2 else "loss",
        }
        for i in range(count)
    ]


def _calibration(count=60, residual=0.04):
    return [{"prediction": 0.50, "actual": 0.50 + ((-1) ** i) * residual} for i in range(count)]


class TestAdvancedRedTeamProviderPolicy(unittest.TestCase):
    def test_advanced_diagnostic_registry_defaults(self):
        registry = get_advanced_diagnostic_registry()
        self.assertIn("topological_persistent_homology", registry)
        self.assertIn("conformal_uncertainty", registry)
        for row in registry.values():
            self.assertTrue(row["red_team_only"])
            self.assertFalse(row["provider_write"])
            self.assertFalse(row["execution_allowed"])

    def test_deepseek_provider_accepted_when_enabled(self):
        with patch.dict("os.environ", {"ADVANCED_RED_TEAM_ENABLED": "true", "ADVANCED_RED_TEAM_PROVIDER": "deepseek", "DEEPSEEK_ENABLED": "true"}, clear=True):
            result = evaluate_advanced_red_team_provider()
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "deepseek")
        self.assertEqual(result["status"], "red_team_provider_allowed")
        self.assertFalse(result["provider_write"])

    def test_openai_provider_rejected_by_default(self):
        with patch.dict("os.environ", {"ADVANCED_RED_TEAM_ENABLED": "true", "ADVANCED_RED_TEAM_PROVIDER": "openai"}, clear=True):
            result = evaluate_advanced_red_team_provider()
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "provider_not_allowed_for_red_team")
        self.assertFalse(result["openai_used"])

    def test_openai_provider_accepted_only_when_both_flags_enabled(self):
        with patch.dict(
            "os.environ",
            {
                "ADVANCED_RED_TEAM_ENABLED": "true",
                "ADVANCED_RED_TEAM_PROVIDER": "openai",
                "OPENAI_RED_TEAM_ENABLED": "true",
                "ADVANCED_RED_TEAM_ALLOW_OPENAI": "true",
            },
            clear=True,
        ):
            result = evaluate_advanced_red_team_provider()
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "openai")
        self.assertFalse(result["execution_allowed"])

    def test_any_other_provider_rejected(self):
        with patch.dict("os.environ", {"ADVANCED_RED_TEAM_PROVIDER": "anthropic"}, clear=True):
            result = evaluate_advanced_red_team_provider()
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "provider_not_allowed_for_red_team")

    def test_internal_deterministic_diagnostics_allowed(self):
        result = evaluate_advanced_red_team_provider("internal_deterministic")
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "internal_deterministic_diagnostics_allowed")
        self.assertFalse(result["external_ai_call_performed"])


class TestAdvancedDiagnostics(unittest.TestCase):
    def test_red_team_output_includes_required_safety_flags_and_provider_usage(self):
        result = run_advanced_shape_diagnostics(_candidate(), historical_records=_history(), provider="internal_deterministic")
        self.assertTrue(result["red_team_only"])
        self.assertFalse(result["deepseek_used"])
        self.assertFalse(result["openai_used"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])

    def test_tda_blocked_missing_dependency_behavior(self):
        result = run_topological_red_team(_candidate(), historical_records=_history(40), dependency_available=False)
        self.assertEqual(result["persistent_homology_status"], "blocked_missing_dependency")
        self.assertEqual(result["status"], "blocked_missing_dependency")

    def test_umap_laplacian_fallback_to_deterministic_vector_similarity(self):
        result = run_nonlinear_embedding_diagnostics(_candidate(score=70), historical_records=_history(10))
        self.assertEqual(result["embedding_status"], "deterministic_fallback")
        self.assertEqual(result["embedding_method"], "deterministic_vector_similarity_fallback")

    def test_sliding_window_topology_insufficient_sequence_behavior(self):
        result = run_sliding_window_topology([1, 2, 3])
        self.assertTrue(result["insufficient_sequence_length"])
        self.assertEqual(result["sliding_window_topology_status"], "insufficient_sequence_length")

    def test_graph_density_sparse_region_detection(self):
        result = run_advanced_shape_diagnostics(
            _candidate(score=999, edge_estimate=99),
            historical_records=_history(8),
            provider="internal_deterministic",
        )
        self.assertIn(result["sparse_region_risk"], {"high", "moderate", "data_insufficient"})
        self.assertIn("graph_cluster_density", result)

    def test_mutual_information_output_shape(self):
        result = run_information_theory_diagnostics(records=_labeled(30))
        self.assertIn("mutual_information_score", result)
        self.assertIn("transfer_entropy_score", result)
        self.assertFalse(result["provider_write"])

    def test_transfer_entropy_fake_edge_warning(self):
        result = run_information_theory_diagnostics(candidate={"mutual_information_score": 0.7, "transfer_entropy_score": 0.01})
        self.assertTrue(result["fake_edge_information_risk"])
        self.assertIn("static_correlation_not_predictive", result["information_no_bet_reasons"])

    def test_conformal_prediction_insufficient_sample_behavior(self):
        result = run_conformal_uncertainty(_candidate(), calibration_records=_calibration(5))
        self.assertEqual(result["conformal_status"], "blocked_insufficient_data")
        self.assertTrue(result["uncertainty_too_wide"])

    def test_contrastive_embedding_insufficient_labeled_data_behavior(self):
        result = run_contrastive_embedding_diagnostics(_candidate(), labeled_records=_labeled(5))
        self.assertEqual(result["contrastive_status"], "blocked_insufficient_data")
        self.assertTrue(result["insufficient_sample"])

    def test_edm_s_map_surrogate_comparison_output_shape(self):
        result = run_dynamical_systems_diagnostics([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        self.assertIn("forecast_skill_rho", result)
        self.assertIn("surrogate_skill_rho", result)
        self.assertIn("skill_above_surrogate", result)

    def test_causal_discovery_not_ready_behavior(self):
        result = run_causal_discovery_research(_candidate(), records=_labeled(10))
        self.assertEqual(result["causal_graph_support"], "not_ready")
        self.assertEqual(result["causal_status"], "not_ready")
        self.assertFalse(result["causal_claim_allowed"])

    def test_bayesian_structural_baseline_insufficient_data_behavior(self):
        result = run_bayesian_structural_baseline(_candidate(), baseline_records=_history(5))
        self.assertEqual(result["bayesian_baseline_status"], "blocked_insufficient_data")
        self.assertTrue(result["counterfactual_no_edge_warning"])

    def test_advanced_red_team_report_compact_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_advanced_red_team_report(
                candidate=_candidate(),
                historical_records=_history(15),
                labeled_records=_labeled(10),
                calibration_records=_calibration(5),
                provider="internal_deterministic",
                persist_report=True,
                base_data_dir=tmp,
            )
        self.assertEqual(result["status"], "advanced_red_team_report")
        self.assertEqual(result["candidate_count"], 1)
        self.assertIn("persistence", result)
        self.assertTrue(result["red_team_only"])

    def test_fatal_safety_blockers_override_diagnostic_optimism(self):
        result = run_advanced_shape_diagnostics(
            _candidate(provider_write=True),
            historical_records=_history(40),
            labeled_records=_labeled(40),
            calibration_records=_calibration(60),
            provider="internal_deterministic",
            fatal_safety_blocker=True,
        )
        self.assertEqual(result["advanced_red_team_status"], "fatal_safety_blocked")
        self.assertIn(result["recommended_action_adjustment"], {"NO_BET", "NO_TRADE"})
        self.assertFalse(result["provider_write"])

    def test_no_raw_payload_or_secrets_exposed(self):
        result = run_advanced_shape_diagnostics(
            _candidate(api_key="sk-should-not-appear-1234567890", raw_payload={"x": 1}, provider_payload={"x": 2}),
            historical_records=_history(10),
            provider="internal_deterministic",
        )
        text = json.dumps(result)
        self.assertNotIn("sk-should-not-appear", text)
        self.assertNotIn('"raw_payload":', text)
        self.assertNotIn('"provider_payload":', text)
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])

    def test_no_provider_write_or_execution_regression(self):
        result = run_advanced_shape_diagnostics(_candidate(), provider="internal_deterministic")
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])
        self.assertFalse(result["auto_execution"])


class TestAdvancedRedTeamEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_advanced_shape_endpoint_compact_default(self):
        response = self.client.post(
            "/api/automation/advanced-shape-diagnostics",
            json={
                "dry_run": True,
                "provider": "internal_deterministic",
                "candidate": _candidate(),
                "historical_records": _history(8),
                "calibration_records": _calibration(5),
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["red_team_only"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertEqual(payload["items"][0]["candidate_id"], "adv-1")

    def test_advanced_report_endpoint_compact_default(self):
        response = self.client.get("/api/automation/advanced-red-team-report?provider=internal_deterministic")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "advanced_red_team_report")
        self.assertTrue(payload["red_team_only"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])

    def test_provider_rejection_output_shape(self):
        response = self.client.post(
            "/api/automation/advanced-shape-diagnostics",
            json={"dry_run": True, "provider": "anthropic", "candidate": _candidate()},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "provider_not_allowed_for_red_team")
        self.assertEqual(payload["allowed_ai_providers"], ["deepseek", "openai"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
