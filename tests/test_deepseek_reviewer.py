import json
import os
import unittest
from unittest.mock import patch

import httpx

from src.services.streamlit_dashboard_facade import compact_review_input, local_crosscheck, run_deepseek_review, validate_reviewer_output


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response=None, exc=None, *args, **kwargs):
        self.response = response
        self.exc = exc

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, *args, **kwargs):
        if self.exc:
            raise self.exc
        return self.response


class TestDeepSeekReviewer(unittest.TestCase):
    def setUp(self):
        os.environ.pop("DEEPSEEK_ENABLED", None)

    def test_disabled_by_default_has_no_side_effects(self):
        result = run_deepseek_review(collector_cycle_report={"matched_outcomes_count": 0})
        self.assertEqual(result["status"], "disabled")
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["auto_execution_enabled"])
        self.assertEqual(result["reviewer_side_effects"], "none")

    def test_invalid_json_is_handled(self):
        os.environ["DEEPSEEK_ENABLED"] = "true"
        response = _FakeResponse({"response": "not json"})
        with patch('src.automation_scheduler_legacy.deepseek_reviewer.httpx.Client', return_value=_FakeClient(response=response)):
            result = run_deepseek_review(collector_cycle_report={})
        self.assertEqual(result["status"], "invalid_json")
        self.assertFalse(result["json_schema_valid"])
        self.assertEqual(result["reviewer_side_effects"], "none")

    def test_timeout_is_handled(self):
        os.environ["DEEPSEEK_ENABLED"] = "true"
        with patch('src.automation_scheduler_legacy.deepseek_reviewer.httpx.Client', return_value=_FakeClient(exc=httpx.TimeoutException("timeout"))):
            result = run_deepseek_review(collector_cycle_report={})
        self.assertEqual(result["status"], "timeout")
        self.assertFalse(result["local_server_reachable"])

    def test_forbidden_action_rejected(self):
        os.environ["DEEPSEEK_ENABLED"] = "true"
        payload = {
            "summary": "bad",
            "crosscheck_status": "fail",
            "risk_flags": [],
            "valuation_mismatches": [],
            "missing_inputs": [],
            "data_quality_notes": [],
            "recommended_action": "place_bet",
            "confidence": 0.9,
            "must_not_execute": True,
        }
        response = _FakeResponse({"response": json.dumps(payload)})
        with patch('src.automation_scheduler_legacy.deepseek_reviewer.httpx.Client', return_value=_FakeClient(response=response)):
            result = run_deepseek_review(collector_cycle_report={})
        self.assertEqual(result["status"], "review_rejected")
        self.assertTrue(result["forbidden_actions_rejected"])
        self.assertEqual(result["reviewer_side_effects"], "none")

    def test_valid_output_schema(self):
        valid, reason = validate_reviewer_output(
            {
                "summary": "ok",
                "crosscheck_status": "pass",
                "risk_flags": [],
                "valuation_mismatches": [],
                "missing_inputs": [],
                "data_quality_notes": [],
                "recommended_action": "continue_collecting",
                "confidence": 0.5,
                "must_not_execute": True,
            }
        )
        self.assertIsNone(reason)
        self.assertTrue(valid["must_not_execute"])

    def test_valuation_mismatch_detection(self):
        review_input = compact_review_input(
            sampled_contracts=[
                {
                    "ticker": "KXBAD",
                    "liquidity_score": 150,
                    "spread_score": 50,
                    "pricing_quality_score": 100,
                    "close_time_score": 35,
                    "market_structure_score": 50,
                    "risk_score": 40,
                    "confidence_score": 40,
                    "review_priority_score": 60,
                    "liquidity_tier": "adequate_liquidity",
                    "implied_probability": None,
                }
            ]
        )
        checks = local_crosscheck(review_input)
        self.assertTrue(any("liquidity_score_outside_0_100" in item for item in checks["valuation_mismatches"]))
        self.assertTrue(any("missing_implied_probability" in item for item in checks["missing_inputs"]))


if __name__ == "__main__":
    unittest.main()
