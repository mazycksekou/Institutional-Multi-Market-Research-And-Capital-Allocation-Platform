import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafOxylabsAudit(unittest.TestCase):
    def test_audit_uses_both_transports_and_has_no_vague_lanes(self):
        report = ncaaf_artifacts()["audit"]
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["lanes_free_open_backfilled"], 5)

if __name__ == "__main__":
    unittest.main()
