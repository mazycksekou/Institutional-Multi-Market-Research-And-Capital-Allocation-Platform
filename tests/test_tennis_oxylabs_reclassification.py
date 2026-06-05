import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisOxylabsReclassification(unittest.TestCase):
    def test_reclassification_rows_exist_for_manual_paid_and_policy_lanes(self):
        report = tennis_artifacts()["reclassification_report"]
        self.assertGreater(report["reclassification_row_count"], 0)
        self.assertGreaterEqual(report["manual_import_still_required_count"], 1)
        self.assertGreaterEqual(report["paid_still_required_count"], 1)


if __name__ == "__main__":
    unittest.main()
