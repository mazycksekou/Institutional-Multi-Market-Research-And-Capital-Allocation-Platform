import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.soccer_loader_ready_backfill import build_soccer_loader_ready_backfill_report, write_soccer_loader_ready_backfill_report


FAKE_LANES = [{"sport": "soccer", "lane_name": "schedule_results", "field_or_feature_group": "fixtures", "candidate_source_name": "football-data.co.uk", "source_url_hash": "hash", "free_or_paid_category": "free_open_populated"}]


class TestSoccerLoaderReadyBackfill(unittest.TestCase):
    def test_backfill_writes_rows(self):
        with patch("automation_scheduler.soccer_loader_ready_backfill.default_soccer_loader_lanes", return_value=FAKE_LANES), patch(
            "automation_scheduler.soccer_loader_ready_backfill.load_soccer_lane_records",
            return_value={"ok": True, "normalized_records": [{"stable_match_key": "x"}], "source_name": "football-data.co.uk", "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
        ):
            report = build_soccer_loader_ready_backfill_report()
        self.assertEqual(report["loader_ready_lanes_backfilled"], 1)
        self.assertGreater(report["records_added_by_soccer"], 0)

    def test_writer_creates_files(self):
        report = {"loader_ready_lanes_before": 1, "loader_ready_lanes_backfilled": 1, "loader_ready_lanes_hard_blocked": 0, "records_added_by_soccer": 1, "oxylabs_total_calls_attempted": 1, "backfill_rows": [{"lane_name": "schedule_results", "backfill_written": True, "normalized_records_added": 1, "hard_block_reason": None}]}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_loader_ready_backfill_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
