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

    def test_run_once_endpoint_dry_run_only(self):
        r = self.client.post('/api/automation/run-once', json={'dry_run': True, 'run_key': 'endpoint-test'})
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertTrue(p['dry_run'])
        self.assertIn('report_path', p)

    def test_run_once_rejects_non_dry_run(self):
        r = self.client.post('/api/automation/run-once', json={'dry_run': False})
        self.assertEqual(r.status_code, 400)
