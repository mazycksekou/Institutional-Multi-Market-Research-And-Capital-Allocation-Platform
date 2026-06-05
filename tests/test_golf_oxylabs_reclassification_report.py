import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfOxylabsReclassificationReport(unittest.TestCase):
    def test_reclassification_keeps_paid_manual_policy_lanes_final(self):
        report = golf_artifacts()["reclassification"]
        self.assertGreater(report["reclassification_row_count"], 0)
        self.assertEqual(report["paid_still_required_count"], 2)
        self.assertGreaterEqual(report["manual_import_still_required_count"], 4)


if __name__ == "__main__":
    unittest.main()
