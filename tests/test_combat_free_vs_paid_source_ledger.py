import unittest

from automation_scheduler.combat_free_vs_paid_readiness import combat_lane_catalog
from tests.combat_test_support import combat_artifacts


class TestCombatFreeVsPaidSourceLedger(unittest.TestCase):
    def test_ledger_matches_lane_catalog_and_has_expected_gap_types(self):
        report = combat_artifacts()["source_ledger"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["source_ledger_row_count"], len(combat_lane_catalog()))
        self.assertGreater(report["free_open_loader_needed_count"], 0)
        self.assertGreater(report["free_open_manual_import_needed_count"], 0)
        self.assertGreater(report["paid_data_subscription_required_count"], 0)
        self.assertGreater(report["license_terms_unclear_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["paid_source_enabled_count"], 1)


if __name__ == "__main__":
    unittest.main()
