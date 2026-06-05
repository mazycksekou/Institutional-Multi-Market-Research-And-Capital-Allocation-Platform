import unittest

from automation_scheduler.active_source_discovery_policy import build_paid_retrieval_policy_registry, evaluate_active_source_discovery_policy


class TestActiveSourceDiscoveryPolicy(unittest.TestCase):
    def test_blocked_reference_sites_are_rejected(self):
        decision = evaluate_active_source_discovery_policy(
            source_id="blocked_pfr_reference",
            domain="pro-football-reference.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
            source_allowlist=("blocked_pfr_reference",),
            domain_allowlist=("pro-football-reference.com",),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_status, "blocked_reference_site")

    def test_paid_mode_registry_enables_count_one(self):
        registry = build_paid_retrieval_policy_registry(sport="mlb")
        self.assertEqual(registry["paid_source_enabled_count"], 1)
        self.assertTrue(registry["paid_source_records"])

    def test_allowlisted_source_passes(self):
        decision = evaluate_active_source_discovery_policy(
            source_id="official_team_staff_pages",
            domain="nfl.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
            source_allowlist=("official_team_staff_pages",),
            domain_allowlist=("nfl.com", "*.nfl.com"),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.policy_status, "approved_paid_transport")


if __name__ == "__main__":
    unittest.main()

