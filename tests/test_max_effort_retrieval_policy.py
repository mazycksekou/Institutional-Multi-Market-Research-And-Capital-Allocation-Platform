import unittest

from automation_scheduler.max_effort_retrieval_policy import build_max_effort_policy_registry, evaluate_max_effort_retrieval_policy


class TestMaxEffortRetrievalPolicy(unittest.TestCase):
    def test_allows_paid_transport_when_authorized(self):
        decision = evaluate_max_effort_retrieval_policy(
            source_id="example_source",
            domain="example.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["policy_status"], "approved_paid_transport")
        self.assertEqual(decision["paid_source_enabled_count"], 1)

    def test_blocks_when_oxylabs_disabled(self):
        decision = evaluate_max_effort_retrieval_policy(
            source_id="example_source",
            domain="example.com",
            allow_oxylabs=False,
            allow_paid_retrieval=True,
        )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["policy_status"], "blocked_paywall_or_login")
        self.assertEqual(decision["paid_source_enabled_count"], 0)

    def test_build_registry_includes_expected_shape(self):
        registry = build_max_effort_policy_registry(sport="nfl", allow_oxylabs=True, allow_paid_retrieval=True)

        self.assertEqual(registry["sport"], "nfl")
        self.assertEqual(registry["run_mode"], "user_approved_paid_retrieval_mode")
        self.assertIn("paid_source_records", registry)
        self.assertIn("domain_blocklist", registry)
        self.assertIsInstance(registry["domain_blocklist"], list)


if __name__ == "__main__":
    unittest.main()
