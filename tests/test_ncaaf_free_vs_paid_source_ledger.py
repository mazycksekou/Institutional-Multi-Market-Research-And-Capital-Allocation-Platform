import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafFreeVsPaidSourceLedger(unittest.TestCase):
    def test_source_ledger_final_categories(self):
        report = ncaaf_artifacts()["source_ledger"]
        self.assertEqual(report["free_open_loader_needed_count"], 5)
        self.assertEqual(report["paid_data_subscription_required_count"], 2)
        self.assertGreaterEqual(report["free_open_manual_import_needed_count"], 4)

if __name__ == "__main__":
    unittest.main()
