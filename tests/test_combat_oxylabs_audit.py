import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatOxylabsAudit(unittest.TestCase):
    def test_audit_has_oxylabs_usage_and_only_final_states(self):
        report = combat_artifacts()["audit_report"]
        self.assertTrue(report["ok"])
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertGreater(report["oxylabs_total_calls_attempted"], 0)
        self.assertGreater(report["lanes_tested_count"], 0)
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["secrets_included"])


if __name__ == "__main__":
    unittest.main()
