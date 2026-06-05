import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfFreeVsPaidSourceLedger(unittest.TestCase):
    def test_ledger_classifies_remaining_lanes(self):
        report = golf_artifacts()["source_ledger"]
        self.assertEqual(report["report_name"], "GOLF_FREE_VS_PAID_SOURCE_LEDGER")
        self.assertEqual(report["free_open_loader_needed_count"], 3)
        self.assertEqual(report["free_open_manual_import_needed_count"], 4)
        self.assertEqual(report["paid_data_subscription_required_count"], 2)
        self.assertGreaterEqual(report["license_terms_unclear_count"], 3)


if __name__ == "__main__":
    unittest.main()
