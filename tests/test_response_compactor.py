import unittest
from automation_scheduler.response_compactor import (
    compact_health_response, compact_review_queue_response, compact_run_once_response,
    compact_governance_inventory, compact_governance_report, compact_validation_response,
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

    def test_run_once_summary_only(self):
        p = {"ok": True, "run_id": "r1", "report": {"path": "data/reports/r1.json"}, "review_queue_size": 3}
        c = compact_run_once_response(p)
        self.assertIn("report_path", c)
        self.assertNotIn("report", c)

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
