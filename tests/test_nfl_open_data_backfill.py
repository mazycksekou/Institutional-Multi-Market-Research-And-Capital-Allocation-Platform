import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.providers.nfl_open_data_adapters as nfl_open_data_adapters
import src.providers.nfl_open_data_backfill as nfl_open_data_backfill
from src.providers.nfl_open_data_adapters import _load_resume_ledger, _merge_asset_reports, _merge_validated_report, _save_resume_ledger
from src.providers.nfl_open_data_backfill import build_nfl_open_data_backfill_report, build_nfl_open_data_coverage_matrix, write_nfl_open_data_backfill_report
from src.services.streamlit_dashboard_facade import BLOCKED_FEATURE_FAMILIES, REQUIRED_DATA_CATEGORIES

PARTIAL_LANE_SOURCE_IDS = [
    "nflverse_play_by_play",
    "nflverse_team_stats",
    "nflverse_weekly_player_stats",
    "nflverse_rosters",
    "nflverse_weekly_rosters",
    "nflverse_snap_counts",
    "nflverse_participation",
    "nflverse_depth_charts",
    "nflverse_injuries",
    "nflverse_pace_or_play_volume",
    "nflverse_roster_continuity",
    "nflverse_nextgen_stats",
]


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
        with patch('src.providers.nfl_open_data_adapters._urlopen_json', return_value={"assets": []}), patch(
            'src.providers.nfl_open_data_adapters.urllib.request.urlopen'
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

    def test_partial_lanes_present_in_coverage_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_open_data_coverage_matrix(base_data_dir=tmp)
        source_ids = {row["source_id"] for row in report["coverage_rows"]}
        for lane in PARTIAL_LANE_SOURCE_IDS:
            self.assertIn(lane, source_ids)

    def test_coverage_row_reports_completion_percentage(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / "nflverse_team_stats" / "latest.json"
            latest.parent.mkdir(parents=True)
            latest.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "gate": "full_available_backfill",
                        "seasons_available": ["2023", "2024", "2025"],
                        "seasons_backfilled": ["2024", "2025"],
                        "records_validated": 100,
                        "fields_available": ["season", "week", "team"],
                    }
                ),
                encoding="utf-8",
            )
            report = build_nfl_open_data_coverage_matrix(base_data_dir=tmp)
            row = {item["source_id"]: item for item in report["coverage_rows"]}["nflverse_team_stats"]
        self.assertEqual(row["completion_percentage"], 66.67)

    def test_resume_ledger_dedupes_asset_reports(self):
        merged = _merge_asset_reports(
            [{"asset_name_or_dataset_ref": "a.csv", "season": "2023", "records_validated": 10}],
            [{"asset_name_or_dataset_ref": "a.csv", "season": "2023", "records_validated": 12}, {"asset_name_or_dataset_ref": "b.csv", "season": "2024", "records_validated": 5}],
        )
        self.assertEqual(len(merged), 2)
        by_name = {item["asset_name_or_dataset_ref"]: item for item in merged}
        self.assertEqual(by_name["a.csv"]["records_validated"], 12)

    def test_merge_validated_report_accumulates_season_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            _save_resume_ledger(
                {
                    "schema_version": "nfl_open_data_resume_ledger_v1",
                    "source_id": "nflverse_snap_counts",
                    "seasons_completed": ["2023"],
                    "season_records_validated": {"2023": 1000},
                    "total_records_validated": 1000,
                    "total_records_rejected": 0,
                },
                base_data_dir=tmp,
            )
            merged = _merge_validated_report(
                "nflverse_snap_counts",
                {
                    "ok": True,
                    "gate": "full_available_backfill",
                    "seasons_available": ["2023", "2024"],
                    "seasons_backfilled": ["2024"],
                    "asset_reports": [{"asset_name_or_dataset_ref": "snap_2024.csv", "season": "2024", "status": "ok", "records_validated": 500}],
                    "fields_available": ["season"],
                    "records_rejected": 0,
                },
                base_data_dir=tmp,
            )
            ledger = _load_resume_ledger("nflverse_snap_counts", tmp)
        self.assertEqual(merged["records_validated"], 1500)
        self.assertEqual(set(merged["seasons_backfilled"]), {"2023", "2024"})
        self.assertEqual(ledger["total_records_validated"], 1500)

    def test_feature_availability_flags_include_partial_lane_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_open_data_coverage_matrix(base_data_dir=tmp)
        flags = report["feature_availability"]
        for key in (
            "play_by_play_available",
            "team_stats_available",
            "weekly_player_stats_available",
            "roster_data_available",
            "weekly_rosters_available",
            "snap_counts_available",
            "participation_available",
            "depth_charts_available",
            "injury_data_available",
            "pace_play_volume_available",
            "roster_continuity_available",
            "nextgen_stats_available",
        ):
            self.assertIn(key, flags)

    def test_tiny_sample_requires_allow_download(self):
        report = build_nfl_open_data_backfill_report(
            source_id="nflverse_team_stats",
            mode="tiny_sample",
            allow_download=False,
        )
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertFalse(report["ok"])

    def test_full_backfill_mode_alias(self):
        report = build_nfl_open_data_backfill_report(
            source_id="nflverse_coaching_research",
            mode="full_backfill",
            allow_download=False,
        )
        self.assertEqual(report["mode"], "full_available_backfill")

    def test_adapters_module_has_no_outcome_writes(self):
        source = inspect.getsource(nfl_open_data_adapters)
        self.assertNotIn("outcome_store", source)
        self.assertNotIn("paper_ledger", source)

    def test_generated_nfl_open_data_paths_are_gitignored(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/", gitignore)
        self.assertIn("*.csv", gitignore)


if __name__ == "__main__":
    unittest.main()
