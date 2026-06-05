import unittest

from automation_scheduler.soccer_oxylabs_source_policy import evaluate_soccer_oxylabs_source_policy


class TestSoccerOxylabsSourcePolicy(unittest.TestCase):
    def test_allowed_source_passes(self):
        result = evaluate_soccer_oxylabs_source_policy(
            source_id="soccer_football_data_csv",
            domain="football-data.co.uk",
            transport="residential_proxy",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["policy_status"], "approved_free_open_transport")

    def test_blocked_reference_domain_fails(self):
        result = evaluate_soccer_oxylabs_source_policy(
            source_id="soccer_fbref_blocked",
            domain="fbref.com",
            transport="web_scraper_api",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["blocked_reason"], "domain_blocklisted")


if __name__ == "__main__":
    unittest.main()
