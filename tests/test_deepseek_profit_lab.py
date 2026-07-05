import json
import os
import tempfile
import unittest
from unittest.mock import patch

import httpx

from src.services.streamlit_dashboard_facade import evaluate_ai_provider
from src.services.streamlit_dashboard_facade import load_disagreement_queue
from src.ai.deepseek_profit_lab import run_candidate_review, run_daily_report, run_red_team_review


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    calls = []

    def __init__(self, response=None, exc=None, *args, **kwargs):
        self.response = response
        self.exc = exc

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, *args, **kwargs):
        _FakeClient.calls.append({"args": args, "kwargs": kwargs})
        if self.exc:
            raise self.exc
        return self.response


def _candidate(**extra):
    row = {
        "candidate_id": "cand-1",
        "asset_type": "prediction_market",
        "market_type": "prediction_market",
        "provider": "kalshi_prediction_market",
        "recommended_action": "ACTIVE_REVIEW",
        "calibration_bucket": "p60_70",
        "manifold_cluster_id": "cluster-a",
    }
    row.update(extra)
    return row


def _valid_review(**extra):
    payload = {
        "deepseek_status": "review_complete",
        "candidate_id": "cand-1",
        "asset_type": "prediction_market",
        "market_type": "prediction_market",
        "recommended_action": "WATCHLIST_REVIEW",
        "confidence_score": 61,
        "edge_quality_score": 44,
        "liquidity_risk_score": 72,
        "trap_risk_score": 63,
        "calibration_support_score": 35,
        "out_of_distribution_risk": 20,
        "agreement_with_core_model": True,
        "disagreement_reasons": [],
        "missing_inputs": ["settlement_sample"],
        "review_reasons": ["edge_needs_calibration_support"],
        "no_bet_reasons": [],
        "no_trade_reasons": [],
        "next_data_to_collect": ["settled_outcomes"],
        "red_team_only": True,
        "deepseek_used": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": True,
        "owner_approval_required": True,
    }
    payload.update(extra)
    return payload


def _valid_daily(**extra):
    payload = {
        "report_id": "deepseek_profit_lab_2026-06-02",
        "date": "2026-06-02",
        "strongest_review_candidates": [],
        "strongest_no_bet_no_trade_traps": [],
        "calibration_improvements": ["increase settled sample"],
        "failing_clusters": [],
        "missing_data": ["provider health"],
        "provider_issues": [],
        "disagreement_count": 0,
        "repeated_model_mistakes": [],
        "recommended_next_data_to_collect": ["outcomes"],
        "recommended_next_codex_task": "add calibration sample audit",
        "safety_status": {
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        },
        "red_team_only": True,
        "deepseek_used": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": True,
        "owner_approval_required": True,
    }
    payload.update(extra)
    return payload


class TestDeepSeekProfitLab(unittest.TestCase):
    def setUp(self):
        _FakeClient.calls = []

    def test_disabled_returns_safe_compact_response(self):
        with patch.dict(os.environ, {}, clear=True):
            result = run_candidate_review(candidate=_candidate())
        self.assertEqual(result["status"], "disabled")
        self.assertFalse(result["deepseek_used"])
        self.assertTrue(result["red_team_only"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])
        self.assertFalse(result["auto_execution"])
        self.assertTrue(result["human_approval_required"])
        self.assertTrue(result["owner_approval_required"])

    def test_missing_api_key_returns_config_missing_without_crashing(self):
        with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true"}, clear=True):
            result = run_candidate_review(candidate=_candidate())
        self.assertEqual(result["status"], "config_missing")
        self.assertEqual(result["rejected_reason"], "missing_DEEPSEEK_API_KEY")
        self.assertFalse(result["deepseek_used"])
        self.assertFalse(result["provider_write"])

    def test_deepseek_provider_accepted_only_when_allowed_by_security_policy(self):
        with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true"}, clear=True):
            allowed = evaluate_ai_provider("deepseek", persist_audit=False)
            blocked = evaluate_ai_provider("kalshi", persist_audit=False)
        self.assertEqual(allowed["status"], "ai_provider_allowed")
        self.assertFalse(allowed["execution_allowed"])
        self.assertEqual(blocked["status"], "ai_provider_not_allowed")
        self.assertFalse(blocked["provider_write"])

    def test_request_uses_compact_redacted_input_only(self):
        fake_response = _FakeResponse({"choices": [{"message": {"content": json.dumps(_valid_review())}}]})
        with patch.dict(
            os.environ,
            {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890", "DEEPSEEK_BASE_URL": "https://api.deepseek.com"},
            clear=True,
        ):
            with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                result = run_candidate_review(
                    candidate=_candidate(
                        raw_payload={"provider": "drop"},
                        api_key="sk-should-not-appear-1234567890",
                        order_payload={"side": "buy"},
                        sportsbook_bet_payload={"stake": 100},
                        provider_write=True,
                    )
                )
        body_text = json.dumps(_FakeClient.calls[0]["kwargs"]["json"])
        self.assertEqual(result["status"], "review_complete")
        compact_input = body_text.split("Compact redacted input:", 1)[1]
        self.assertNotIn('"raw_payload":', compact_input)
        self.assertNotIn('"api_key":', compact_input)
        self.assertNotIn('"order_payload":', compact_input)
        self.assertNotIn('"sportsbook_bet_payload":', compact_input)
        self.assertNotIn("sk-should-not-appear", body_text)
        self.assertNotIn("provider_write\":true", body_text.replace(" ", "").lower())
        self.assertNotIn("sk-test-secret", str(result))

    def test_valid_review_returns_strict_candidate_json(self):
        fake_response = _FakeResponse({"choices": [{"message": {"content": json.dumps(_valid_review())}}]})
        with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
            with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                result = run_candidate_review(candidate=_candidate())
        review = result["candidate_review"]
        self.assertEqual(result["status"], "review_complete")
        self.assertTrue(review["deepseek_used"])
        self.assertEqual(review["recommended_action"], "WATCHLIST_REVIEW")
        self.assertFalse(review["provider_write"])
        self.assertFalse(review["execution_allowed"])
        self.assertFalse(review["live_execution_enabled"])

    def test_invalid_json_safely_rejected(self):
        fake_response = _FakeResponse({"choices": [{"message": {"content": "not json"}}]})
        with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
            with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                result = run_candidate_review(candidate=_candidate())
        self.assertEqual(result["status"], "invalid_json")
        self.assertFalse(result["json_schema_valid"])
        self.assertFalse(result["provider_write"])

    def test_timeout_returns_safe_provider_timeout(self):
        with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
            with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(exc=httpx.TimeoutException("timeout"))):
                result = run_candidate_review(candidate=_candidate())
        self.assertEqual(result["status"], "provider_timeout")
        self.assertFalse(result["deepseek_used"])
        self.assertFalse(result["execution_allowed"])

    def test_deepseek_cannot_enable_execution_or_provider_write_or_live_execution(self):
        for field in ("execution_allowed", "provider_write", "live_execution_enabled", "auto_execution"):
            payload = _valid_review(**{field: True})
            fake_response = _FakeResponse({"choices": [{"message": {"content": json.dumps(payload)}}]})
            with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
                with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                    result = run_candidate_review(candidate=_candidate())
            self.assertEqual(result["status"], "review_rejected")
            self.assertFalse(result["provider_write"])
            self.assertFalse(result["execution_allowed"])
            self.assertFalse(result["live_execution_enabled"])

    def test_deepseek_cannot_create_executable_payloads_or_owner_approval(self):
        blocked_payloads = [
            _valid_review(order_payload={"side": "buy"}),
            _valid_review(bet_slip={"stake": 25}),
            _valid_review(owner_approval_present=True),
        ]
        for payload in blocked_payloads:
            fake_response = _FakeResponse({"choices": [{"message": {"content": json.dumps(payload)}}]})
            with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
                with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                    result = run_candidate_review(candidate=_candidate())
            self.assertEqual(result["status"], "review_rejected")
            self.assertFalse(result["provider_write"])
            self.assertFalse(result["execution_allowed"])

    def test_disagreement_queue_writes_compact_local_records_only(self):
        review = _valid_review(
            recommended_action="NO_BET",
            agreement_with_core_model=False,
            disagreement_reasons=["weak calibration"],
        )
        fake_response = _FakeResponse({"choices": [{"message": {"content": json.dumps(review)}}]})
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
                with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                    result = run_candidate_review(
                        candidate=_candidate(api_key="sk-should-not-persist-1234567890"),
                        core_model_action="ACTIVE_REVIEW",
                        base_data_dir=tmp,
                    )
            queue = load_disagreement_queue(base_data_dir=tmp)
        self.assertEqual(result["status"], "review_complete")
        self.assertEqual(queue["count"], 1)
        record_text = json.dumps(queue["items"][0])
        self.assertIn("weak calibration", record_text)
        self.assertNotIn("sk-should-not-persist", record_text)
        self.assertFalse(queue["items"][0]["provider_write"])
        self.assertFalse(queue["items"][0]["execution_allowed"])

    def test_daily_report_compact_response_contains_safety_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {}, clear=True):
                result = run_daily_report(
                    report_date="2026-06-02",
                    base_data_dir=tmp,
                    summaries={"review_queue_summary": {"total_count": 0}, "disagreement_summary": {"count": 0}},
                )
        self.assertEqual(result["status"], "disabled")
        report = result["report"]
        self.assertIn("safety_status", report)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["live_execution_enabled"])
        self.assertTrue(report["human_approval_required"])

    def test_daily_report_valid_deepseek_output(self):
        fake_response = _FakeResponse({"choices": [{"message": {"content": json.dumps(_valid_daily())}}]})
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true", "DEEPSEEK_API_KEY": "sk-test-secret-1234567890"}, clear=True):
                with patch('src.ai.deepseek_profit_lab.httpx.Client', return_value=_FakeClient(response=fake_response)):
                    result = run_daily_report(report_date="2026-06-02", base_data_dir=tmp, summaries={})
        self.assertEqual(result["status"], "daily_report_complete")
        self.assertTrue(result["report"]["deepseek_used"])
        self.assertFalse(result["report"]["safety_status"]["provider_write"])

    def test_red_team_disabled_reviews_are_safe(self):
        with patch.dict(os.environ, {}, clear=True):
            result = run_red_team_review(candidates=[_candidate()])
        self.assertEqual(result["status"], "red_team_local_only")
        self.assertEqual(result["review_count"], 1)
        self.assertFalse(result["deepseek_used"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["reviews"][0]["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
