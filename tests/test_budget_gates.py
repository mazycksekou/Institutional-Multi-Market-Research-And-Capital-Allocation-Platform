import unittest

from src.services.streamlit_dashboard_facade import build_budget_gate
from src.services.streamlit_dashboard_facade import build_registry


class TestBudgetGates(unittest.TestCase):
    def setUp(self):
        self.registry = build_registry()
        self.sources = {source["source_id"]: source for source in self.registry["sources"]}

    def test_paid_sources_require_budget_approval_and_are_not_enabled(self):
        paid = [
            source for source in self.registry["sources"]
            if source["source_access_type"] in {
                "paid_candidate",
                "partner_candidate",
                "institutional_vendor_candidate",
                "broker_data_candidate",
                "sportsbook_account_candidate",
                "internal_proprietary_candidate",
            }
        ]
        self.assertGreater(len(paid), 0)
        for source in paid:
            self.assertTrue(source["requires_budget_approval"])
            self.assertEqual(source["approval_status"], "not_approved")
            self.assertFalse(source["enabled"])
            self.assertFalse(source["paid_upgrade_allowed"])
            self.assertFalse(source["substantial_usage_allowed"])

    def test_limited_call_source_defaults_to_no_call_then_tiny_sample(self):
        cfbd = self.sources["collegefootballdata"]
        self.assertEqual(cfbd["source_access_type"], "free_key")
        self.assertEqual(cfbd["call_budget_level"], "no_call_audit_default_tiny_sample_if_explicit")
        self.assertEqual(cfbd["max_provider_calls_default"], 0)
        self.assertEqual(cfbd["max_provider_calls_hard_cap"], 3)
        self.assertTrue(cfbd["verification_phase_allowed"])
        self.assertFalse(cfbd["enabled"])

    def test_paid_upgrade_and_substantial_usage_are_blocked_by_default(self):
        gate = build_budget_gate(source_access_type="paid_candidate", requires_paid_subscription=True)
        self.assertTrue(gate["requires_budget_approval"])
        self.assertEqual(gate["call_budget_level"], "blocked_pending_budget_approval")
        self.assertEqual(gate["max_provider_calls_default"], 0)
        self.assertEqual(gate["max_provider_calls_hard_cap"], 0)
        self.assertFalse(gate["paid_upgrade_allowed"])
        self.assertFalse(gate["substantial_usage_allowed"])

    def test_no_source_is_enabled_and_safety_flags_hold(self):
        self.assertEqual(self.registry["enabled_source_count"] if "enabled_source_count" in self.registry else 0, 0)
        for source in self.registry["sources"]:
            self.assertFalse(source["enabled"])
            self.assertFalse(source["provider_write"])
            self.assertFalse(source["execution_allowed"])
            self.assertFalse(source["paid_upgrade_allowed"])
            self.assertFalse(source["substantial_usage_allowed"])


if __name__ == "__main__":
    unittest.main()

