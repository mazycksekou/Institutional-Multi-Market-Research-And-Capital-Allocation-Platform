import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_matrix_has_vendor_row(self):
        report = tennis_artifacts()["paid_matrix"]
        self.assertEqual(report["paid_required_count"], 1)
        row = report["requirement_rows"][0]
        self.assertEqual(row["recommendation"], "paid_subscription_required")
        self.assertGreater(row["oxylabs_calls_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
