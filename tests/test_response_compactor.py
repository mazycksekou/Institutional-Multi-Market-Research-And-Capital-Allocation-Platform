import unittest
from automation_scheduler.response_compactor import (
    compact_health_response, compact_review_queue_response, compact_run_once_response,
    compact_governance_inventory, compact_governance_report, compact_validation_response,
    compact_provider_health_response, compact_provider_registry_response, compact_provider_status,
    redact_and_limit_payload,
)


class TestResponseCompactor(unittest.TestCase):
    def test_default_compact(self):
        p = {"ok": True, "review_queue_count": 20, "human_approval_required": True, "auto_execution_enabled": False}
        c = compact_health_response(p)
        self.assertIn("counts", c)
        self.assertNotIn("providers", c)

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
                "prediction_market_count": 1,
                "review_only_count": 1,
                "execution_allowed_count": 0,
                "flagged_low_liquidity_count": 1,
                "rejected_count": 3,
            },
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
                    "volume": 10,
                    "open_interest": 20,
                    "liquidity_score": 0.1,
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
        self.assertEqual(c["flagged_low_liquidity_count"], 1)
        self.assertEqual(c["rejected_count"], 3)
        self.assertEqual(c["items"][0]["recommendation_status"], "review_only")
        self.assertFalse(c["items"][0]["execution_allowed"])

    def test_run_once_summary_only(self):
        p = {"ok": True, "status": "dry_run_complete", "run_id": "r1", "report_path": "data/reports/r1.json", "records_received": 10}
        c = compact_run_once_response(p)
        self.assertIn("report_path", c)
        self.assertIn("records_received", c)
        self.assertTrue(c["dry_run"])

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
