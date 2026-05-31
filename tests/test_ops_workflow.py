import json
import os
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler import ops_workflow
from automation_scheduler.data_paths import AUTOMATION_DATA_DIR_ENV


class _FakeResponse:
    status = 200

    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def close(self):
        return None


class TestOpsWorkflow(unittest.TestCase):
    def test_local_mode_works_without_app_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {AUTOMATION_DATA_DIR_ENV: tmp}
            with patch.dict(os.environ, env, clear=False):
                os.environ.pop("APP_BASE_URL", None)
                report = ops_workflow.run_ops_check(mode="local", write_report=False, skip_network=True)
        self.assertEqual(report["mode"], "local")
        self.assertIn(report["local_status"]["status"], {"ok", "code_defect"})
        self.assertNotEqual(report["render_status"]["status"], "render_endpoint_failure")

    def test_render_mode_returns_config_missing_when_app_base_url_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            report = ops_workflow.run_ops_check(mode="render", base_url=None, write_report=False)
        self.assertEqual(report["render_status"]["status"], "config_missing")

    def test_render_mode_handles_network_unavailable_without_crashing(self):
        def raise_url_error(*args, **kwargs):
            raise urllib.error.URLError("network unavailable")

        with patch("urllib.request.urlopen", side_effect=raise_url_error):
            result = ops_workflow.safe_get_json("https://example.invalid/api", timeout=1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "local_sandbox_network_unavailable")

    def test_safe_get_json_redacts_secrets_and_raw_payloads(self):
        payload = {
            "ok": True,
            "token": "secret-token",
            "nested": {"api_key": "secret-key", "requires_api_key": True},
            "raw_provider_payload": {"private": "provider-data"},
        }
        with patch("urllib.request.urlopen", return_value=_FakeResponse(payload)):
            result = ops_workflow.safe_get_json("https://example.com/api?token=secret-token")
        encoded = json.dumps(result)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("secret-key", encoded)
        self.assertNotIn("provider-data", encoded)
        self.assertEqual(result["data"]["token"], "[redacted]")
        self.assertTrue(result["data"]["nested"]["requires_api_key"])

    def test_safety_checker_catches_enabled_execution_flag(self):
        result = ops_workflow.check_safety_flags(
            [
                {
                    "provider_write": False,
                    "execution_allowed": True,
                    "execution_allowed_count": 0,
                    "live_execution_enabled": False,
                    "auto_execution_enabled": False,
                    "kalshi_order_execution_enabled": False,
                    "sportsbook_bet_execution_enabled": False,
                    "broker_order_execution_enabled": False,
                    "crypto_trade_execution_enabled": False,
                    "stock_trade_execution_enabled": False,
                    "actual_orders_submitted": 0,
                    "actual_bets_submitted": 0,
                    "actual_trades_submitted": 0,
                    "actual_crypto_swaps_submitted": 0,
                    "human_approval_required": True,
                    "paper_only": True,
                    "raw_payload_included": False,
                    "secrets_included": False,
                }
            ]
        )
        self.assertFalse(result["ok"])
        self.assertIn("execution_allowed_enabled", result["critical"])

    def test_safety_checker_passes_disabled_flags(self):
        result = ops_workflow.check_safety_flags([ops_workflow._base_safety_payload()])
        self.assertTrue(result["ok"])
        self.assertEqual(result["critical"], [])

    def test_cron_classifier_identifies_repeated_http_429(self):
        cycles = [
            {"status": "collector_cycle_complete", "provider_blockers": ["http_429"]},
            {"status": "collector_cycle_complete", "provider_blockers": ["http_429"]},
            {"status": "collector_cycle_complete", "provider_blockers": ["http_429"]},
        ]
        result = ops_workflow.classify_cron_state(cycles[0], cycles)
        self.assertEqual(result["status"], "running_but_provider_limited")
        self.assertEqual(result["repeated_http_429_count"], 3)

    def test_cron_classifier_identifies_running_but_no_settlements(self):
        latest = {
            "status": "collector_cycle_complete",
            "provider_blockers": [],
            "watchlist_size": 10,
            "explicit_settlement_count": 0,
            "outcomes_persisted": 0,
        }
        result = ops_workflow.classify_cron_state(latest, [latest])
        self.assertEqual(result["status"], "running_but_no_settlements")

    def test_storage_report_uses_automation_data_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                config = ops_workflow.get_ops_config()
        self.assertEqual(Path(config["storage"]["data_dir"]), Path(tmp).resolve())

    def test_ops_report_writes_latest_items_and_daily(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                report = {
                    "run_id": "ops_test",
                    "started_at": "2026-05-30T00:00:00Z",
                    "completed_at": "2026-05-30T00:00:01Z",
                    "mode": "local",
                    "storage_status": ops_workflow.get_storage_health(),
                    "blocker_classification": {"primary": "verification_ok", "recommended_action": "continue"},
                    "raw_payload_included": False,
                    "secrets_included": False,
                }
                result = ops_workflow.write_ops_report(report)
                paths = result["paths"]
                self.assertTrue(Path(paths["latest"]).exists())
                self.assertTrue(Path(paths["item"]).exists())
                self.assertTrue(Path(paths["daily_json"]).exists())
                self.assertTrue(Path(paths["daily_markdown"]).exists())

    def test_env_var_values_are_never_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                AUTOMATION_DATA_DIR_ENV: tmp,
                "COLLECTOR_CRON_TOKEN": "top-secret-token",
                "RENDER_API_KEY": "top-secret-render-key",
            }
            with patch.dict(os.environ, env, clear=False):
                report = ops_workflow.run_ops_check(mode="local", write_report=False, skip_network=True)
        encoded = json.dumps(report)
        self.assertNotIn("top-secret-token", encoded)
        self.assertNotIn("top-secret-render-key", encoded)

    def test_raw_payload_fields_are_removed(self):
        sanitized = ops_workflow._sanitize_payload(
            {
                "ok": True,
                "raw_payload": {"secret": "hidden"},
                "raw_payload_included": False,
            }
        )
        self.assertNotIn("raw_payload", sanitized)
        self.assertFalse(sanitized["raw_payload_included"])


if __name__ == "__main__":
    unittest.main()

