import unittest
from automation_scheduler.response_compactor import (
    compact_calibration_collector_response,
    compact_calibration_response,
    compact_deepseek_review_response,
    compact_institutional_execution_response,
    compact_institutional_lab_health_response,
    compact_institutional_lab_run_response,
    compact_institutional_report_response,
    compact_outcome_ingest_response,
    compact_outcomes_response,
    compact_settlement_discovery_response,
    compact_health_response, compact_review_queue_response, compact_run_once_response,
    compact_governance_inventory, compact_governance_report, compact_validation_response,
    compact_provider_health_response, compact_provider_registry_response, compact_provider_status,
    redact_and_limit_payload,
)


class TestResponseCompactor(unittest.TestCase):
    def test_default_compact(self):
        p = {
            "ok": True,
            "review_queue_count": 20,
            "human_approval_required": True,
            "auto_execution_enabled": False,
            "review_queue_storage_backend": "file",
            "review_queue_latest_run_id": "run-1",
            "review_queue_read_ok": True,
        }
        c = compact_health_response(p)
        self.assertIn("counts", c)
        self.assertNotIn("providers", c)
        self.assertEqual(c["review_queue_storage_backend"], "file")
        self.assertEqual(c["review_queue_latest_run_id"], "run-1")
        self.assertTrue(c["review_queue_read_ok"])

    def test_limit_enforced(self):
        p = {"ok": True, "count": 50, "items": [{"recommended_action": "watch_recheck"} for _ in range(50)]}
        c = compact_review_queue_response(p, limit=10)
        self.assertEqual(len(c["items"]), 10)

    def test_review_queue_compact_includes_kalshi_summary_and_review_only_execution_safety(self):
        payload = {
            "ok": True,
            "status": "ok",
            "count": 1,
            "summary": {
                "kalshi_candidate_count": 1,
                "sharp_candidate_count": 0,
                "prediction_market_count": 1,
                "sportsbook_count": 0,
                "review_only_count": 1,
                "execution_allowed_count": 0,
                "low_liquidity_count": 1,
                "missing_liquidity_count": 0,
                "liquidity_tier_counts": {"low_liquidity": 1},
                "high_priority_count": 1,
                "average_review_priority_score": 72.0,
                "flagged_low_liquidity_count": 1,
                "flagged_partial_pricing_count": 1,
                "rejected_count": 3,
                "rejected_reason_counts": {"missing_prices": 3},
                "provider_counts": {"kalshi_prediction_market": 1},
                "total_count": 1,
            },
            "storage_backend": "file",
            "last_updated_at": "2026-05-29T00:00:00+00:00",
            "latest_run_id": "run-1",
            "queue_read_ok": True,
            "queue_read_path": "review_queue/latest.json",
            "items_read_count": 1,
            "items": [
                {
                    "provider_id": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "event_id": "evt",
                    "event_name": "Event",
                    "market_id": "m1",
                    "contract_id": "c1",
                    "ticker": "KX-TICKER",
                    "yes_price": 0.55,
                    "no_price": 0.45,
                    "yes_bid": 0.54,
                    "yes_ask": 0.56,
                    "no_bid": 0.44,
                    "no_ask": 0.46,
                    "implied_probability": 0.55,
                    "partial_pricing": True,
                    "price_source": "partial_bid_ask",
                    "volume": 10,
                    "open_interest": 20,
                    "liquidity_score": 0.1,
                    "liquidity_policy_version": "kalshi_liquidity_policy_v2",
                    "liquidity_source": "volume_open_interest_proxy",
                    "liquidity_tier": "low_liquidity",
                    "liquidity_reason": "below_low_threshold",
                    "spread_score": 98,
                    "pricing_quality_score": 100,
                    "close_time_score": 85,
                    "market_structure_score": 94,
                    "low_liquidity": True,
                    "close_time": "2026-06-01T00:00:00+00:00",
                    "status_reason": "open",
                    "settlement_rule_status": "present",
                    "data_quality_status": "approved",
                    "recommended_action": "watch_recheck",
                    "recommendation_status": "review_only",
                }
            ],
        }
        c = compact_review_queue_response(payload, limit=10)
        self.assertEqual(c["kalshi_candidate_count"], 1)
        self.assertEqual(c["prediction_market_count"], 1)
        self.assertEqual(c["review_only_count"], 1)
        self.assertEqual(c["execution_allowed_count"], 0)
        self.assertEqual(c["low_liquidity_count"], 1)
        self.assertEqual(c["missing_liquidity_count"], 0)
        self.assertEqual(c["liquidity_tier_counts"]["low_liquidity"], 1)
        self.assertEqual(c["high_priority_count"], 1)
        self.assertEqual(c["flagged_low_liquidity_count"], 1)
        self.assertEqual(c["flagged_partial_pricing_count"], 1)
        self.assertEqual(c["rejected_count"], 3)
        self.assertEqual(c["rejected_reason_counts"]["missing_prices"], 3)
        self.assertEqual(c["storage_backend"], "file")
        self.assertEqual(c["latest_run_id"], "run-1")
        self.assertTrue(c["queue_read_ok"])
        self.assertEqual(c["items"][0]["liquidity_policy_version"], "kalshi_liquidity_policy_v2")
        self.assertEqual(c["items"][0]["liquidity_tier"], "low_liquidity")
        self.assertEqual(c["items"][0]["recommendation_status"], "review_only")
        self.assertFalse(c["items"][0]["execution_allowed"])

    def test_run_once_summary_only(self):
        p = {
            "ok": True,
            "status": "dry_run_complete",
            "run_id": "r1",
            "report_path": "data/reports/r1.json",
            "records_received": 10,
            "kalshi_price_field_telemetry": {
                "total_kalshi_records_seen": 2,
                "records_with_any_price_signal": 1,
                "first_record_safe_field_names": ["yes_price", "ticker"],
            },
            "review_queue_items_written": 2,
            "review_queue_storage_backend": "file",
            "review_queue_write_path": "review_queue/latest.json",
            "review_queue_latest_run_id": "run-2",
            "kalshi_liquidity_tier_counts": {"low_liquidity": 1},
            "kalshi_missing_liquidity_count": 0,
            "kalshi_high_priority_count": 1,
            "kalshi_average_review_priority_score": 72.0,
            "paper_decisions_written": 2,
            "paper_decisions_count": 2,
            "paper_ledger_storage_backend": "file",
            "paper_ledger_write_path": "paper_ledger/latest.json",
            "paper_ledger_latest_run_id": "run-2",
            "calibration": {"status": "insufficient_data", "settled_count": 0, "coverage_rate": 0.0},
            "provider_payload": {"raw": "should_not_show"},
        }
        c = compact_run_once_response(p)
        self.assertIn("report_path", c)
        self.assertIn("records_received", c)
        self.assertTrue(c["dry_run"])
        self.assertEqual(c["kalshi_price_field_telemetry"]["total_kalshi_records_seen"], 2)
        self.assertEqual(c["review_queue_items_written"], 2)
        self.assertEqual(c["review_queue_storage_backend"], "file")
        self.assertEqual(c["paper_decisions_written"], 2)
        self.assertEqual(c["paper_ledger_storage_backend"], "file")
        self.assertEqual(c["calibration_status"], "insufficient_data")
        self.assertEqual(c["kalshi_liquidity_tier_counts"]["low_liquidity"], 1)
        self.assertEqual(c["kalshi_high_priority_count"], 1)
        self.assertNotIn("provider_payload", str(c))

    def test_calibration_compact_response_is_bounded_and_safe(self):
        compact = compact_calibration_response(
            {
                "ok": True,
                "status": "insufficient_data",
                "dry_run": True,
                "human_approval_required": True,
                "auto_execution_enabled": False,
                "review_items_count": 2,
                "paper_decisions_count": 2,
                "outcome_records_count": 1,
                "matched_outcomes_count": 1,
                "unmatched_outcomes_count": 0,
                "unmatched_reason_counts": {"provider_ticker_contract_not_found": 1},
                "ambiguous_matches_count": 0,
                "settled_count": 0,
                "pending_count": 2,
                "void_count": 0,
                "coverage_rate": 0.0,
                "provider_counts": {"kalshi_prediction_market": 1, "sharp_sportsbook": 1},
                "market_type_counts": {"prediction_market": 1},
                "liquidity_tier_counts": {"low_liquidity": 1},
                "score_bucket_counts": {"60-80": 1},
                "score_field_presence_counts": {"review_priority_score": 1},
                "settlement_field_presence_counts": {"final_outcome": 0},
                "metrics": {},
                "next_required_data": ["settlement_results"],
                "provider_payload": {"raw": "drop"},
                "api_secret": "secret",
            }
        )
        self.assertEqual(compact["status"], "insufficient_data")
        self.assertEqual(compact["paper_decisions_count"], 2)
        self.assertEqual(compact["outcome_records_count"], 1)
        self.assertEqual(compact["matched_outcomes_count"], 1)
        self.assertEqual(compact["unmatched_reason_counts"]["provider_ticker_contract_not_found"], 1)
        self.assertEqual(compact["execution_allowed_count"], 0)
        self.assertTrue(compact["compact_response"])
        rendered = str(compact)
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("secret", rendered)

    def test_outcome_ingest_and_list_compact_responses_are_safe(self):
        ingest = compact_outcome_ingest_response(
            {
                "ok": True,
                "status": "outcomes_validated",
                "dry_run": True,
                "local_persistence": False,
                "persistence_requested": True,
                "persistence_blocked_reason": "dry_run",
                "provider_write": False,
                "records_received": 1,
                "records_valid": 1,
                "records_rejected": 0,
                "duplicate_count": 0,
                "outcome_records_written": 0,
                "api_key": "secret",
            }
        )
        self.assertTrue(ingest["dry_run"])
        self.assertFalse(ingest["provider_write"])
        self.assertFalse(ingest["auto_execution_enabled"])
        self.assertTrue(ingest["persistence_requested"])
        self.assertEqual(ingest["persistence_blocked_reason"], "dry_run")
        self.assertNotIn("secret", str(ingest))

        listed = compact_outcomes_response(
            {
                "ok": True,
                "summary": {
                    "total_count": 1,
                    "provider_counts": {"kalshi_prediction_market": 1},
                    "outcome_status_counts": {"settled": 1},
                    "final_outcome_counts": {"yes": 1},
                },
                "records": [
                    {
                        "outcome_id": "o1",
                        "provider": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KX",
                        "outcome_status": "settled",
                        "final_outcome": "yes",
                        "provider_payload": {"raw": "drop"},
                    }
                ],
            }
        )
        self.assertEqual(listed["total_count"], 1)
        self.assertEqual(listed["records"][0]["outcome_id"], "o1")
        self.assertNotIn("provider_payload", str(listed))

    def test_settlement_discovery_compact_response_is_safe(self):
        compact = compact_settlement_discovery_response(
            {
                "ok": True,
                "status": "completion_candidates_ready",
                "pending_diagnostics": {
                    "pending_rows_count": 1,
                    "completed_rows_count": 0,
                    "rows_with_contract_id": 1,
                    "rows_missing_final_outcome": 1,
                },
                "kalshi_discovery": {
                    "pending_kalshi_rows": 1,
                    "read_only_records_checked": 1,
                    "settled_yes_count": 1,
                    "settlement_field_presence_counts": {"settlement_result": 1},
                    "rejected_reason_counts": {},
                    "provider_payload": {"raw": "drop"},
                },
                "imported_file": {"rows_found": 0, "valid_rows": 0, "rejected_rows": 0},
                "completion_candidates_count": 1,
                "completion_candidates": [
                    {
                        "provider": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KX",
                        "outcome_status": "settled",
                        "final_outcome": "yes",
                        "settled_at": "2026-05-29T00:00:00+00:00",
                        "source": "read_only_settlement",
                        "evidence_type": "explicit_settlement_field",
                        "api_key": "secret",
                    }
                ],
            }
        )
        self.assertEqual(compact["completion_candidates_count"], 1)
        self.assertEqual(compact["settled_yes_count"], 1)
        self.assertFalse(compact["provider_write"])
        self.assertNotIn("provider_payload", str(compact))
        self.assertNotIn("secret", str(compact))

    def test_calibration_collector_compact_response_is_safe(self):
        compact = compact_calibration_collector_response(
            {
                "ok": True,
                "status": "collector_cycle_complete",
                "cycle_id": "cycle-1",
                "dry_run": False,
                "persist_outcomes": True,
                "markets_scanned": 10,
                "eligible_contracts_found": 3,
                "selected_short_term": 2,
                "selected_medium_term": 1,
                "selected_long_term": 0,
                "new_contracts_added": 3,
                "records_checked": 1,
                "explicit_settlement_count": 1,
                "settled_yes_count": 1,
                "outcomes_persisted": 1,
                "total_outcome_records_count": 7,
                "matched_outcomes_count": 7,
                "calibration_status": "partial_calibration",
                "coverage_rate": 0.7,
                "insufficient_sample": True,
                "next_required_data": ["additional_settlement_results"],
                "provider_write": True,
                "execution_allowed_count": 99,
                "auto_execution_enabled": True,
                "kalshi_order_execution_enabled": True,
                "selected_contracts": [{"ticker": "KX", "source_payload": {"raw": "drop"}, "api_key": "secret"}],
            }
        )
        self.assertFalse(compact["provider_write"])
        self.assertEqual(compact["execution_allowed_count"], 0)
        self.assertFalse(compact["auto_execution_enabled"])
        self.assertFalse(compact["kalshi_order_execution_enabled"])
        self.assertEqual(compact["explicit_settlement_count"], 1)
        rendered = str(compact)
        self.assertNotIn("source_payload", rendered)
        self.assertNotIn("secret", rendered)

    def test_deepseek_review_compact_response_is_safe(self):
        compact = compact_deepseek_review_response(
            {
                "ok": True,
                "status": "review_complete",
                "enabled": True,
                "local_server_reachable": True,
                "json_schema_valid": True,
                "provider_write": True,
                "auto_execution_enabled": True,
                "kalshi_order_execution_enabled": True,
                "review": {
                    "summary": "ok",
                    "crosscheck_status": "pass",
                    "risk_flags": [],
                    "valuation_mismatches": [],
                    "missing_inputs": [],
                    "data_quality_notes": [],
                    "recommended_action": "continue_collecting",
                    "confidence": 0.4,
                    "must_not_execute": False,
                    "api_key": "secret",
                },
                "raw_payload": {"x": 1},
            }
        )
        self.assertFalse(compact["provider_write"])
        self.assertFalse(compact["auto_execution_enabled"])
        self.assertFalse(compact["kalshi_order_execution_enabled"])
        self.assertEqual(compact["reviewer_side_effects"], "none")
        self.assertTrue(compact["review"]["must_not_execute"])
        self.assertFalse(compact["raw_payload_included"])
        self.assertNotIn("secret", str(compact))
        self.assertNotIn("'raw_payload':", str(compact))

    def test_institutional_lab_compactors_force_execution_safety(self):
        health = compact_institutional_lab_health_response({"ok": True, "provider_write": True, "execution_allowed": True})
        self.assertFalse(health["provider_write"])
        self.assertFalse(health["execution_allowed"])
        self.assertFalse(health["live_execution_enabled"])

        run = compact_institutional_lab_run_response(
            {
                "ok": True,
                "status": "completed",
                "run_id": "run-1",
                "records_read": 1,
                "records_normalized": 1,
                "calibration": {"status": "insufficient_data", "next_required_data": ["x"]},
                "execution_simulation": {"execution_desk_status": "simulation_only", "simulated_ticket_created": True},
                "records": [{"sidecar_id": "s1", "provider_payload": {"raw": "drop"}, "execution_allowed": True}],
                "provider_write": True,
            }
        )
        self.assertFalse(run["provider_write"])
        self.assertFalse(run["execution_allowed"])
        self.assertFalse(run["live_execution_enabled"])
        self.assertEqual(run["actual_orders_submitted"], 0)
        self.assertNotIn("provider_payload", str(run))

        execution = compact_institutional_execution_response(
            {
                "ok": True,
                "status": "simulated",
                "actual_order_submitted": True,
                "actual_bet_submitted": True,
                "provider_write": True,
                "execution_allowed": True,
            }
        )
        self.assertFalse(execution["actual_order_submitted"])
        self.assertFalse(execution["actual_bet_submitted"])
        self.assertFalse(execution["provider_write"])
        self.assertFalse(execution["execution_allowed"])

        report = compact_institutional_report_response(
            {"ok": True, "actual_orders_submitted": 9, "provider_write": True, "execution_allowed": True}
        )
        self.assertEqual(report["actual_orders_submitted"], 0)
        self.assertFalse(report["provider_write"])

    def test_verbose_redaction(self):
        payload = {"api_key": "x", "nested": [{"token": "y"}], "items": list(range(200)), "provider_payload": {"raw": 1}}
        c = redact_and_limit_payload(payload, limit=25, verbose=True)
        self.assertEqual(c["api_key"], "[redacted]")
        self.assertEqual(c["provider_payload"], "[omitted]")
        self.assertEqual(len(c["items"]), 25)

    def test_inventory_not_full_by_default(self):
        p = {"ok": True, "inventory": [{"model_id": str(i)} for i in range(20)]}
        c = compact_governance_inventory(p, limit=10)
        self.assertEqual(len(c["items"]), 10)

    def test_report_and_validation_compact(self):
        r = compact_governance_report({"ok": True, "blocked_model_count": 2, "eligible_model_count": 3})
        self.assertIn("counts", r)
        v = compact_validation_response({"ok": True, "dry_run": True, "validation": {"blocked_reasons": ["x"]}})
        self.assertIn("decision", v)

    def test_provider_compact_hides_raw_payloads(self):
        payload = {
            "ok": True,
            "provider_count": 1,
            "providers": [
                {
                    "provider_id": "p1",
                    "provider_type": "sportsbook_odds",
                    "enabled": False,
                    "dry_run": True,
                    "live_calls_enabled": False,
                    "raw_payload": {"x": 1},
                }
            ],
        }
        c = compact_provider_registry_response(payload)
        self.assertIn("top_provider_statuses", c)
        self.assertNotIn("raw_payload", str(c))
        h = compact_provider_health_response({"ok": True, "provider_count": 1, "top_provider_statuses": payload["providers"]})
        self.assertIn("provider_count", h)

    def test_provider_status_includes_provider_enabled_and_redacts(self):
        compact = compact_provider_status(
            {
                "ok": True,
                "status": "read_only_ready",
                "provider_id": "sharp_sportsbook",
                "provider_enabled": True,
                "live_calls_enabled": True,
                "credential_status": "ok",
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "rejection_reason_counts": {"missing_event_id": 1},
                "blockers": [],
                "api_key": "secret-value",
            }
        )
        self.assertTrue(compact["provider_enabled"])
        self.assertTrue(compact["live_calls_enabled"])
        self.assertEqual(compact["rejection_reason_counts"]["missing_event_id"], 1)
        self.assertNotIn("secret-value", str(compact))

    def test_provider_status_diagnostic_is_compact(self):
        compact = compact_provider_status(
            {
                "ok": True,
                "status": "provider_error",
                "provider_id": "sharp_sportsbook",
                "provider_enabled": True,
                "live_calls_enabled": True,
                "credential_status": "ok",
                "http_status": 404,
                "diagnostic": {
                    "url_host": "api.sharp.app",
                    "url_path": "/v1/odds",
                    "method": "GET",
                    "secret_redacted": True,
                    "raw_body": {"detail": "nope"},
                    "authorization": "Bearer abc",
                },
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "blockers": ["http_404"],
            }
        )
        self.assertEqual(compact["http_status"], 404)
        self.assertEqual(compact["diagnostic"]["url_host"], "api.sharp.app")
        self.assertEqual(compact["diagnostic"]["url_path"], "/v1/odds")
        self.assertEqual(compact["diagnostic"]["method"], "GET")
        self.assertTrue(compact["diagnostic"]["secret_redacted"])
        self.assertNotIn("raw_body", str(compact))
        self.assertNotIn("authorization", str(compact).lower())

    def test_kalshi_provider_status_compact_shape(self):
        compact = compact_provider_status(
            {
                "ok": True,
                "status": "provider_disabled",
                "provider_id": "kalshi_prediction_market",
                "provider_enabled": False,
                "live_calls_enabled": False,
                "dry_run": True,
                "credential_status": "missing_credentials",
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "rejection_reason_counts": {},
                "blockers": ["provider_disabled"],
                "provider_payload": {"api_key": "secret-value"},
            }
        )
        self.assertEqual(compact["provider_id"], "kalshi_prediction_market")
        self.assertNotIn("provider_payload", str(compact))
        self.assertNotIn("secret-value", str(compact))

    def test_kalshi_diagnostic_fields_are_compact_and_bounded(self):
        compact = compact_provider_status(
            {
                "ok": True,
                "status": "provider_error",
                "provider_id": "kalshi_prediction_market",
                "provider_enabled": True,
                "live_calls_enabled": True,
                "credential_status": "ok",
                "http_status": None,
                "diagnostic": {
                    "url_host": "external-api.kalshi.com",
                    "url_path": "/trade-api/v2/markets",
                    "method": "GET",
                    "error_class": "ConnectError",
                    "error_category": "dns_error",
                    "timeout_seconds": 8.0,
                    "retry_count": 0,
                    "secret_redacted": True,
                    "authorization": "Bearer hidden",
                    "raw_body": {"x": 1},
                },
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "blockers": ["dns_error"],
            }
        )
        diag = compact["diagnostic"]
        self.assertEqual(diag["url_host"], "external-api.kalshi.com")
        self.assertEqual(diag["error_category"], "dns_error")
        self.assertEqual(diag["error_class"], "ConnectError")
        self.assertEqual(diag["timeout_seconds"], 8.0)
        self.assertEqual(diag["retry_count"], 0)
        self.assertTrue(diag["secret_redacted"])
        self.assertNotIn("authorization", str(compact).lower())
        self.assertNotIn("raw_body", str(compact))
