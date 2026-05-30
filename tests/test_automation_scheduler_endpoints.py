import unittest
from unittest.mock import patch

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

    def test_settlement_discovery_endpoint_compact_default(self):
        discovered = self.client.post(
            '/api/automation/outcomes/discover-settlements',
            json={
                'dry_run': True,
                'use_kalshi_snapshot': False,
                'pending_rows': [
                    {
                        'provider': 'kalshi_prediction_market',
                        'market_type': 'prediction_market',
                        'contract_id': 'KXTEST',
                    }
                ],
                'imported_rows': [
                    {
                        'provider': 'kalshi_prediction_market',
                        'market_type': 'prediction_market',
                        'contract_id': 'KXIMPORT',
                        'outcome_status': 'settled',
                        'final_outcome': 'yes',
                        'settled_at': '2026-05-29T00:00:00+00:00',
                        'source': 'imported_file',
                        'provider_payload': {'raw': 'drop'},
                    }
                ],
            },
        )
        self.assertEqual(discovered.status_code, 200)
        payload = discovered.json()
        self.assertFalse(payload['provider_write'])
        self.assertFalse(payload['auto_execution_enabled'])
        self.assertEqual(payload['completion_candidates_count'], 1)
        self.assertEqual(payload['import_valid_rows'], 1)
        self.assertNotIn('provider_payload', str(payload))

    def test_settlement_discovery_rejects_non_dry_run(self):
        rejected = self.client.post('/api/automation/outcomes/discover-settlements', json={'dry_run': False})
        self.assertEqual(rejected.status_code, 400)

    def test_run_once_endpoint_dry_run_only(self):
        r = self.client.post('/api/automation/run-once', json={'dry_run': True, 'run_key': 'endpoint-test'})
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertTrue(p['dry_run'])
        self.assertIn('report_path', p)

    def test_run_once_rejects_non_dry_run(self):
        r = self.client.post('/api/automation/run-once', json={'dry_run': False})
        self.assertEqual(r.status_code, 400)

    def test_calibration_collector_endpoint_compact_default(self):
        with patch(
            "automation_scheduler.run_automation_calibration_collector",
            return_value={
                "ok": True,
                "status": "collector_cycle_complete",
                "cycle_id": "cycle-1",
                "dry_run": True,
                "persist_outcomes": False,
                "markets_scanned": 10,
                "eligible_contracts_found": 3,
                "selected_short_term": 2,
                "selected_medium_term": 1,
                "selected_long_term": 0,
                "new_contracts_added": 3,
                "records_checked": 0,
                "explicit_settlement_count": 0,
                "total_outcome_records_count": 0,
                "matched_outcomes_count": 0,
                "calibration_status": "insufficient_data",
                "coverage_rate": 0.0,
                "insufficient_sample": True,
                "next_required_data": ["additional_settlement_results"],
                "provider_payload": {"raw": "drop"},
                "selected_contracts": [{"ticker": "KX", "source_payload": {"raw": "drop"}}],
            },
        ):
            r = self.client.post(
                "/api/automation/calibration-collector/run",
                json={"dry_run": True, "persist_outcomes": False, "max_new_contracts": 3},
            )
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["markets_scanned"], 10)
        self.assertFalse(payload["provider_write"])
        self.assertEqual(payload["execution_allowed_count"], 0)
        self.assertFalse(payload["auto_execution_enabled"])
        self.assertFalse(payload["kalshi_order_execution_enabled"])
        self.assertNotIn("provider_payload", str(payload))
        self.assertNotIn("source_payload", str(payload))

    def test_deepseek_review_endpoint_compact_default(self):
        with patch(
            "automation_scheduler.run_automation_deepseek_review",
            return_value={
                "ok": True,
                "status": "disabled",
                "enabled": False,
                "local_server_reachable": False,
                "json_schema_valid": True,
                "forbidden_actions_rejected": False,
                "reviewer_side_effects": "none",
                "provider_write": False,
                "auto_execution_enabled": False,
                "kalshi_order_execution_enabled": False,
                "review": {
                    "summary": "disabled",
                    "crosscheck_status": "pass",
                    "risk_flags": [],
                    "valuation_mismatches": [],
                    "missing_inputs": [],
                    "data_quality_notes": [],
                    "recommended_action": "continue_collecting",
                    "confidence": 0.0,
                    "must_not_execute": True,
                },
                "raw_payload": {"x": 1},
            },
        ):
            r = self.client.post("/api/automation/deepseek-review", json={})
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["status"], "disabled")
        self.assertFalse(payload["provider_write"])
        self.assertEqual(payload["reviewer_side_effects"], "none")
        self.assertTrue(payload["review"]["must_not_execute"])
        self.assertFalse(payload["raw_payload_included"])
        self.assertNotIn("'raw_payload':", str(payload))

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
