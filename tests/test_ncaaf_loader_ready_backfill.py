import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafLoaderReadyBackfill(unittest.TestCase):
    def test_backfill_writes_all_loader_lanes(self):
        report = ncaaf_artifacts()["backfill"]
        self.assertEqual(report["loader_ready_lanes_before"], 5)
        self.assertEqual(report["loader_ready_lanes_backfilled"], 5)
        self.assertEqual(report["records_added_by_ncaaf"], 10)

if __name__ == "__main__":
    unittest.main()
