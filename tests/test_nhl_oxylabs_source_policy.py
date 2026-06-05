import unittest

from automation_scheduler.nhl_oxylabs_source_policy import evaluate_nhl_oxylabs_source_policy


class TestNhlOxylabsSourcePolicy(unittest.TestCase):
    def test_official_api_domain_is_allowed(self):
        result = evaluate_nhl_oxylabs_source_policy(
            source_id="nhl_official_api",
            domain="api-web.nhle.com",
            transport="residential_proxy",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["policy_status"], "approved_free_open_transport")

    def test_blocked_reference_domain_is_hard_blocked(self):
        result = evaluate_nhl_oxylabs_source_policy(
            source_id="nhl_official_api",
            domain="hockey-reference.com",
            transport="web_scraper_api",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["oxylabs_transport_used"], "hard_blocked")

    def test_terms_review_source_is_allowed_for_public_page_check(self):
        result = evaluate_nhl_oxylabs_source_policy(
            source_id="nhl_natural_stat_trick_home",
            domain="naturalstattrick.com",
            transport="web_scraper_api",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["policy_status"], "terms_review_required")


if __name__ == "__main__":
    unittest.main()
