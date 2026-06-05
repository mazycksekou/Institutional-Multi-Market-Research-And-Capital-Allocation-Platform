import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.nhl_loader_ready_backfill import build_nhl_loader_ready_backfill_report, write_nhl_loader_ready_backfill_report


FAKE_LANES = [
    {"sport": "icehockey_nhl", "lane_name": "schedule_results", "field_or_feature_group": "schedule/results", "candidate_source_name": "NHL public API", "source_url_hash": "hash-a", "free_or_paid_category": "free_open_populated"},
    {"sport": "icehockey_nhl", "lane_name": "rest_travel_features", "field_or_feature_group": "rest/travel", "candidate_source_name": "NHL public API", "source_url_hash": "hash-b", "free_or_paid_category": "free_open_partial"},
]


def _fake_loader(lane, **kwargs):
    if lane["lane_name"] == "rest_travel_features":
        return {"ok": False, "blocked_reason": "no_records_available", "normalized_records": [], "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 1}
    return {"ok": True, "normalized_records": [{"game_id": 1}], "source_name": "NHL public API", "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0}


class TestNhlLoaderReadyBackfill(unittest.TestCase):
    def test_backfill_counts_success_and_hard_block(self):
        with patch("automation_scheduler.nhl_loader_ready_backfill.default_nhl_loader_lanes", return_value=FAKE_LANES), patch(
            "automation_scheduler.nhl_loader_ready_backfill.load_nhl_lane_records",
            side_effect=_fake_loader,
        ):
            report = build_nhl_loader_ready_backfill_report()
        self.assertEqual(report["loader_ready_lanes_before"], 2)
        self.assertEqual(report["loader_ready_lanes_backfilled"], 1)
        self.assertEqual(report["loader_ready_lanes_hard_blocked"], 1)

    def test_writer_creates_files(self):
        report = {
            "loader_ready_lanes_before": 1,
            "loader_ready_lanes_backfilled": 1,
            "loader_ready_lanes_hard_blocked": 0,
            "records_added_by_nhl": 1,
            "oxylabs_total_calls_attempted": 1,
            "backfill_rows": [{"lane_name": "schedule_results", "backfill_written": True, "normalized_records_added": 1, "hard_block_reason": None}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_loader_ready_backfill_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
