import tempfile
import unittest
from pathlib import Path

from automation_scheduler.soccer_free_open_exhaustion import build_soccer_free_open_exhaustion_certificate, write_soccer_free_open_exhaustion_certificate


class TestSoccerFreeOpenExhaustionCertificate(unittest.TestCase):
    def test_certificate_declares_verified_when_lanes_and_backfill_align(self):
        report = build_soccer_free_open_exhaustion_certificate(
            audit_report={"source_candidate_rows": [{"source_type": "open_csv_dataset", "domain": "football-data.co.uk", "query_used": "csv query"}], "oxylabs_total_calls_attempted": 2, "oxylabs_total_calls_successful": 2, "oxylabs_total_calls_failed": 0, "sources_accepted_count": 1, "sources_rejected_count": 0, "lanes_improved_by_oxylabs": 1, "lanes_confirmed_paid_required": 1, "lanes_confirmed_manual_import_required": 1, "lanes_confirmed_policy_blocked": 1, "lanes_tested_count": 3, "lanes_with_vague_status": 0},
            backfill_report={"loader_ready_lanes_before": 1, "loader_ready_lanes_backfilled": 1, "loader_ready_lanes_hard_blocked": 0},
        )
        self.assertTrue(report["free_open_exhaustion_verified"])

    def test_writer_creates_files(self):
        report = {"free_open_exhaustion_verified": True, "lanes_with_vague_status": 0, "no_more_free_open_search_required": True}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_free_open_exhaustion_certificate(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
