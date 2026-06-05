import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafOxylabsReclassification(unittest.TestCase):
    def test_reclassification_covers_unresolved_lanes(self):
        report = ncaaf_artifacts()["reclassification"]
        self.assertGreater(report["reclassification_row_count"], 0)
        self.assertEqual(report["paid_still_required_count"], 2)
        self.assertGreaterEqual(report["manual_import_still_required_count"], 4)

if __name__ == "__main__":
    unittest.main()
