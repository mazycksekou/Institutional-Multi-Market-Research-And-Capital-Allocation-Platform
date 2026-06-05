import unittest

from automation_scheduler.tennis_free_vs_paid_readiness import tennis_lane_catalog
from tests.tennis_test_support import tennis_artifacts


class TestTennisFreeVsPaidSourceLedger(unittest.TestCase):
    def test_ledger_matches_lane_catalog_and_categories(self):
        report = tennis_artifacts()["source_ledger"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["source_ledger_row_count"], len(tennis_lane_catalog()))
        categories = {row["free_or_paid_category"] for row in report["source_ledger_rows"]}
        self.assertIn("free_open_loader_needed", categories)
        self.assertIn("free_open_manual_import_needed", categories)
        self.assertIn("paid_data_subscription_required", categories)
        self.assertIn("license_terms_unclear", categories)


if __name__ == "__main__":
    unittest.main()
