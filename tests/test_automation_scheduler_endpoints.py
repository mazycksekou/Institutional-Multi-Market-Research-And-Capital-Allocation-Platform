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
        self.assertEqual(p["storage"]["env_var"], "AUTOMATION_DATA_DIR")
        self.assertEqual(p["storage"]["backend"], "file")
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
        self.assertEqual(p["storage"]["env_var"], "AUTOMATION_DATA_DIR")
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
        self.assertEqual(listed_payload["storage"]["env_var"], "AUTOMATION_DATA_DIR")

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
                "daily_new_contract_target": 250,
                "daily_new_contract_hard_cap": 500,
                "daily_remaining_capacity": 247,
                "records_checked": 0,
                "records_rechecked_today": 0,
                "explicit_settlement_count": 0,
                "total_outcome_records_count": 0,
                "matched_outcomes_count": 0,
                "calibration_status": "insufficient_data",
                "coverage_rate": 0.0,
                "insufficient_sample": True,
                "next_required_data": ["additional_settlement_results"],
                "provider_payload": {"raw": "drop"},
                "selected_contracts": [{"ticker": "KX", "source_payload": {"raw": "drop"}}],
                "storage_health": {"env_var": "AUTOMATION_DATA_DIR", "data_dir": "/var/data", "backend": "file", "configured": True, "read_ok": True, "write_ok": True},
            },
        ):
            r = self.client.post(
                "/api/automation/calibration-collector/run",
                json={"dry_run": True, "persist_outcomes": False, "max_new_contracts": 3},
            )
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["markets_scanned"], 10)
        self.assertEqual(payload["daily_new_contract_target"], 250)
        self.assertEqual(payload["daily_new_contract_hard_cap"], 500)
        self.assertFalse(payload["provider_write"])
        self.assertEqual(payload["execution_allowed_count"], 0)
        self.assertFalse(payload["auto_execution_enabled"])
        self.assertFalse(payload["kalshi_order_execution_enabled"])
        self.assertEqual(payload["storage"]["env_var"], "AUTOMATION_DATA_DIR")
        self.assertNotIn("provider_payload", str(payload))
        self.assertNotIn("source_payload", str(payload))

    def test_calibration_collector_endpoint_accepts_adaptive_throughput_request(self):
        with patch(
            "automation_scheduler.run_automation_calibration_collector",
            return_value={
                "ok": True,
                "status": "collector_cycle_complete",
                "dry_run": True,
                "markets_scanned": 25000,
                "daily_new_contract_target": 250,
                "daily_new_contract_hard_cap": 500,
                "new_contracts_selected": 50,
                "provider_write": False,
                "execution_allowed_count": 0,
            },
        ) as mocked:
            r = self.client.post(
                "/api/automation/calibration-collector/run",
                json={
                    "dry_run": True,
                    "persist_outcomes": False,
                    "max_new_contracts": 50,
                    "target_daily_new_contracts": 250,
                    "hard_cap_daily_new_contracts": 500,
                    "max_markets_scanned": 25000,
                    "adaptive_throttle": True,
                },
            )
        self.assertEqual(r.status_code, 200)
        kwargs = mocked.call_args.kwargs
        self.assertEqual(kwargs["max_new_contracts"], 50)
        self.assertEqual(kwargs["target_daily_new_contracts"], 250)
        self.assertEqual(kwargs["hard_cap_daily_new_contracts"], 500)
        self.assertEqual(kwargs["max_markets_scanned"], 25000)
        self.assertTrue(kwargs["adaptive_throttle"])

    def test_calibration_collector_endpoint_rejects_unsafe_cap(self):
        with patch(
            "automation_scheduler.run_automation_calibration_collector",
            return_value={
                "ok": False,
                "status": "invalid_request",
                "errors": ["hard_cap_daily_new_contracts_exceeds_configured_cap"],
                "provider_write": False,
                "execution_allowed_count": 0,
            },
        ):
            r = self.client.post(
                "/api/automation/calibration-collector/run",
                json={"dry_run": True, "hard_cap_daily_new_contracts": 999999},
            )
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()["detail"]["provider_write"])
        self.assertEqual(r.json()["detail"]["execution_allowed_count"], 0)

    def test_calibration_collector_scheduled_endpoint_requires_token(self):
        with patch.dict("os.environ", {"COLLECTOR_CRON_TOKEN": "endpoint-secret"}, clear=False):
            r = self.client.post("/api/automation/calibration-collector/scheduled-run", json={})
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("endpoint-secret", r.text)

    def test_calibration_collector_scheduled_endpoint_rejects_unsafe_flags(self):
        with patch.dict("os.environ", {"COLLECTOR_CRON_TOKEN": "endpoint-secret"}, clear=False):
            r = self.client.post(
                "/api/automation/calibration-collector/scheduled-run",
                headers={"X-Collector-Token": "endpoint-secret"},
                json={"provider_write": True, "live_execution_requested": True, "submit_live_order": True},
            )
        self.assertEqual(r.status_code, 400)
        detail = r.json()["detail"]
        self.assertFalse(detail["provider_write"])
        self.assertEqual(detail["execution_allowed_count"], 0)
        self.assertFalse(detail["live_execution_enabled"])
        self.assertNotIn("endpoint-secret", r.text)

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

    def test_deepseek_red_team_endpoint_compact_default(self):
        with patch(
            "automation_scheduler.run_automation_deepseek_red_team",
            return_value={
                "ok": True,
                "status": "red_team_local_only",
                "enabled": False,
                "deepseek_used": False,
                "red_team_only": True,
                "provider_write": False,
                "execution_allowed": False,
                "live_execution_enabled": False,
                "auto_execution": False,
                "human_approval_required": True,
                "owner_approval_required": True,
                "reviews": [
                    {
                        "deepseek_status": "disabled",
                        "candidate_id": "cand-1",
                        "asset_type": "prediction_market",
                        "market_type": "prediction_market",
                        "recommended_action": "NO_REVIEW",
                        "confidence_score": 0,
                        "edge_quality_score": 0,
                        "liquidity_risk_score": 0,
                        "trap_risk_score": 0,
                        "calibration_support_score": 0,
                        "out_of_distribution_risk": 0,
                        "agreement_with_core_model": False,
                        "disagreement_reasons": [],
                        "missing_inputs": [],
                        "review_reasons": ["deepseek_not_used"],
                        "no_bet_reasons": [],
                        "no_trade_reasons": [],
                        "next_data_to_collect": [],
                        "red_team_only": True,
                        "deepseek_used": False,
                        "provider_write": False,
                        "execution_allowed": False,
                        "live_execution_enabled": False,
                        "auto_execution": False,
                        "human_approval_required": True,
                        "owner_approval_required": True,
                    }
                ],
                "review_count": 1,
            },
        ):
            r = self.client.post("/api/automation/deepseek-red-team", json={"candidates": [{"candidate_id": "cand-1"}]})
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["status"], "red_team_local_only")
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["reviews"][0]["execution_allowed"])

    def test_deepseek_disagreements_endpoint_compact_default(self):
        with patch(
            "automation_scheduler.get_deepseek_disagreements",
            return_value={
                "ok": True,
                "status": "ok",
                "schema_version": "automation_scheduler.v1.deepseek_profit_lab.disagreement_queue.v1",
                "count": 1,
                "items": [
                    {
                        "disagreement_id": "d1",
                        "candidate_id": "cand-1",
                        "asset_type": "prediction_market",
                        "market_type": "prediction_market",
                        "provider": "kalshi_prediction_market",
                        "core_model_action": "ACTIVE_REVIEW",
                        "deepseek_action": "NO_BET",
                        "disagreement_type": "action_disagreement",
                        "disagreement_reasons": ["weak calibration"],
                        "created_at": "2026-06-02T00:00:00+00:00",
                        "redacted": True,
                        "provider_write": False,
                        "execution_allowed": False,
                        "live_execution_enabled": False,
                    }
                ],
            },
        ):
            r = self.client.get("/api/automation/deepseek-disagreements")
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["count"], 1)
        self.assertFalse(payload["items"][0]["provider_write"])
        self.assertFalse(payload["items"][0]["execution_allowed"])

    def test_deepseek_daily_report_endpoint_compact_default(self):
        with patch(
            "automation_scheduler.get_deepseek_daily_report",
            return_value={
                "ok": True,
                "status": "disabled",
                "enabled": False,
                "deepseek_used": False,
                "red_team_only": True,
                "provider_write": False,
                "execution_allowed": False,
                "live_execution_enabled": False,
                "auto_execution": False,
                "human_approval_required": True,
                "owner_approval_required": True,
                "report": {
                    "report_id": "r1",
                    "date": "2026-06-02",
                    "strongest_review_candidates": [],
                    "strongest_no_bet_no_trade_traps": [],
                    "calibration_improvements": [],
                    "failing_clusters": [],
                    "missing_data": [],
                    "provider_issues": [],
                    "disagreement_count": 0,
                    "repeated_model_mistakes": [],
                    "recommended_next_data_to_collect": ["outcomes"],
                    "recommended_next_codex_task": "collect outcomes",
                    "safety_status": {"provider_write": False, "execution_allowed": False, "live_execution_enabled": False},
                    "red_team_only": True,
                    "deepseek_used": False,
                    "provider_write": False,
                    "execution_allowed": False,
                    "live_execution_enabled": False,
                    "auto_execution": False,
                    "human_approval_required": True,
                    "owner_approval_required": True,
                },
            },
        ):
            r = self.client.get("/api/automation/deepseek-daily-report")
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertIn("report", payload)
        self.assertFalse(payload["report"]["provider_write"])
        self.assertFalse(payload["report"]["safety_status"]["execution_allowed"])

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

    def test_institutional_lab_health_endpoint_is_safe(self):
        r = self.client.get("/api/automation/institutional-lab/health")
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertTrue(payload["simulation_only"])

    def test_institutional_lab_run_endpoint_compact_default(self):
        with patch(
            "automation_scheduler.run_institutional_lab",
            return_value={
                "ok": True,
                "status": "completed",
                "run_id": "run-1",
                "created_at": "2026-05-30T12:00:00+00:00",
                "lock_acquired": True,
                "records_read": 1,
                "records_normalized": 1,
                "records_with_outcomes": 0,
                "outcome_records_count": 0,
                "matched_outcomes_count": 0,
                "source_counts": {"prediction_market": 1, "stock": 0, "bond": 0, "major_asset": 0, "sportsbook": 0},
                "status_by_asset_class": {"prediction_market": "insufficient_data"},
                "calibration": {"status": "insufficient_data", "next_required_data": ["settlement_results"]},
                "risk_summary": {"risk_records_count": 1},
                "deepseek_review": {"status": "disabled"},
                "execution_simulation": {"execution_desk_status": "simulation_only", "simulated_ticket_created": False},
                "records": [{"sidecar_id": "s1", "asset_class": "prediction_market", "provider": "kalshi_prediction_market"}],
                "provider_payload": {"raw": "drop"},
            },
        ):
            r = self.client.post("/api/automation/institutional-lab/run", json={"dry_run": True})
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["records_normalized"], 1)
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertEqual(payload["actual_orders_submitted"], 0)
        self.assertNotIn("provider_payload", str(payload))

    def test_institutional_lab_rejects_non_dry_run(self):
        r = self.client.post("/api/automation/institutional-lab/run", json={"dry_run": False})
        self.assertEqual(r.status_code, 400)

    def test_institutional_execution_simulation_endpoint_accepts_simulation_only(self):
        with patch(
            "automation_scheduler.simulate_institutional_execution",
            return_value={
                "ok": True,
                "status": "simulated",
                "execution_desk_status": "simulation_only",
                "candidate_id": "candidate-1",
                "asset_class": "prediction_market",
                "provider": "kalshi_prediction_market",
                "pre_trade_checks_passed": False,
                "risk_blocks": ["insufficient_calibration_sample"],
                "simulated_ticket_created": True,
                "actual_order_submitted": False,
                "actual_bet_submitted": False,
                "actual_trade_submitted": False,
                "provider_write": False,
                "execution_allowed": False,
                "live_execution_enabled": False,
            },
        ):
            r = self.client.post(
                "/api/automation/institutional-lab/execution-desk/simulate",
                json={
                    "simulation_only": True,
                    "live_execution_requested": False,
                    "candidate_id": "candidate-1",
                    "asset_class": "prediction_market",
                    "provider": "kalshi_prediction_market",
                    "human_command": "simulate_only",
                    "max_theoretical_risk": 0,
                    "submit_live_order": False,
                },
            )
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["execution_desk_status"], "simulation_only")
        self.assertFalse(payload["actual_order_submitted"])
        self.assertFalse(payload["actual_bet_submitted"])
        self.assertFalse(payload["actual_trade_submitted"])
        self.assertFalse(payload["provider_write"])

    def test_institutional_execution_simulation_rejects_live_flags(self):
        r = self.client.post(
            "/api/automation/institutional-lab/execution-desk/simulate",
            json={"simulation_only": False, "live_execution_requested": True, "submit_live_order": True},
        )
        self.assertEqual(r.status_code, 400)
        detail = r.json()["detail"]
        self.assertFalse(detail["provider_write"])
        self.assertFalse(detail["execution_allowed"])
        self.assertFalse(detail["live_execution_enabled"])
        self.assertFalse(detail["actual_order_submitted"])

    def test_institutional_deepseek_endpoint_disabled_does_not_crash(self):
        with patch(
            "automation_scheduler.run_institutional_deepseek_review",
            return_value={
                "ok": True,
                "status": "disabled",
                "enabled": False,
                "local_server_reachable": False,
                "json_schema_valid": True,
                "reviewer_side_effects": "none",
                "provider_write": False,
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
            },
        ):
            r = self.client.post("/api/automation/institutional-lab/deepseek-review", json={})
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["status"], "disabled")
        self.assertFalse(payload["provider_write"])
        self.assertEqual(payload["reviewer_side_effects"], "none")

    def test_institutional_report_and_audit_endpoints_compact(self):
        with patch("automation_scheduler.get_institutional_lab_report", return_value={"ok": True, "status": "not_run"}):
            report = self.client.get("/api/automation/institutional-lab/report")
        self.assertEqual(report.status_code, 200)
        self.assertFalse(report.json()["provider_write"])
        with patch(
            "automation_scheduler.get_institutional_lab_audit",
            return_value={"ok": True, "status": "ok", "total_count": 1, "count": 1, "items": [{"audit_id": "a1"}]},
        ):
            audit = self.client.get("/api/automation/institutional-lab/audit")
        self.assertEqual(audit.status_code, 200)
        self.assertEqual(audit.json()["count"], 1)
