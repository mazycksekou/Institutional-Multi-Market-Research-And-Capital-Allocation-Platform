import csv
import json
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
        self.assertIn("americanfootball_nfl", coverage["modules_ready_for_real_tier0"])
        self.assertEqual(coverage["real_rows_count"], 1)
        self.assertEqual(coverage["synthetic_rows_count"], 0)
        self.assertEqual(coverage["real_rows_by_source"], {"nflverse_nfl": 1})
        self.assertEqual(coverage["real_rows_by_module"], {"americanfootball_nfl": 1})
        self.assertEqual(coverage["real_rows_by_season"], {"2024": 1})
        self.assertEqual(coverage["target_coverage_strategy"], "all_available_completed_seasons")
        self.assertEqual(coverage["target_source_id"], "nflverse_nfl")
        self.assertEqual(coverage["target_module"], "americanfootball_nfl")
        self.assertEqual(coverage["target_seasons"], ["2024"])
        self.assertEqual(coverage["seasons_validated"], ["2024"])
        self.assertEqual(coverage["seasons_missing_for_target"], [])
        self.assertEqual(coverage["real_rows_by_target_season"], {"2024": 1})
        self.assertEqual(coverage["nflverse_nfl_coverage_percentage"], 100.0)
        self.assertTrue(coverage["synthetic_rows_ignored_for_real_coverage"])
        self.assertEqual(coverage["game_type_present_count"], 0)
        self.assertEqual(coverage["game_type_missing_count"], 1)
        self.assertEqual(coverage["game_type_missing_by_season"], {"2024": 1})
        self.assertEqual(coverage["label_enrichment_status"], "partial_source_label_coverage")
        self.assertIn("compact_game_type_missing", coverage["label_enrichment_blockers"])
        self.assertIn("nflverse_nfl", coverage["sources_with_valid_rows"])
        self.assertEqual(coverage["downloads_attempted"], 0)

    def test_coverage_report_uses_source_availability_for_missing_and_incomplete_seasons(self):
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
            self.assertTrue(report["ok"])
            latest = Path(tmp) / "data_sources" / "open_sports_history" / "validated" / "latest.json"
            payload = json.loads(latest.read_text(encoding="utf-8"))
            payload["source_availability"] = {
                "target_coverage_strategy": "all_available_completed_seasons",
                "earliest_available_season": "2023",
                "latest_available_completed_season": "2024",
                "all_available_completed_seasons": ["2023", "2024"],
                "seasons_available": ["2023", "2024"],
                "incomplete_or_future_seasons": ["2025"],
                "source_completion_status": {
                    "2023": {"status": "complete_final_scores", "rows": 1, "final_score_rows": 1, "missing_score_rows": 0},
                    "2024": {"status": "complete_final_scores", "rows": 1, "final_score_rows": 1, "missing_score_rows": 0},
                    "2025": {"status": "incomplete_or_future", "rows": 1, "final_score_rows": 0, "missing_score_rows": 1},
                },
            }
            latest.write_text(json.dumps(payload), encoding="utf-8")
            coverage = build_open_sports_history_coverage_report(base_data_dir=tmp)

        self.assertEqual(coverage["target_coverage_strategy"], "all_available_completed_seasons")
        self.assertEqual(coverage["earliest_available_season"], "2023")
        self.assertEqual(coverage["latest_available_completed_season"], "2024")
        self.assertEqual(coverage["all_available_completed_seasons"], ["2023", "2024"])
        self.assertEqual(coverage["validated_completed_seasons"], ["2024"])
        self.assertEqual(coverage["missing_completed_seasons"], ["2023"])
        self.assertEqual(coverage["incomplete_or_future_seasons"], ["2025"])
        self.assertEqual(coverage["coverage_percentage"], 50.0)
        self.assertEqual(coverage["source_completion_status"]["2025"]["status"], "incomplete_or_future")

    def test_coverage_report_counts_game_type_missing_by_season(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._nflverse_csv(
                tmp,
                rows=[
                    {
                        "game_id": "nfl-2024-1",
                        "gameday": "2024-09-05",
                        "season": "2024",
                        "week": "1",
                        "game_type": "REG",
                        "home_team": "KC",
                        "away_team": "BAL",
                        "home_score": "27",
                        "away_score": "20",
                    },
                    {
                        "game_id": "nfl-2024-2",
                        "gameday": "2024-09-12",
                        "season": "2024",
                        "week": "2",
                        "game_type": "",
                        "home_team": "MIA",
                        "away_team": "BUF",
                        "home_score": "31",
                        "away_score": "28",
                    },
                ],
            )
            report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            self.assertTrue(report["ok"])
            coverage = build_open_sports_history_coverage_report(base_data_dir=tmp)

        self.assertEqual(coverage["game_type_present_count"], 1)
        self.assertEqual(coverage["game_type_missing_count"], 1)
        self.assertEqual(coverage["game_type_present_by_season"], {"2024": 1})
        self.assertEqual(coverage["game_type_missing_by_season"], {"2024": 1})
        self.assertEqual(coverage["playoff_label_available_by_season"], {"2024": 1})
        self.assertEqual(coverage["super_bowl_label_available_by_season"], {"2024": 1})
        self.assertEqual(coverage["label_enrichment_status"], "partial_source_label_coverage")
        self.assertTrue(coverage["missing_source_label_fields"])
        self.assertIn("source_field_missing", coverage["label_enrichment_blockers"])

    def test_season_backfill_download_uses_source_hard_cap_and_propagates_provider_counts(self):
        fake_import = {
            "status": "preview_ready",
            "blocked_reason": None,
            "data_kind": "real_open_data",
            "is_synthetic": False,
            "source_url_verified": True,
            "selected_source_url_kind": "nflverse_data_release_asset",
            "selected_source_host": "github.com",
            "selected_release_tag": "schedules",
            "selected_asset_name": "games.csv",
            "selected_asset_format": "csv",
            "fallback_used": False,
            "url_resolution_blocker": None,
            "source_verified_at": "2026-06-03T00:00:00Z",
            "records_received": 285,
            "records_valid": 285,
            "records_rejected": 0,
            "downloads_attempted": 1,
            "downloads_succeeded": 1,
            "provider_calls_attempted": 1,
            "provider_calls_succeeded": 1,
            "provider_calls_failed": 0,
            "validated_preview_rows": [
                {
                    "module": "americanfootball_nfl",
                    "source_id": "nflverse_nfl",
                    "event_id": "2024_01_BAL_KC",
                    "data_kind": "real_open_data",
                    "is_synthetic": False,
                    "blocked_reason": "available",
                }
            ],
        }
        with patch("automation_scheduler.open_sports_history_backfill._run_import", return_value=(fake_import, {})) as run_import:
            report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
                allow_download=True,
                persist_preview=True,
                base_data_dir="unused",
            )

        self.assertTrue(report["ok"])
        self.assertEqual(report["records_valid"], 285)
        self.assertEqual(report["downloads_attempted"], 1)
        self.assertEqual(report["downloads_succeeded"], 1)
        self.assertEqual(report["provider_calls_attempted"], 1)
        self.assertEqual(report["provider_calls_succeeded"], 1)
        self.assertEqual(run_import.call_args.kwargs["max_records"], 500)
        self.assertEqual(report["season_results"][0]["valid_real_preview_rows"], 1)

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

    def test_multiseason_backfill_dedupes_existing_season_and_writes_by_season(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nflverse.csv"
            self._write_csv(
                path,
                [
                    {
                        "game_id": "nfl-2024-1",
                        "gameday": "2024-09-05",
                        "season": "2024",
                        "week": "1",
                        "home_team": "KC",
                        "away_team": "BAL",
                        "home_score": "27",
                        "away_score": "20",
                    },
                    {
                        "game_id": "nfl-2023-1",
                        "gameday": "2023-09-07",
                        "season": "2023",
                        "week": "1",
                        "home_team": "DET",
                        "away_team": "KC",
                        "home_score": "21",
                        "away_score": "20",
                    },
                ],
            )
            first = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="bulk_backfill",
                seasons=[2024, 2023],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            second = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="bulk_backfill",
                seasons=[2024, 2023],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            coverage = build_open_sports_history_coverage_report(base_data_dir=tmp)
            by_2024 = Path(tmp) / "data_sources" / "open_sports_history" / "validated" / "by_season" / "americanfootball_nfl" / "2024.json"
            by_2023 = Path(tmp) / "data_sources" / "open_sports_history" / "validated" / "by_season" / "americanfootball_nfl" / "2023.json"
            by_2024_exists = by_2024.exists()
            by_2023_exists = by_2023.exists()

        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertTrue(by_2024_exists)
        self.assertTrue(by_2023_exists)
        self.assertEqual(coverage["real_rows_by_target_season"], {"2023": 1, "2024": 1})
        self.assertEqual(coverage["seasons_validated"], ["2023", "2024"])
        self.assertEqual(coverage["nflverse_nfl_coverage_percentage"], 100.0)
        self.assertEqual(coverage["real_rows_count"], 2)

    def test_failed_season_does_not_corrupt_existing_validated_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._nflverse_csv(tmp)
            ok_report = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
                input_path=path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            blocked = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2023],
                persist_preview=True,
                base_data_dir=tmp,
            )
            coverage = build_open_sports_history_coverage_report(base_data_dir=tmp)

        self.assertTrue(ok_report["ok"])
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["blocked_reason"], "download_not_allowed")
        self.assertEqual(coverage["real_rows_by_target_season"], {"2024": 1})
        self.assertEqual(coverage["seasons_validated"], ["2024"])
        self.assertEqual(coverage["records_valid"], 1)

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

    def test_synthetic_import_rows_do_not_count_toward_real_coverage_or_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            imports_path = Path(tmp) / "data_sources" / "open_sports_history" / "imports" / "nflverse_nfl" / "sample.csv"
            self._nflverse_csv(imports_path.parent, rows=[
                {
                    "game_id": "nfl-synthetic-1",
                    "gameday": "2024-09-05",
                    "season": "2024",
                    "week": "1",
                    "home_team": "KC",
                    "away_team": "BAL",
                    "home_score": "27",
                    "away_score": "20",
                }
            ]).replace(imports_path)
            season = build_open_sports_history_backfill_report(
                source_id="nflverse_nfl",
                mode="season_backfill",
                seasons=[2024],
                input_path=imports_path,
                persist_preview=True,
                base_data_dir=tmp,
            )
            self.assertTrue(season["ok"])
            coverage = build_open_sports_history_backfill_report(mode="coverage_report", base_data_dir=tmp)

        self.assertEqual(coverage["total_rows"], 1)
        self.assertEqual(coverage["real_rows_count"], 0)
        self.assertEqual(coverage["synthetic_rows_count"], 1)
        self.assertEqual(coverage["real_rows_by_source"], {})
        self.assertNotIn("americanfootball_nfl", coverage["modules_ready_for_tier0"])
        self.assertNotIn("americanfootball_nfl", coverage["modules_ready_for_real_tier0"])
        self.assertTrue(coverage["synthetic_rows_ignored_for_real_coverage"])
        self.assertEqual(coverage["seasons_validated"], [])
        self.assertEqual(coverage["nflverse_nfl_coverage_percentage"], 0.0)

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

    def test_downloaded_dataset_file_patterns_are_gitignored(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/", gitignore)
        self.assertIn("*.csv", gitignore)

    def test_coverage_report_exposes_no_raw_download_url_payloads(self):
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
            self.assertTrue(report["ok"])
            coverage = build_open_sports_history_coverage_report(base_data_dir=tmp)

        rendered = str(coverage).lower()
        self.assertNotIn("browser_download_url", rendered)
        self.assertNotIn("api.github.com/repos", rendered)
        self.assertFalse(coverage["raw_payload_included"])
        self.assertFalse(coverage["secrets_included"])


if __name__ == "__main__":
    unittest.main()
