import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from automation_scheduler.data_source_registry import MANDATORY_LANES
from tests.support.action_imports import app


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
        self.assertFalse(payload["secrets_included"])
        self.assertNotIn("do-not-leak", str(payload).lower())
        self.assertNotIn("provider_payload", str(payload).lower())

    def test_registry_endpoint_module_filter_accepts_nba(self):
        response = self.client.get("/api/automation/data-sources/registry?module=nba&limit=100")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_lanes"], 1)
        self.assertEqual(payload["lanes"][0]["lane_id"], "basketball_nba")

    def test_registry_endpoint_module_filter_accepts_stock_and_crypto_lanes(self):
        stock = self.client.get("/api/automation/data-sources/registry?module=institutional_stock_pro_analyst&limit=100")
        crypto = self.client.get("/api/automation/data-sources/registry?module=cryptocurrency_edge_lab&limit=100")
        self.assertEqual(stock.status_code, 200)
        self.assertEqual(crypto.status_code, 200)
        self.assertEqual(stock.json()["lanes"][0]["lane_id"], "institutional_stock_pro_analyst")
        self.assertEqual(crypto.json()["lanes"][0]["lane_id"], "cryptocurrency_edge_lab")
        self.assertEqual(crypto.json()["lanes"][0]["module_priority"], "highest")

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
        self.assertEqual(payload["enabled_source_count"], 0)
        self.assertFalse(payload["provider_write"])

    def test_env_vars_endpoint_returns_names_only(self):
        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "do-not-leak"}, clear=False):
            response = self.client.get("/api/automation/data-sources/env-vars?module=institutional_stock_pro_analyst&limit=200")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        text = str(payload)
        self.assertIn("ALPHA_VANTAGE_API_KEY", text)
        self.assertIn("key_is_configured", payload["env_vars"][0])
        self.assertNotIn("do-not-leak", text)
        self.assertNotIn("key_value", text.lower())
        self.assertFalse(payload["provider_write"])

    def test_priorities_and_expansion_report_endpoints_work(self):
        priorities = self.client.get("/api/automation/data-sources/priorities?limit=25")
        report = self.client.get("/api/automation/data-sources/public-apis-expansion-report?limit=100")
        self.assertEqual(priorities.status_code, 200)
        self.assertEqual(report.status_code, 200)
        self.assertIn("priorities", priorities.json())
        self.assertGreater(report.json()["sources_added"], 0)
        self.assertEqual(report.json()["enabled_source_count"], 0)
        self.assertFalse(report.json()["provider_write"])

    def test_data_availability_tiers_endpoint_works_and_persists_compact_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = self.client.get("/api/automation/data-sources/data-availability/tiers?persist_report=true&limit=100")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_modules"], len(MANDATORY_LANES))
        modules = {row["module"]: row for row in payload["modules"]}
        self.assertIn("americanfootball_ncaaf", modules)
        self.assertIn("current_best_tier", modules["americanfootball_ncaaf"])
        self.assertEqual(payload["enabled_source_count"], 0)
        self.assertEqual(payload["paid_source_enabled_count"], 0)
        self.assertIn("data_sources/data_availability/latest.json", payload["latest_path"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["raw_payload_included"])
        self.assertFalse(payload["secrets_included"])
        self.assertNotIn("provider_payload", str(payload).lower())

    def test_verify_endpoint_works_and_persists_report_under_data_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = self.client.post("/api/automation/data-sources/verify?limit=100", json={"persist_report": True})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "verified")
        self.assertEqual(payload["storage"]["env_var"], "AUTOMATION_DATA_DIR")
        self.assertIn("data_sources/latest.json", payload["latest_path"])
        self.assertIn("data_sources/public_apis_expansion/latest.json", payload["public_apis_expansion_latest_path"])
        self.assertIn("data_sources/public_apis_expansion/daily/", payload["public_apis_expansion_daily_json_path"])
        self.assertIn("data_sources/public_apis_expansion/daily/", payload["public_apis_expansion_daily_markdown_path"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["raw_payload_included"])

    def test_ncaaf_cfbd_adapter_metadata_only_endpoint_is_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                os.environ.pop("CFBD_API_KEY", None)
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen") as urlopen:
                    response = self.client.post(
                        "/api/automation/data-sources/adapters/ncaaf/cfbd/verify",
                        json={"dry_run": True, "fetch_live_sample": False, "max_records": 5},
                    )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_id"], "collegefootballdata")
        self.assertEqual(payload["module"], "americanfootball_ncaaf")
        self.assertEqual(payload["adapter_status"], "metadata_only_verified")
        self.assertFalse(payload["enabled"])
        self.assertFalse(payload["fetch_live_sample_performed"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["raw_payload_included"])
        self.assertFalse(payload["secrets_included"])
        self.assertIn("latest_path", payload["report_paths"])
        self.assertNotIn("api_key", str(payload).lower().replace("missing_api_key", "").replace("api_key_configured", ""))
        urlopen.assert_not_called()

    def test_ncaaf_cfbd_adapter_missing_key_live_request_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                os.environ.pop("CFBD_API_KEY", None)
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen") as urlopen:
                    response = self.client.post(
                        "/api/automation/data-sources/adapters/ncaaf/cfbd/verify",
                        json={"dry_run": True, "fetch_live_sample": True, "max_records": 5},
                    )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["adapter_status"], "missing_api_key")
        self.assertTrue(payload["missing_api_key"])
        self.assertFalse(payload["fetch_live_sample_performed"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["raw_payload_included"])
        self.assertFalse(payload["secrets_included"])
        urlopen.assert_not_called()

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
