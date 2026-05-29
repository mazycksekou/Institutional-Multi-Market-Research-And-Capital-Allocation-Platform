import unittest
from fastapi.testclient import TestClient
from main import app


class TestAutomationSchedulerEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_returns_compact_json(self):
        r = self.client.get('/api/automation/health')
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertTrue(p['ok'])
        self.assertIn('counts', p)
        self.assertNotIn('health', p)

    def test_review_queue_endpoint_compact_default(self):
        r = self.client.get('/api/automation/review-queue')
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertIn('items', p)

    def test_calibration_endpoint_compact_default(self):
        r = self.client.get('/api/automation/calibration')
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertIn('status', p)
        self.assertIn('paper_decisions_count', p)
        self.assertFalse(p['auto_execution_enabled'])
        self.assertEqual(p['execution_allowed_count'], 0)
        self.assertNotIn('provider_payload', str(p))

    def test_run_once_endpoint_dry_run_only(self):
        r = self.client.post('/api/automation/run-once', json={'dry_run': True, 'run_key': 'endpoint-test'})
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertTrue(p['dry_run'])
        self.assertIn('report_path', p)

    def test_run_once_rejects_non_dry_run(self):
        r = self.client.post('/api/automation/run-once', json={'dry_run': False})
        self.assertEqual(r.status_code, 400)

    def test_kalshi_provider_endpoints_compact_default(self):
        health = self.client.get('/api/providers/kalshi/health')
        self.assertEqual(health.status_code, 200)
        health_payload = health.json()
        self.assertIn('provider_id', health_payload)
        self.assertEqual(health_payload['provider_id'], 'kalshi_prediction_market')
        self.assertNotIn('records', health_payload)

        snap = self.client.post('/api/providers/kalshi/snapshot')
        self.assertEqual(snap.status_code, 200)
        snap_payload = snap.json()
        self.assertIn('status', snap_payload)
        self.assertIn('blockers', snap_payload)
        self.assertNotIn('api_key', str(snap_payload).lower())
