import unittest

from automation_scheduler.combat_free_vs_paid_readiness import combat_lane_catalog
from tests.combat_test_support import combat_artifacts


class TestCombatArchitectureInventory(unittest.TestCase):
    def test_inventory_contains_combat_fields_and_safety_flags(self):
        report = combat_artifacts()["architecture_inventory"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["sport"], "combat")
        self.assertGreater(report["fields_total"], 0)
        self.assertGreater(report["fields_missing_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["paid_source_enabled_count"], 1)
        lane_names = {row["lane_name"] for row in report["inventory_entries"]}
        self.assertEqual(lane_names, {lane["lane_name"] for lane in combat_lane_catalog()})


if __name__ == "__main__":
    unittest.main()
