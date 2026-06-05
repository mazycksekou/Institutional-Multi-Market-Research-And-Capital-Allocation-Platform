import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_free_open_exhaustion import build_nhl_free_open_exhaustion_certificate, write_nhl_free_open_exhaustion_certificate


class TestNhlFreeOpenExhaustionCertificate(unittest.TestCase):
    def test_certificate_marks_finality_true_when_counts_close(self):
        audit = {
            "lanes_with_vague_status": 0,
            "source_candidate_rows": [{"source_type": "official_public_api", "query_used": "NHL schedule csv github"}],
            "oxylabs_total_calls_attempted": 5,
            "oxylabs_total_calls_successful": 5,
            "oxylabs_total_calls_failed": 0,
            "sources_accepted_count": 4,
            "sources_rejected_count": 1,
            "lanes_improved_by_oxylabs": 2,
            "lanes_confirmed_paid_required": 1,
            "lanes_confirmed_manual_import_required": 1,
            "lanes_confirmed_policy_blocked": 1,
            "lanes_tested_count": 5,
        }
        backfill = {"loader_ready_lanes_before": 2, "loader_ready_lanes_backfilled": 2, "loader_ready_lanes_hard_blocked": 0}
        report = build_nhl_free_open_exhaustion_certificate(audit_report=audit, backfill_report=backfill)
        self.assertTrue(report["free_open_exhaustion_verified"])
        self.assertTrue(report["no_more_free_open_search_required"])

    def test_writer_creates_files(self):
        report = build_nhl_free_open_exhaustion_certificate(
            audit_report={"lanes_with_vague_status": 0, "source_candidate_rows": [], "lanes_tested_count": 0},
            backfill_report={"loader_ready_lanes_before": 0, "loader_ready_lanes_backfilled": 0, "loader_ready_lanes_hard_blocked": 0},
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_free_open_exhaustion_certificate(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
