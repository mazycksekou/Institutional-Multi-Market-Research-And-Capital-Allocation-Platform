import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import automation_scheduler
from automation_scheduler.collector_scheduled_runner import (
    build_scheduled_collector_config,
    run_scheduled_collector_cycle,
    validate_cron_token,
)
from main import app


class TestCollectorScheduledRunner(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rejects_missing_collector_cron_token_env(self):
        with patch.dict(os.environ, {}, clear=True):
            ok, status_code, payload = validate_cron_token("provided")
        self.assertFalse(ok)
        self.assertEqual(status_code, 503)
        self.assertEqual(payload["status"], "scheduled_endpoint_disabled")
        self.assertNotIn("provided", str(payload))

    def test_endpoint_rejects_missing_header(self):
        with patch.dict(os.environ, {"COLLECTOR_CRON_TOKEN": "secret"}, clear=False):
            response = self.client.post("/api/automation/calibration-collector/scheduled-run", json={})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("secret", response.text)

    def test_endpoint_rejects_wrong_token(self):
        with patch.dict(os.environ, {"COLLECTOR_CRON_TOKEN": "secret"}, clear=False):
            response = self.client.post(
                "/api/automation/calibration-collector/scheduled-run",
                headers={"X-Collector-Token": "wrong"},
                json={},
            )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("secret", response.text)
        self.assertNotIn("wrong", response.text)

    def test_endpoint_accepts_correct_token_and_returns_compact_report(self):
        with patch.dict(os.environ, {"COLLECTOR_CRON_TOKEN": "secret"}, clear=False):
            with patch(
                "automation_scheduler.run_automation_calibration_collector_scheduled",
                return_value={
                    "ok": True,
                    "status": "collector_cycle_complete",
                    "cycle_id": "scheduled-1",
                    "dry_run": False,
                    "persist_outcomes": True,
                    "markets_scanned": 0,
                    "provider_write": False,
                    "execution_allowed_count": 0,
                    "live_execution_enabled": False,
                    "storage_backend": "file",
                    "storage_health": {
                        "env_var": "AUTOMATION_DATA_DIR",
                        "data_dir": "/var/data",
                        "backend": "file",
                        "configured": True,
                        "render_persistent_disk_expected": True,
                        "persistence_warning": None,
                        "read_ok": True,
                        "write_ok": True,
                    },
                },
            ) as mocked:
                response = self.client.post(
                    "/api/automation/calibration-collector/scheduled-run",
                    headers={"X-Collector-Token": "secret"},
                    json={
                        "trigger_type": "render_cron",
                        "target_daily_new_contracts": 100,
                        "hard_cap_daily_new_contracts": 250,
                        "max_new_contracts_per_cycle": 25,
                        "max_markets_scanned": 5000,
                        "adaptive_throttle": True,
                    },
                )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "collector_cycle_complete")
        self.assertFalse(payload["provider_write"])
        self.assertEqual(payload["execution_allowed_count"], 0)
        self.assertEqual(payload["storage"]["env_var"], "AUTOMATION_DATA_DIR")
        self.assertNotIn("secret", response.text)
        self.assertEqual(mocked.call_args.args[0]["max_new_contracts_per_cycle"], 25)

    def test_rejects_unsafe_overrides_before_collector_runs(self):
        config, errors = build_scheduled_collector_config(
            {
                "provider_write": True,
                "submit_live_order": True,
                "live_execution_requested": True,
                "hard_cap_daily_new_contracts": 999999,
            }
        )
        self.assertEqual(config["hard_cap_daily_new_contracts"], 999999)
        self.assertIn("provider_write_rejected", errors)
        self.assertIn("submit_live_order_rejected", errors)
        self.assertIn("live_execution_requested_rejected", errors)
        self.assertIn("hard_cap_daily_new_contracts_exceeds_scheduled_cap", errors)

    def test_endpoint_rejects_unsafe_overrides(self):
        with patch.dict(os.environ, {"COLLECTOR_CRON_TOKEN": "secret"}, clear=False):
            response = self.client.post(
                "/api/automation/calibration-collector/scheduled-run",
                headers={"X-Collector-Token": "secret"},
                json={"provider_write": True, "submit_live_order": True},
            )
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertFalse(detail["provider_write"])
        self.assertEqual(detail["execution_allowed_count"], 0)

    def test_runner_maps_safe_defaults_to_collector(self):
        with patch(
            "automation_scheduler.collector_scheduled_runner.run_collector_cycle",
            return_value={
                "ok": True,
                "status": "collector_cycle_complete",
                "provider_write": False,
                "execution_allowed_count": 0,
            },
        ) as mocked:
            result = run_scheduled_collector_cycle({"trigger_type": "render_cron"})
        kwargs = mocked.call_args.kwargs
        self.assertFalse(kwargs["dry_run"])
        self.assertTrue(kwargs["persist_outcomes"])
        self.assertEqual(kwargs["max_new_contracts"], 25)
        self.assertEqual(kwargs["target_daily_new_contracts"], 100)
        self.assertEqual(kwargs["hard_cap_daily_new_contracts"], 250)
        self.assertEqual(kwargs["max_markets_scanned"], 5000)
        self.assertTrue(kwargs["adaptive_throttle"])
        self.assertFalse(result["provider_write"])
        self.assertEqual(result["actual_orders_submitted"], 0)

    def test_no_regression_execution_desk_still_rejects_live_flags(self):
        response = self.client.post(
            "/api/automation/institutional-lab/execution-desk/simulate",
            json={"simulation_only": False, "live_execution_requested": True, "submit_live_order": True},
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertFalse(detail["provider_write"])
        self.assertFalse(detail["execution_allowed"])
        self.assertFalse(detail["live_execution_enabled"])


if __name__ == "__main__":
    unittest.main()
