import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_matrix_exists(self):
        report = combat_artifacts()["paid_matrix"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["paid_required_count"], 1)
        self.assertEqual(report["requirement_rows"][0]["recommendation"], "paid_subscription_required")


if __name__ == "__main__":
    unittest.main()
