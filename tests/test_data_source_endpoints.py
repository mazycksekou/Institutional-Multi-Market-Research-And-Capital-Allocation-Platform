import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from automation_scheduler.data_source_registry import MANDATORY_LANES
from main import app


class TestDataSourceEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_registry_endpoint_works_and_contains_every_lane(self):
        response = self.client.get("/api/automation/data-sources/registry?limit=100")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        expected = {lane["lane_id"] for lane in MANDATORY_LANES}
        self.assertEqual({lane["lane_id"] for lane in payload["lanes"]}, expected)
        self.assertEqual(payload["total_lanes"], len(expected))
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertNotIn("secret", str(payload).lower())
        self.assertNotIn("provider_payload", str(payload).lower())

    def test_registry_endpoint_module_filter_accepts_nba(self):
        response = self.client.get("/api/automation/data-sources/registry?module=nba&limit=100")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_lanes"], 1)
        self.assertEqual(payload["lanes"][0]["lane_id"], "basketball_nba")

    def test_coverage_endpoint_works(self):
        response = self.client.get("/api/automation/data-sources/coverage?limit=100")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_modules"], len(MANDATORY_LANES))
        self.assertIn("basketball_nba", {row["lane_id"] for row in payload["modules"]})
        self.assertFalse(payload["provider_write"])

    def test_research_lanes_endpoint_works(self):
        response = self.client.get("/api/automation/data-sources/research-lanes?limit=100")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload["total_tasks"], len(MANDATORY_LANES))
        self.assertIn("tasks", payload)
        self.assertFalse(payload["execution_allowed"])

    def test_health_endpoint_works(self):
        response = self.client.get("/api/automation/data-sources/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["storage"]["env_var"], "AUTOMATION_DATA_DIR")
        self.assertFalse(payload["provider_write"])

    def test_verify_endpoint_works_and_persists_report_under_data_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = self.client.post("/api/automation/data-sources/verify?limit=100", json={"persist_report": True})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "verified")
        self.assertEqual(payload["storage"]["env_var"], "AUTOMATION_DATA_DIR")
        self.assertIn("data_sources/latest.json", payload["latest_path"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["raw_payload_included"])

    def test_no_regression_institutional_lab_and_execution_safety(self):
        health = self.client.get("/api/automation/institutional-lab/health")
        self.assertEqual(health.status_code, 200)
        self.assertFalse(health.json()["provider_write"])
        rejected = self.client.post(
            "/api/automation/institutional-lab/execution-desk/simulate",
            json={"simulation_only": False, "live_execution_requested": True, "submit_live_order": True},
        )
        self.assertEqual(rejected.status_code, 400)
        detail = rejected.json()["detail"]
        self.assertFalse(detail["provider_write"])
        self.assertFalse(detail["execution_allowed"])
        self.assertFalse(detail["live_execution_enabled"])

    def test_no_regression_kalshi_collector_endpoint_still_works(self):
        with patch(
            "automation_scheduler.run_automation_calibration_collector",
            return_value={
                "ok": True,
                "status": "collector_cycle_complete",
                "dry_run": True,
                "persist_outcomes": False,
                "provider_write": False,
                "execution_allowed_count": 0,
                "live_execution_enabled": False,
            },
        ):
            response = self.client.post(
                "/api/automation/calibration-collector/run",
                json={"dry_run": True, "persist_outcomes": False, "max_new_contracts": 1},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["provider_write"])
        self.assertEqual(payload["execution_allowed_count"], 0)
        self.assertFalse(payload["live_execution_enabled"])


if __name__ == "__main__":
    unittest.main()
