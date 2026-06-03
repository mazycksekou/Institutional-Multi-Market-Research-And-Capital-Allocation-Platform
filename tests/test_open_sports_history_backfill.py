import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.open_sports_history_backfill import (
    build_open_sports_history_backfill_report,
    build_open_sports_history_coverage_report,
    write_open_sports_history_backfill_report,
)


class TestOpenSportsHistoryBackfill(unittest.TestCase):
    def _write_csv(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _retrosheet_csv(self, tmp):
        path = Path(tmp) / "retrosheet.csv"
        self._write_csv(
            path,
            [
                {"game_id": "mlb-2024-1", "date": "2024-04-01", "home_team": "BOS", "away_team": "NYY", "home_runs": "5", "away_runs": "3"}
            ],
        )
        return path

    def _nflverse_csv(self, tmp, rows=None):
        path = Path(tmp) / "nflverse.csv"
        self._write_csv(
            path,
            rows
            or [
                {
                    "game_id": "nfl-2024-1",
                    "gameday": "2024-09-05",
                    "season": "2024",
                    "week": "1",
                    "home_team": "KC",
                    "away_team": "BAL",
                    "home_score": "27",
                    "away_score": "20",
                }
            ],
        )
        return path

    def test_smoke_test_local_file_writes_resumable_session_without_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._retrosheet_csv(tmp)
            report = build_open_sports_history_backfill_report(
                source_id="retrosheet_mlb",
                mode="smoke_test",
                input_path=path,
                max_records=25,
                base_data_dir=tmp,
            )
            paths = write_open_sports_history_backfill_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["session_latest_json_path"])
            latest_exists = latest.exists()

        self.assertTrue(report["ok"])
        self.assertTrue(report["smoke_test_passed"])
        self.assertEqual(report["records_valid"], 1)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertTrue(latest_exists)
        self.assertIn("data_sources/open_sports_history/backfill_sessions/latest.json", paths["session_latest_json_path"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])

    def test_season_backfill_validates_one_season_and_persists_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._nflverse_csv(tmp)
            report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            paths = write_open_sports_history_backfill_report(report, base_data_dir=tmp)
            coverage = build_open_sports_history_coverage_report(base_data_dir=tmp)

        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "season_backfill_complete")
        self.assertEqual(report["records_valid"], 1)
        self.assertEqual(report["completed_seasons"], [2024])
        self.assertIn("data_sources/open_sports_history/backfill_sessions/items/", paths["session_item_json_path"])
        self.assertIn("americanfootball_nfl", coverage["modules_ready_for_tier0"])
        self.assertIn("nflverse_nfl", coverage["sources_with_valid_rows"])
        self.assertEqual(coverage["downloads_attempted"], 0)

    def test_bulk_backfill_requires_smoke_test_or_valid_local_parser_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocked = build_open_sports_history_backfill_report(
                source_id="retrosheet_mlb",
                mode="bulk_backfill",
                seasons=[2024],
                base_data_dir=tmp,
            )
            path = self._retrosheet_csv(tmp)
            allowed = build_open_sports_history_backfill_report(
                source_id="retrosheet_mlb",
                mode="bulk_backfill",
                seasons=[2024],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )

        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["blocked_reason"], "smoke_test_required")
        self.assertTrue(allowed["ok"])
        self.assertEqual(allowed["records_valid"], 1)
        self.assertEqual(allowed["downloads_attempted"], 0)

    def test_bulk_backfill_uses_prior_smoke_session_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._retrosheet_csv(tmp)
            smoke = build_open_sports_history_backfill_report(
                source_id="retrosheet_mlb",
                mode="smoke_test",
                input_path=path,
                base_data_dir=tmp,
            )
            write_open_sports_history_backfill_report(smoke, base_data_dir=tmp)
            bulk = build_open_sports_history_backfill_report(
                source_id="retrosheet_mlb",
                mode="bulk_backfill",
                seasons=[2024],
                input_path=path,
                base_data_dir=tmp,
            )

        self.assertTrue(smoke["smoke_test_passed"])
        self.assertTrue(bulk["ok"])
        self.assertEqual(bulk["blocked_reason"], None)

    def test_scheduled_backfill_writes_resumable_session_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="scheduled_backfill",
                seasons=[2023, 2024],
                base_data_dir=tmp,
            )
            paths = write_open_sports_history_backfill_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["session_latest_json_path"])
            latest_exists = latest.exists()

        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "scheduled_session_ready")
        self.assertEqual(report["pending_seasons"], [2023, 2024])
        self.assertIn("resume scheduled_backfill", report["next_recommended_session"])
        self.assertTrue(latest_exists)

    def test_coverage_report_reads_validated_rows_and_writes_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._retrosheet_csv(tmp)
            season = build_open_sports_history_backfill_report(
                source_id="retrosheet_mlb",
                mode="season_backfill",
                seasons=[2024],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            self.assertTrue(season["ok"])
            coverage = build_open_sports_history_backfill_report(mode="coverage_report", base_data_dir=tmp)
            paths = write_open_sports_history_backfill_report(coverage, base_data_dir=tmp)

        self.assertEqual(coverage["records_valid"], 1)
        self.assertIn("baseball_mlb", coverage["modules_ready_for_tier0"])
        self.assertIn("retrosheet_mlb", coverage["sources_with_valid_rows"])
        self.assertIn("data_sources/open_sports_history/coverage/latest.json", paths["coverage_latest_json_path"])
        self.assertIn("data_sources/open_sports_history/coverage/items/", paths["coverage_item_json_path"])

    def test_no_download_occurs_unless_allow_download_is_true(self):
        with patch("automation_scheduler.open_sports_history_import.urllib.request.urlopen") as urlopen:
            report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["blocked_reason"], "download_not_allowed")
        self.assertEqual(report["downloads_attempted"], 0)
        urlopen.assert_not_called()

    def test_unsupported_paid_and_sports_reference_sources_are_rejected_cleanly(self):
        unsupported = build_open_sports_history_backfill_report(source_id="not_real", mode="smoke_test")
        sports_ref = build_open_sports_history_backfill_report(
            source_id="sports_reference_manual_export",
            mode="smoke_test",
            allow_download=True,
        )
        paid_source = {
            "source_id": "paid_fixture",
            "module": "baseball_mlb",
            "source_name": "Paid Fixture",
            "source_access_type": "paid_candidate",
            "approval_status": "candidate",
            "enabled": False,
            "current_phase_allowed": True,
            "future_paid_candidate": True,
            "requires_budget_approval": True,
        }
        with patch("automation_scheduler.open_sports_history_backfill.source_by_id", return_value=paid_source):
            paid = build_open_sports_history_backfill_report(source_id="paid_fixture", mode="smoke_test")

        self.assertFalse(unsupported["ok"])
        self.assertEqual(unsupported["blocked_reason"], "unsupported_source")
        self.assertFalse(sports_ref["ok"])
        self.assertEqual(sports_ref["blocked_reason"], "sports_reference_scraping_blocked")
        self.assertFalse(paid["ok"])
        self.assertEqual(paid["blocked_reason"], "paid_source_not_approved")

    def test_control_plane_never_enables_sources_or_persists_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._nflverse_csv(tmp)
            report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )

        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertFalse(report["outcome_persistence_attempted"])
        self.assertFalse(report["persisted_outcomes"])


if __name__ == "__main__":
    unittest.main()
