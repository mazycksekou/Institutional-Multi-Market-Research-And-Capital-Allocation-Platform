import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisOxylabsAudit(unittest.TestCase):
    def test_audit_uses_both_oxylabs_transports_and_has_no_vague_states(self):
        report = tennis_artifacts()["audit_report"]
        self.assertTrue(report["ok"])
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertGreater(report["oxylabs_total_calls_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
