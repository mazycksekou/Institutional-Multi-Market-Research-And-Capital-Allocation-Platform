import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatOxylabsReclassification(unittest.TestCase):
    def test_reclassification_report_exists(self):
        report = combat_artifacts()["reclassification_report"]
        self.assertTrue(report["ok"])
        self.assertGreater(report["reclassification_row_count"], 0)
        self.assertTrue(all(row["exact_reason"] for row in report["reclassification_rows"]))


if __name__ == "__main__":
    unittest.main()
