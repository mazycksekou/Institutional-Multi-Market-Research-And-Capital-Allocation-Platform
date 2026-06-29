import tempfile
import unittest
from unittest.mock import Mock, patch

from src.services.streamlit_dashboard_facade import run_deepseek_sidecar_review


class TestInstitutionalDeepSeekReview(unittest.TestCase):
    def test_disabled_by_default_has_no_side_effect_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_deepseek_sidecar_review(report={"provider_payload": {"raw": "drop"}}, enabled=False, base_data_dir=tmp)
        self.assertEqual(result["status"], "disabled")
        self.assertFalse(result["provider_write"])
        self.assertEqual(result["reviewer_side_effects"], "none")
        self.assertTrue(result["review"]["must_not_execute"])
        self.assertNotIn("provider_payload", str(result))

    @patch('src.automation_scheduler_legacy.institutional_deepseek_review.httpx.post')
    def test_local_server_unavailable_is_safe(self, post):
        post.side_effect = RuntimeError("down")
        with tempfile.TemporaryDirectory() as tmp:
            result = run_deepseek_sidecar_review(report={}, enabled=True, base_data_dir=tmp)
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["local_server_reachable"])
        self.assertFalse(result["provider_write"])

    @patch('src.automation_scheduler_legacy.institutional_deepseek_review.httpx.post')
    def test_forbidden_action_is_rejected(self, post):
        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {
            "summary": "bad",
            "crosscheck_status": "pass",
            "asset_class_findings": {},
            "valuation_mismatches": [],
            "risk_flags": [],
            "execution_desk_warnings": [],
            "missing_inputs": [],
            "data_quality_notes": [],
            "recommended_action": "place_bet",
            "confidence": 1,
            "must_not_execute": True,
        }
        post.return_value = response
        with tempfile.TemporaryDirectory() as tmp:
            result = run_deepseek_sidecar_review(report={}, enabled=True, base_data_dir=tmp)
        self.assertEqual(result["status"], "rejected")
        self.assertTrue(result["forbidden_actions_rejected"])
        self.assertFalse(result["provider_write"])

    @patch('src.automation_scheduler_legacy.institutional_deepseek_review.httpx.post')
    def test_valid_schema_passes_without_side_effects(self, post):
        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {
            "summary": "ok",
            "crosscheck_status": "warning",
            "asset_class_findings": {"prediction_market": []},
            "valuation_mismatches": [],
            "risk_flags": ["insufficient_sample"],
            "execution_desk_warnings": [],
            "missing_inputs": [],
            "data_quality_notes": [],
            "recommended_action": "continue_collecting",
            "confidence": 0.5,
            "must_not_execute": True,
        }
        post.return_value = response
        with tempfile.TemporaryDirectory() as tmp:
            result = run_deepseek_sidecar_review(report={"api_key": "secret"}, enabled=True, base_data_dir=tmp)
        self.assertEqual(result["status"], "review_complete")
        self.assertTrue(result["json_schema_valid"])
        self.assertEqual(result["reviewer_side_effects"], "none")
        self.assertNotIn("secret", str(result))


if __name__ == "__main__":
    unittest.main()
