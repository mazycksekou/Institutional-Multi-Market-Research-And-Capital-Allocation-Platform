import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafFreeOpenExhaustion(unittest.TestCase):
    def test_finality_report_declares_exhaustion(self):
        report = ncaaf_artifacts()["final_report"]
        self.assertEqual(report["new_overall_verdict"], "NCAAF_FINAL_FREE_OPEN_EXHAUSTED")
        self.assertTrue(report["no_more_free_open_search_required"])
        self.assertTrue(report["free_open_sources_exhausted"])

if __name__ == "__main__":
    unittest.main()
