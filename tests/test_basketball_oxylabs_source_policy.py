import unittest

from automation_scheduler.basketball_oxylabs_source_policy import (
    basketball_oxylabs_policy_registry,
    evaluate_basketball_oxylabs_source_policy,
)


class TestBasketballOxylabsSourcePolicy(unittest.TestCase):
    def test_allowed_free_open_source_is_approved(self):
        result = evaluate_basketball_oxylabs_source_policy(
            source_id="basketball_release_assets",
            domain="github.com",
            transport="residential_proxy",
            source_type="open_release_asset",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["policy_status"], "approved_free_open_transport")
        self.assertTrue(result["oxylabs_used"])
        self.assertEqual(result["oxylabs_transport_used"], "residential_proxy")

    def test_blocked_reference_domain_is_hard_blocked(self):
        result = evaluate_basketball_oxylabs_source_policy(
            source_id="basketball_docs_page",
            domain="basketball-reference.com",
            transport="web_scraper_api",
            source_type="reference_site",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["policy_status"], "blocked_reference_site")
        self.assertEqual(result["blocked_reason"], "domain_blocklisted")
        self.assertFalse(result["oxylabs_used"])
        self.assertEqual(result["oxylabs_transport_used"], "hard_blocked")

    def test_policy_registry_exposes_basketball_allowlists(self):
        registry = basketball_oxylabs_policy_registry()
        self.assertTrue(registry["ok"])
        self.assertIn("basketball_release_assets", registry["allowed_source_ids"])
        self.assertIn("github.com", registry["allowed_domains"])
        self.assertIn("basketball_release_assets", registry["source_references"])


if __name__ == "__main__":
    unittest.main()
