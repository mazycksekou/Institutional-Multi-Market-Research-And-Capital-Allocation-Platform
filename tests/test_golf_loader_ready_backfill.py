import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfLoaderReadyBackfill(unittest.TestCase):
    def test_all_loader_ready_lanes_are_backfilled(self):
        report = golf_artifacts()["backfill"]
        self.assertEqual(report["loader_ready_lanes_before"], 3)
        self.assertEqual(report["loader_ready_lanes_backfilled"], 3)
        self.assertEqual(report["loader_ready_lanes_hard_blocked"], 0)
        self.assertEqual(report["records_added_by_golf"], 9)


if __name__ == "__main__":
    unittest.main()
