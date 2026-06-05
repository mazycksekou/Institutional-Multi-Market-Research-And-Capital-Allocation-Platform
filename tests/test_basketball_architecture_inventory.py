import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS, build_basketball_architecture_inventory


class TestBasketballArchitectureInventory(unittest.TestCase):
    def test_inventory_separates_all_basketball_sports(self):
        report = build_basketball_architecture_inventory()
        self.assertTrue(report["ok"])
        self.assertEqual(set(report["by_sport"]), set(SPORTS))
        for sport in SPORTS:
            self.assertGreater(report["by_sport"][sport]["field_count"], 0)

    def test_inventory_rows_have_required_audit_fields(self):
        row = build_basketball_architecture_inventory()["inventory_entries"][0]
        for key in (
            "sport",
            "module",
            "table",
            "field_name",
            "entity_level",
            "current_population_status",
            "current_record_count",
            "current_source",
            "source_family",
            "data_type",
            "coverage_start",
            "coverage_end",
            "cutoff_safe",
            "future_leakage_risk",
            "model_eligible",
            "calibration_impact",
            "missing_reason",
            "candidate_sources_to_fill",
            "duplicate_or_obsolete_candidate",
        ):
            self.assertIn(key, row)


if __name__ == "__main__":
    unittest.main()
