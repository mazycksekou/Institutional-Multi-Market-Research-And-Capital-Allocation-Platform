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
        self.assertIn('outcome_records_count', p)
        self.assertFalse(p['auto_execution_enabled'])
        self.assertEqual(p['execution_allowed_count'], 0)
        self.assertNotIn('provider_payload', str(p))

    def test_outcome_endpoints_compact_default(self):
        ingest = self.client.post(
            '/api/automation/outcomes/ingest',
            json={
                'dry_run': True,
                'persist': True,
                'records': [
                    {
                        'provider': 'kalshi_prediction_market',
                        'market_type': 'prediction_market',
                        'contract_id': 'KXTEST',
                        'outcome_status': 'settled',
                        'final_outcome': 'yes',
                        'settled_at': '2026-05-29T00:00:00+00:00',
                        'source': 'test_fixture',
                        'provider_payload': {'raw': 'drop'},
                    }
                ],
            },
        )
        self.assertEqual(ingest.status_code, 200)
        payload = ingest.json()
        self.assertTrue(payload['dry_run'])
        self.assertFalse(payload['provider_write'])
        self.assertFalse(payload['persisted'])
        self.assertEqual(payload['persistence_blocked_reason'], 'dry_run')
        self.assertEqual(payload['records_valid'], 1)
        self.assertNotIn('provider_payload', str(payload))

        rejected = self.client.post(
            '/api/automation/outcomes/ingest',
            json={
                'dry_run': False,
                'persist': True,
                'records': [
                    {
                        'provider': 'kalshi_prediction_market',
                        'market_type': 'prediction_market',
                        'contract_id': 'KXTEST',
                        'outcome_status': 'settled',
                        'final_outcome': 'yes',
                        'settled_at': '2026-05-29T00:00:00+00:00',
                        'source': 'test_fixture',
                    }
                ],
            },
        )
        self.assertEqual(rejected.status_code, 200)
        rejected_payload = rejected.json()
        self.assertFalse(rejected_payload['provider_write'])
        self.assertFalse(rejected_payload['persisted'])
        self.assertEqual(rejected_payload['records_valid'], 0)
        self.assertEqual(rejected_payload['rejected_reason_counts']['non_real_source_not_persistable'], 1)

        listed = self.client.get('/api/automation/outcomes')
        self.assertEqual(listed.status_code, 200)
        listed_payload = listed.json()
        self.assertIn('total_count', listed_payload)
        self.assertIn('records', listed_payload)

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
