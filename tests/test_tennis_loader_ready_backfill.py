import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisLoaderReadyBackfill(unittest.TestCase):
    def test_loader_ready_lanes_are_all_hard_blocked_with_zero_writes(self):
        report = tennis_artifacts()["loader_backfill"]
        self.assertEqual(report["loader_ready_lanes_backfilled"], 0)
        self.assertEqual(report["records_added_by_tennis"], 0)
        self.assertEqual(report["loader_ready_lanes_before"], report["loader_ready_lanes_hard_blocked"])


if __name__ == "__main__":
    unittest.main()
