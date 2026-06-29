import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

import src.automation_scheduler_legacy as automation_scheduler
from src.services.streamlit_dashboard_facade import evaluate_ai_provider
from src.services.streamlit_dashboard_facade import evaluate_owner_approval, sign_owner_approval
from src.services.streamlit_dashboard_facade import redact_and_limit_payload
from src.services.streamlit_dashboard_facade import evaluate_risk_limits
from src.services.streamlit_dashboard_facade import assert_no_secret_leak, contains_secret_like_content, redact_sensitive
from src.services.streamlit_dashboard_facade import EXECUTION_ATTEMPT_BLOCKED, FORBIDDEN_PROVIDER_REJECTED, OWNER_APPROVAL_MISSING, PROVIDER_WRITE_BLOCKED
from src.services.streamlit_dashboard_facade import enforce_ai_capability_boundary, kill_switch_state
from src.brokerage.readiness import evaluate_execution_authorization
from src.providers.policy.write_firewall import check_provider_write_attempt
from src.services.ledger_service import load_security_audit_records
from tests.support.action_imports import app


def _future_approval(scope=None, *, nonce="nonce-1", signing_secret="owner-secret"):
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=5)
    approval_scope = scope or {
        "action": "review_only",
        "asset_type": "stock",
        "market_type": "equity",
        "provider": "paper",
        "max_size": 0,
        "max_notional": 0,
        "time_window": "2026-06-01T00:00:00Z/2026-06-01T01:00:00Z",
    }
    payload = {
        "owner_user_id": "owner-1",
        "owner_email_hash": "hash_owner_email",
        "owner_approval_present": True,
        "owner_approval_timestamp": now.isoformat(),
        "approval_scope": approval_scope,
        "approval_expires_at": expires.isoformat(),
        "approval_nonce": nonce,
        "audit_event_id": "security_event_fixture",
    }
    payload["approval_signature"] = sign_owner_approval(
        approval_scope=approval_scope,
        approval_nonce=nonce,
        owner_email_hash=payload["owner_email_hash"],
        owner_user_id=payload["owner_user_id"],
        owner_approval_timestamp=payload["owner_approval_timestamp"],
        approval_expires_at=payload["approval_expires_at"],
        signing_secret=signing_secret,
    )
    return payload


class TestSecurityFramework(unittest.TestCase):
    def test_ai_provider_policy_accepts_deepseek_when_enabled(self):
        with patch.dict(os.environ, {"DEEPSEEK_ENABLED": "true"}, clear=True):
            result = evaluate_ai_provider("deepseek", persist_audit=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "ai_provider_allowed")
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])
        self.assertFalse(result["auto_execution"])

    def test_ai_provider_policy_rejects_openai_by_default_and_accepts_only_dual_enabled(self):
        with patch.dict(os.environ, {}, clear=True):
            rejected = evaluate_ai_provider("openai", persist_audit=False)
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["status"], "ai_provider_not_allowed")
        self.assertEqual(rejected["denial_reason"], "openai_analysis_not_explicitly_enabled")

        env = {"OPENAI_ANALYST_ENABLED": "true", "ALLOW_OPENAI_ANALYST": "true"}
        with patch.dict(os.environ, env, clear=True):
            accepted = evaluate_ai_provider("openai", persist_audit=False)
        self.assertTrue(accepted["ok"])
        self.assertEqual(accepted["status"], "ai_provider_allowed")
        self.assertFalse(accepted["can_execute"])

    def test_ai_provider_policy_rejects_unknown_and_execution_capable_providers(self):
        for provider in ("unknown_llm", "alpaca_broker", "draftkings_sportsbook", "kalshi_order", "coinbase_crypto_exchange"):
            with self.subTest(provider=provider):
                result = evaluate_ai_provider(provider, persist_audit=False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "ai_provider_not_allowed")
                self.assertFalse(result["provider_write"])
                self.assertFalse(result["execution_allowed"])

    def test_internal_deterministic_diagnostics_allowed_read_only(self):
        result = evaluate_ai_provider("python_diagnostics", persist_audit=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "internal_deterministic_diagnostics_allowed")
        self.assertTrue(result["read_only_computation"])
        self.assertFalse(result["provider_write"])

    def test_ai_capability_boundaries_block_execution_flags_payloads_and_bet_slips(self):
        payload = {
            "provider_write": True,
            "live_execution_enabled": True,
            "auto_execution": True,
            "recommended_action": "buy",
            "order_payload": {"side": "BUY", "qty": 10},
            "bet_slip": {"stake": 100},
        }
        result = enforce_ai_capability_boundary(payload, actor_provider="deepseek")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "ai_execution_authority_blocked")
        self.assertTrue(any("execution_flag_true" in item for item in result["violations"]))
        self.assertTrue(any("executable_payload" in item for item in result["violations"]))
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])

    def test_ai_can_only_flag_downgrade_disagree_or_request_more_data(self):
        result = enforce_ai_capability_boundary(
            {"recommended_action": "request_more_data", "risk_flags": ["stale_market"], "downgrade_review_priority": True},
            actor_provider="deepseek",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["ai_can_only_flag_downgrade_disagree_or_request_more_data"])

    def test_ai_cannot_disable_kill_switch(self):
        result = enforce_ai_capability_boundary({"GLOBAL_EXECUTION_KILL_SWITCH": False}, actor_provider="deepseek")
        self.assertFalse(result["ok"])
        self.assertTrue(any("kill_switch_disable_attempt" in item for item in result["violations"]))

    def test_owner_authorization_missing_invalid_expired_reused_and_ai_created_block(self):
        scope = {"action": "review_only", "asset_type": "stock", "market_type": "equity", "provider": "paper", "max_size": 0, "max_notional": 0}
        missing = evaluate_owner_approval(None, requested_scope=scope, persist_audit=False)
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["approval_denial_reason"], "owner_approval_missing")

        invalid = evaluate_owner_approval({"owner_approval_present": True, "audit_event_id": "a", "approval_nonce": "n"}, requested_scope=scope, signing_secret="wrong", persist_audit=False)
        self.assertFalse(invalid["ok"])

        expired = _future_approval(scope, signing_secret="owner-secret")
        expired["approval_expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        expired["approval_signature"] = sign_owner_approval(
            approval_scope=scope,
            approval_nonce=expired["approval_nonce"],
            owner_email_hash=expired["owner_email_hash"],
            owner_user_id=expired["owner_user_id"],
            owner_approval_timestamp=expired["owner_approval_timestamp"],
            approval_expires_at=expired["approval_expires_at"],
            signing_secret="owner-secret",
        )
        expired_result = evaluate_owner_approval(expired, requested_scope=scope, signing_secret="owner-secret", persist_audit=False)
        self.assertFalse(expired_result["ok"])
        self.assertEqual(expired_result["approval_denial_reason"], "owner_approval_expired")

        replayed = _future_approval(scope, nonce="nonce-replay", signing_secret="owner-secret")
        replay_result = evaluate_owner_approval(replayed, requested_scope=scope, signing_secret="owner-secret", used_nonces={"nonce-replay"}, persist_audit=False)
        self.assertFalse(replay_result["ok"])
        self.assertTrue(replay_result["approval_replay_detected"])

        ai_result = evaluate_owner_approval(replayed, requested_scope=scope, actor_type="ai_provider", signing_secret="owner-secret", persist_audit=False)
        self.assertFalse(ai_result["ok"])
        self.assertEqual(ai_result["approval_denial_reason"], "ai_cannot_create_owner_approval")

    def test_valid_owner_approval_is_scoped_auditable_and_does_not_enable_execution(self):
        scope = {"action": "review_only", "asset_type": "stock", "market_type": "equity", "provider": "paper", "max_size": 0, "max_notional": 0}
        approval = _future_approval(scope, signing_secret="owner-secret")
        owner = evaluate_owner_approval(approval, requested_scope=scope, signing_secret="owner-secret", persist_audit=False)
        self.assertTrue(owner["ok"])
        self.assertTrue(owner["approval_signature_valid"])
        self.assertFalse(owner["execution_allowed"])
        self.assertFalse(owner["provider_write"])

        auth = evaluate_execution_authorization(
            {"action": "review_only", "asset_type": "stock", "market_type": "equity", "provider": "paper", "max_size": 0, "max_notional": 0},
            owner_approval=approval,
            persist_audit=False,
        )
        self.assertFalse(auth["ok"])
        self.assertFalse(auth["execution_allowed"])
        self.assertTrue(auth["at_least_one_required_hard_gate_false"])

    def test_provider_write_firewall_blocks_all_execution_provider_types(self):
        providers = ("alpaca_broker", "draftkings_sportsbook", "kalshi_order", "coinbase_crypto_exchange", "schwab_stock_broker")
        for provider in providers:
            with self.subTest(provider=provider):
                result = check_provider_write_attempt(provider=provider, action="submit_order", request_payload={"provider": provider}, persist_audit=False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "provider_write_blocked")
                self.assertFalse(result["provider_write"])
                self.assertFalse(result["execution_allowed"])

    def test_kill_switch_defaults_and_missing_config_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            switches = kill_switch_state()
        self.assertTrue(switches["kill_switches_active"])
        self.assertTrue(switches["switches"]["GLOBAL_EXECUTION_KILL_SWITCH"])
        auth = evaluate_execution_authorization({"provider": "paper", "action": "review_only"}, persist_audit=False)
        self.assertIn("kill_switch_inactive", auth["execution_blockers"])

    def test_secret_safety_redacts_api_keys_auth_headers_signatures_and_raw_payloads(self):
        payload = {
            "api_key": "sk-test12345678901234567890",
            "Authorization": "Bearer abcdefghijklmnopqrstuvwxyz123456",
            "signature": "signed-value",
            "note": "sk-test12345678901234567890",
            "raw_payload": {"order": "BUY"},
        }
        redacted = redact_sensitive(payload)
        self.assertNotIn("sk-test", str(redacted))
        self.assertNotIn("Bearer abc", str(redacted))
        self.assertIn("[omitted]", str(redacted))
        assert_no_secret_leak(redacted)

    def test_response_compactor_strips_raw_secrets_and_order_payloads(self):
        compact = redact_and_limit_payload(
            {
                "neutral": "sk-test12345678901234567890",
                "headers": {"Authorization": "Bearer abcdefghijklmnopqrstuvwxyz123456"},
                "order_payload": {"side": "BUY"},
                "bet_slip": {"stake": 100},
            }
        )
        text = str(compact)
        self.assertNotIn("sk-test", text)
        self.assertNotIn("Bearer abc", text)
        self.assertNotIn("BUY", text)
        self.assertNotIn("stake", text)

    def test_audit_records_for_rejections_are_compact_redacted_and_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            evaluate_ai_provider("unknown_llm", base_data_dir=tmp, persist_audit=True)
            evaluate_execution_authorization({"provider": "alpaca_broker", "action": "submit_order", "api_key": "sk-test12345678901234567890"}, base_data_dir=tmp, persist_audit=True)
            check_provider_write_attempt(provider="alpaca_broker", action="submit_order", request_payload={"token": "Bearer abcdefghijklmnopqrstuvwxyz123456"}, base_data_dir=tmp, persist_audit=True)
            evaluate_owner_approval(None, requested_scope={"provider": "paper"}, base_data_dir=tmp, persist_audit=True)
            audit = load_security_audit_records(base_data_dir=tmp, limit=20)
        event_types = {item["event_type"] for item in audit["items"]}
        self.assertIn(FORBIDDEN_PROVIDER_REJECTED, event_types)
        self.assertIn(EXECUTION_ATTEMPT_BLOCKED, event_types)
        self.assertIn(PROVIDER_WRITE_BLOCKED, event_types)
        self.assertIn(OWNER_APPROVAL_MISSING, event_types)
        self.assertFalse(audit["provider_write"])
        self.assertFalse(audit["execution_allowed"])
        self.assertNotIn("sk-test", str(audit))
        self.assertNotIn("Bearer abc", str(audit))
        self.assertFalse(contains_secret_like_content(audit))

    def test_risk_guard_missing_limits_fail_closed_and_never_enable_execution(self):
        missing = evaluate_risk_limits({"notional": 10}, risk_limits={}, persist_audit=False)
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["risk_limit_status"], "execution_locked")
        self.assertFalse(missing["execution_allowed"])

        active = evaluate_risk_limits(
            {"notional": 10, "spread_percent": 0.01, "slippage_estimate": 0.01},
            risk_limits={
                "risk_limit_status": "active",
                "max_order_notional": 100,
                "max_daily_notional": 100,
                "max_daily_loss": 10,
                "max_position_count": 1,
                "max_correlation_exposure": 0,
                "max_provider_exposure": 0,
                "max_asset_class_exposure": 0,
                "max_slippage": 0.02,
                "max_spread": 0.02,
                "max_open_orders": 0,
            },
            persist_audit=False,
        )
        self.assertTrue(active["ok"])
        self.assertFalse(active["risk_guard_can_enable_execution"])
        self.assertFalse(active["provider_write"])

    def test_security_readiness_endpoint_locked_read_only(self):
        client = TestClient(app)
        with patch.dict(os.environ, {"OPENAI_ANALYST_ENABLED": "false", "ALLOW_OPENAI_ANALYST": "false"}, clear=False):
            response = client.get("/api/automation/security-readiness")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "security_readiness")
        self.assertEqual(payload["security_posture"], "locked_read_only")
        self.assertEqual(payload["default_ai_provider"], "deepseek")
        self.assertIn("deepseek", payload["ai_allowed_providers"])
        self.assertIn("openai", payload["ai_allowed_providers"])
        self.assertFalse(payload["openai_enabled_for_analysis"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertFalse(payload["auto_execution"])
        self.assertTrue(payload["human_approval_required"])
        self.assertTrue(payload["owner_approval_required"])
        self.assertTrue(payload["kill_switches_active"])
        self.assertFalse(payload["secrets_detected"])
        self.assertFalse(payload["raw_payload_exposed"])

    def test_scheduler_wrappers_preserve_no_execution(self):
        readiness = automation_scheduler.get_security_readiness()
        ai = automation_scheduler.evaluate_ai_analyst_provider("deepseek", persist_audit=False)
        boundary = automation_scheduler.enforce_ai_analysis_boundaries({"action": "request_more_data"}, actor_provider="deepseek")
        write = automation_scheduler.check_provider_write_firewall(provider="paper", action="review_only", persist_audit=False)
        auth = automation_scheduler.evaluate_execution_security_authorization({"provider": "paper", "action": "review_only"}, persist_audit=False)
        for payload in (readiness, ai, boundary, write, auth):
            self.assertFalse(payload["provider_write"])
            self.assertFalse(payload["execution_allowed"])
            self.assertFalse(payload["live_execution_enabled"])
            self.assertFalse(payload["auto_execution"])
            self.assertTrue(payload["human_approval_required"])
            self.assertTrue(payload["owner_approval_required"])


if __name__ == "__main__":
    unittest.main()
