import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafArchitectureInventory(unittest.TestCase):
    def test_inventory_shape(self):
        report = ncaaf_artifacts()["architecture"]
        self.assertEqual(report["report_name"], "NCAAF_ARCHITECTURE_INVENTORY")
        self.assertIn("FBS", report["subdivisions_included"])
        self.assertGreater(report["fields_total"], 50)
        self.assertFalse(report["provider_write"])

if __name__ == "__main__":
    unittest.main()
