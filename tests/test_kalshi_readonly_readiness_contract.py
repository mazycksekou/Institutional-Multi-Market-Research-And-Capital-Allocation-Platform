import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from src.services.streamlit_dashboard_facade import REQUIRED_ENV_NAMES, build_kalshi_readonly_readiness_report
from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter


class TestKalshiReadonlyReadinessContract(unittest.TestCase):
    def setUp(self):
        for name in REQUIRED_ENV_NAMES:
            os.environ.pop(name, None)
        for name in (
            "KALSHI_API_BASE_URL",
            "KALSHI_API_TIMEOUT_SECONDS",
            "KALSHI_MARKETS_PATH",
            "KALSHI_EVENTS_PATH",
        ):
            os.environ.pop(name, None)

    def test_readiness_script_exists(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "check_kalshi_readonly_ready.ps1"
        self.assertTrue(script.exists())

    def test_missing_credentials_reported_without_values(self):
        report = build_kalshi_readonly_readiness_report(load_env=False)
        rendered = json.dumps(report, sort_keys=True)
        self.assertEqual(report["provider_readiness_status"], "provider_not_ready")
        self.assertFalse(report["credentials_present"])
        self.assertIn("KALSHI_API_KEY", report["missing_env_names"])
        self.assertIn("KALSHI_API_SECRET", report["missing_env_names"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertNotIn("api_key_value", rendered)
        self.assertNotIn("private_key_value", rendered)

    def test_live_reads_disabled_reported_clearly(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_do_not_print_12345"
        os.environ["KALSHI_API_SECRET"] = "kalshi_secret_do_not_print_12345"
        report = build_kalshi_readonly_readiness_report(load_env=False)
        rendered = json.dumps(report, sort_keys=True)
        self.assertEqual(report["provider_readiness_status"], "provider_not_ready")
        self.assertFalse(report["credentials_present"])
        self.assertFalse(report["live_reads_enabled"])
        self.assertIn("live_reads_disabled", report["provider_readiness_blockers"])
        self.assertIn("KALSHI_LIVE_READS_ENABLED", report["missing_env_names"])
        self.assertNotIn("kalshi_key_do_not_print_12345", rendered)
        self.assertNotIn("kalshi_secret_do_not_print_12345", rendered)

    def test_no_provider_calls_by_default_even_when_ready(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_do_not_print_12345"
        os.environ["KALSHI_API_SECRET"] = "kalshi_secret_do_not_print_12345"
        with patch.object(KalshiReadonlyAdapter, "fetch_markets", side_effect=AssertionError("provider call not allowed by default")):
            report = build_kalshi_readonly_readiness_report(load_env=False)
        self.assertEqual(report["provider_readiness_status"], "provider_not_ready")
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["tiny_connectivity_check_status"], "not_requested")
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_tiny_connectivity_check_strips_provider_payload(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_do_not_print_12345"
        os.environ["KALSHI_API_SECRET"] = "kalshi_secret_do_not_print_12345"
        with patch.object(
            KalshiReadonlyAdapter,
            "fetch_markets",
            return_value={"ok": True, "status": "ok", "records": [{"ticker": "KX", "raw": "drop"}], "errors": []},
        ) as fetch:
            report = build_kalshi_readonly_readiness_report(load_env=False, tiny_connectivity_check=True)
        rendered = json.dumps(report, sort_keys=True)
        fetch.assert_not_called()
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["provider_calls_succeeded"], 0)
        self.assertEqual(report["provider_calls_failed"], 0)
        self.assertEqual(report["tiny_connectivity_check_status"], "skipped_provider_not_ready")
        self.assertNotIn("KX", rendered)
        self.assertNotIn("drop", rendered)
        self.assertNotIn("kalshi_key_do_not_print_12345", rendered)
        self.assertNotIn("kalshi_secret_do_not_print_12345", rendered)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])


if __name__ == "__main__":
    unittest.main()
