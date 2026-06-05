import unittest

from automation_scheduler.tennis_free_vs_paid_readiness import tennis_lane_catalog
from tests.tennis_test_support import tennis_artifacts


class TestTennisArchitectureInventory(unittest.TestCase):
    def test_inventory_contains_tennis_fields_and_safety_flags(self):
        report = tennis_artifacts()["architecture_inventory"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["sport"], "tennis")
        self.assertGreater(report["fields_total"], 0)
        self.assertEqual(report["provider_write"], False)
        self.assertEqual(report["execution_allowed"], False)
        self.assertEqual(report["paid_source_enabled_count"], 1)
        lane_names = {row["lane_name"] for row in report["inventory_entries"]}
        self.assertEqual(lane_names, {lane["lane_name"] for lane in tennis_lane_catalog()})


if __name__ == "__main__":
    unittest.main()
