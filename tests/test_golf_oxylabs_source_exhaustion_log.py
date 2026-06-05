import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfOxylabsSourceExhaustionLog(unittest.TestCase):
    def test_oxylabs_audit_uses_both_mandatory_transports(self):
        report = golf_artifacts()["audit"]
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["lanes_free_open_backfilled"], 3)


if __name__ == "__main__":
    unittest.main()
