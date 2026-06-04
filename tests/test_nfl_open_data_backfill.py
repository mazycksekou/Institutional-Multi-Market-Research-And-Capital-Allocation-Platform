import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import automation_scheduler.nfl_open_data_backfill as nfl_open_data_backfill
from automation_scheduler.nfl_open_data_backfill import (
    build_nfl_open_data_backfill_report,
    build_nfl_open_data_coverage_matrix,
    write_nfl_open_data_backfill_report,
)
from automation_scheduler.nfl_open_data_sources import BLOCKED_FEATURE_FAMILIES, REQUIRED_DATA_CATEGORIES


class TestNflOpenDataBackfill(unittest.TestCase):
    def test_coverage_matrix_includes_every_source_lane_and_blocked_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_open_data_coverage_matrix(base_data_dir=tmp)
        categories = {row["data_category"] for row in report["coverage_rows"]}
        self.assertTrue(set(REQUIRED_DATA_CATEGORIES).issubset(categories))
        self.assertTrue(set(BLOCKED_FEATURE_FAMILIES).issubset(set(report["feature_families_still_blocked"])))
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])

    def test_coverage_matrix_reflects_validated_latest_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / "nflverse_play_by_play" / "latest.json"
            latest.parent.mkdir(parents=True)
            latest.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "gate": "full_available_backfill",
                        "status": "full_backfill_complete",
                        "records_validated": 10,
                        "records_rejected": 0,
                        "seasons_available": ["2024"],
                        "seasons_backfilled": ["2024"],
                        "fields_available": ["game_id", "play_id", "season", "posteam"],
                    }
                ),
                encoding="utf-8",
            )
            report = build_nfl_open_data_coverage_matrix(base_data_dir=tmp)
            row = {item["source_id"]: item for item in report["coverage_rows"]}["nflverse_play_by_play"]

        self.assertEqual(row["records_validated"], 10)
        self.assertEqual(row["full_backfill_status"], "succeeded")
        self.assertTrue(report["feature_availability"]["play_by_play_available"])
        self.assertNotIn("pace_or_advanced_efficiency", report["feature_families_still_blocked"])

    def test_metadata_only_check_does_not_download(self):
        with patch("automation_scheduler.nfl_open_data_adapters._urlopen_json", return_value={"assets": []}), patch(
            "automation_scheduler.nfl_open_data_adapters.urllib.request.urlopen"
        ) as urlopen:
            report = build_nfl_open_data_backfill_report(
                source_id="nflverse_schedules_results",
                mode="metadata_check",
            )
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 1)
        urlopen.assert_not_called()

    def test_backfill_report_writes_session_and_coverage_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = build_nfl_open_data_backfill_report(mode="metadata_check", source_id="nflverse_coaching_research", base_data_dir=tmp)
            session_paths = write_nfl_open_data_backfill_report(session, base_data_dir=tmp)
            coverage = build_nfl_open_data_backfill_report(mode="coverage_report", base_data_dir=tmp)
            coverage_paths = write_nfl_open_data_backfill_report(coverage, base_data_dir=tmp)

        self.assertIn("data_sources/nfl_open_data/backfill_sessions/latest.json", session_paths["session_latest_json_path"])
        self.assertIn("data_sources/nfl_open_data/coverage_matrix/latest.json", coverage_paths["coverage_latest_json_path"])
        self.assertIn("data_sources/nfl_open_data/coverage_matrix/items/", coverage_paths["coverage_item_json_path"])

    def test_no_outcome_paper_ledger_or_calibration_writes_in_module(self):
        source = inspect.getsource(nfl_open_data_backfill)
        self.assertNotIn("get_paper_ledger_dir", source)
        self.assertNotIn("get_outcomes_dir", source)
        self.assertNotIn("get_calibration_reports_dir", source)
        self.assertNotIn("outcome_store", source)
        self.assertNotIn("paper_ledger", source)
        self.assertNotIn("kalshi calibration", source.lower())


if __name__ == "__main__":
    unittest.main()
