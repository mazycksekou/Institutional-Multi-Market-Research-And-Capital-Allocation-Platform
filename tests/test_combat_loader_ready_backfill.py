import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatLoaderReadyBackfill(unittest.TestCase):
    def test_backfill_report_tracks_lanes(self):
        report = combat_artifacts()["loader_backfill"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["loader_ready_lanes_before"], report["loader_ready_lanes_backfilled"] + report["loader_ready_lanes_hard_blocked"])
        self.assertGreater(report["records_added_by_combat"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
