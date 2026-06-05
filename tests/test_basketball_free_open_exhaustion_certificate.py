import tempfile
import unittest
from pathlib import Path

from automation_scheduler.basketball_free_open_exhaustion import (
    build_basketball_free_open_exhaustion_certificate,
    write_basketball_free_open_exhaustion_certificate,
)


class TestBasketballFreeOpenExhaustionCertificate(unittest.TestCase):
    def test_certificate_marks_exhaustion_verified(self):
        audit_report = {
            "lanes_with_vague_status": 0,
            "oxylabs_total_calls_attempted": 5,
            "oxylabs_total_calls_successful": 5,
            "oxylabs_total_calls_failed": 0,
            "sources_accepted_count": 4,
            "sources_rejected_count": 1,
            "lanes_improved_by_oxylabs": 2,
            "lanes_confirmed_paid_required": 1,
            "lanes_confirmed_manual_import_required": 1,
            "lanes_confirmed_policy_blocked": 1,
            "lanes_confirmed_terms_unclear": 0,
            "source_candidate_rows": [
                {
                    "sport": "basketball_nba",
                    "lane_name": "schedule_results",
                    "source_type": "open_release_asset",
                    "final_actionable_state": "free_open_backfilled",
                    "accepted_or_rejected": "accepted",
                    "normalized_records_added": 2,
                },
                {
                    "sport": "basketball_wnba",
                    "lane_name": "lineup_on_off",
                    "source_type": "public_docs_page",
                    "final_actionable_state": "manual_import_required",
                    "accepted_or_rejected": "accepted",
                    "normalized_records_added": 0,
                },
            ],
        }
        backfill_report = {"loader_ready_lanes_backfilled": 2, "loader_ready_lanes_hard_blocked": 0}
        report = build_basketball_free_open_exhaustion_certificate(
            audit_report=audit_report,
            backfill_report=backfill_report,
            gap_plan={"ok": True},
            readiness={"ok": True},
            paid_matrix={"ok": True},
        )
        self.assertTrue(report["free_open_exhaustion_verified"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["by_sport"]["basketball_nba"]["lanes_improved"], 1)
        self.assertEqual(report["by_sport"]["basketball_wnba"]["lanes_improved"], 0)

    def test_writer_creates_report_files(self):
        report = build_basketball_free_open_exhaustion_certificate(
            audit_report={"lanes_with_vague_status": 0, "source_candidate_rows": []},
            backfill_report={"loader_ready_lanes_backfilled": 0, "loader_ready_lanes_hard_blocked": 0},
            gap_plan={"ok": True},
            readiness={"ok": True},
            paid_matrix={"ok": True},
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_basketball_free_open_exhaustion_certificate(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
