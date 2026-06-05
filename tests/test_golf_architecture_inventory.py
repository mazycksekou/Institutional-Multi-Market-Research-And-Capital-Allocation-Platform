import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfArchitectureInventory(unittest.TestCase):
    def test_inventory_covers_golf_lanes(self):
        report = golf_artifacts()["architecture"]
        self.assertEqual(report["report_name"], "GOLF_ARCHITECTURE_INVENTORY")
        self.assertEqual(set(report["tours_included"]), {"PGA Tour", "DP World Tour", "LPGA", "Majors"})
        self.assertGreaterEqual(report["fields_total"], 40)
        self.assertGreater(report["fields_missing_count"], 0)
        self.assertFalse(report["provider_write"])


if __name__ == "__main__":
    unittest.main()
