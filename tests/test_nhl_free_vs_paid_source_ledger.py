import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_free_vs_paid_readiness import (
    build_nhl_free_vs_paid_source_ledger,
    nhl_lane_catalog,
    write_nhl_free_vs_paid_source_ledger,
)


class TestNhlFreeVsPaidSourceLedger(unittest.TestCase):
    def test_ledger_counts_all_lanes_and_loader_ready_rows(self):
        report = build_nhl_free_vs_paid_source_ledger()
        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"]["source_count"], len(nhl_lane_catalog()))
        self.assertGreater(report["summary"]["loader_ready_count"], 0)
        self.assertGreater(report["summary"]["manual_template_count"], 0)

    def test_writer_creates_files(self):
        report = build_nhl_free_vs_paid_source_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_free_vs_paid_source_ledger(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
