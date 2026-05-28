import unittest

from fastapi.testclient import TestClient

from main import app


class TestAutomationSchedulerEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_returns_safe_json(self):
        response = self.client.get("/api/automation/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["health"]["dry_run"])
        self.assertFalse(payload["health"]["auto_execution_enabled"])

    def test_review_queue_endpoint_returns_safe_json(self):
        response = self.client.get("/api/automation/review-queue")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertIn("items", payload)

    def test_run_once_endpoint_is_dry_run_only(self):
        response = self.client.post("/api/automation/run-once", json={"dry_run": True, "run_key": "endpoint-test"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["dry_run"])
        self.assertTrue(payload["human_approval_required"])

    def test_run_once_rejects_non_dry_run(self):
        response = self.client.post("/api/automation/run-once", json={"dry_run": False})
        self.assertEqual(response.status_code, 400)

    def test_no_execution_endpoint_exists(self):
        response = self.client.post("/api/automation/execute", json={})
        self.assertEqual(response.status_code, 404)
