import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafFinalOxylabsFreeOpenExhaustionReport(unittest.TestCase):
    def test_final_report_contract(self):
        artifacts = ncaaf_artifacts()
        report = artifacts["final_report"]
        self.assertEqual(report["new_overall_verdict"], "NCAAF_FINAL_FREE_OPEN_EXHAUSTED")
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["unsafe_extraction_count"], 0)
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["paid_source_enabled_count"], 1)
        self.assertTrue(artifacts["manual_template_path"].exists())
        self.assertTrue(artifacts["manual_docs_path"].exists())
        self.assertTrue(artifacts["policy_docs_path"].exists())

if __name__ == "__main__":
    unittest.main()
