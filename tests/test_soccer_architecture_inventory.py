import tempfile
import unittest
from pathlib import Path

from automation_scheduler.soccer_free_vs_paid_readiness import build_soccer_architecture_inventory, soccer_lane_catalog, write_soccer_architecture_inventory


class TestSoccerArchitectureInventory(unittest.TestCase):
    def test_inventory_counts_fields(self):
        report = build_soccer_architecture_inventory()
        self.assertTrue(report["ok"])
        self.assertEqual(report["fields_total"], sum(len(lane["fields"]) for lane in soccer_lane_catalog()))
        self.assertGreater(report["fields_missing_count"], 0)

    def test_writer_creates_files(self):
        report = build_soccer_architecture_inventory()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_architecture_inventory(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
