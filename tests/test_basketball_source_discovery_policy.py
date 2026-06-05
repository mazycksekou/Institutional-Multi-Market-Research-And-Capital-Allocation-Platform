import unittest

from automation_scheduler.basketball_source_discovery_policy import evaluate_basketball_source_policy


class TestBasketballSourceDiscoveryPolicy(unittest.TestCase):
    def test_reference_and_restricted_sources_are_blocked(self):
        for name, domain in (
            ("Basketball Reference", "basketball-reference.com"),
            ("KenPom", "kenpom.com"),
            ("Synergy Sports", "synergysports.com"),
        ):
            result = evaluate_basketball_source_policy(name, domain)
            self.assertEqual(result["free_or_paid_category"], "blocked_reference_or_restricted_source")
            self.assertEqual(result["policy_status"], "blocked")

    def test_paid_and_terms_unclear_sources_are_classified(self):
        paid = evaluate_basketball_source_policy("Sportradar Basketball", "developer.sportradar.com", "paid_api")
        unclear = evaluate_basketball_source_policy("nba_api", "github.com", "public_wrapper")
        self.assertEqual(paid["free_or_paid_category"], "paid_data_subscription_required")
        self.assertEqual(unclear["free_or_paid_category"], "license_terms_unclear")


if __name__ == "__main__":
    unittest.main()
