import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_free_vs_paid_readiness import build_nhl_architecture_inventory, write_nhl_architecture_inventory


SAMPLE_RESULTS = {
    "source_result_index": {
        "icehockey_nhl::schedule_results": {"records_tested": 5},
        "icehockey_nhl::power_play_penalty_kill_stats": {"records_tested": 2},
    }
}


class TestNhlArchitectureInventory(unittest.TestCase):
    def test_inventory_tracks_populated_and_partial_fields(self):
        report = build_nhl_architecture_inventory(sample_verification_results=SAMPLE_RESULTS)
        self.assertTrue(report["ok"])
        self.assertGreater(report["fields_total"], 0)
        self.assertGreater(report["fields_populated_count"], 0)
        self.assertGreater(report["fields_partial_count"], 0)

    def test_writer_creates_files(self):
        report = build_nhl_architecture_inventory(sample_verification_results=SAMPLE_RESULTS)
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_architecture_inventory(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
