import csv
import inspect
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import src.automation_scheduler_legacy.open_sports_history_import as open_sports_history_import
from src.services.streamlit_dashboard_facade import HARD_MAX_RECORDS, NFLVERSE_RAW_GAMES_CSV_FALLBACK_URL, build_nflverse_schedule_availability, classify_open_data_source_url, build_open_sports_history_import_report, normalize_open_sports_history_row, resolve_nflverse_schedules_source, validate_nflverse_schedule_columns, write_open_sports_history_import_report


class FakeHttpResponse:
    def __init__(self, text):
        self._body = text.encode("utf-8")

    def read(self, _limit=-1):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class TestOpenSportsHistoryImport(unittest.TestCase):
    def _write_csv(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _row(self, report, index=0):
        return report["preview_rows"][index]

    def test_no_download_occurs_unless_allow_download_is_set(self):
        with patch('src.automation_scheduler_legacy.open_sports_history_import.urllib.request.urlopen') as urlopen:
            report = build_open_sports_history_import_report(source_id="nflverse_nfl", season=2024)
        self.assertEqual(report["blocked_reason"], "download_not_allowed")
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 0)
        urlopen.assert_not_called()

    def test_nflverse_release_resolver_selects_official_games_csv(self):
        release = {
            "tag_name": "schedules",
            "assets": [
                {
                    "name": "timestamp.txt",
                    "browser_download_url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/timestamp.txt",
                    "size": 10,
                },
                {
                    "name": "games.csv",
                    "browser_download_url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv",
                    "size": 123,
                },
            ],
        }
        with patch('src.automation_scheduler_legacy.open_sports_history_import._urlopen_json', return_value=release):
            resolved = resolve_nflverse_schedules_source()

        self.assertTrue(resolved["source_url_verified"])
        self.assertEqual(resolved["selected_source_url_kind"], "nflverse_data_release_asset")
        self.assertEqual(resolved["selected_source_host"], "github.com")
        self.assertEqual(resolved["selected_release_tag"], "schedules")
        self.assertEqual(resolved["selected_asset_name"], "games.csv")
        self.assertEqual(resolved["selected_asset_format"], "csv")
        self.assertFalse(resolved["fallback_used"])
        self.assertEqual(resolved["provider_calls_attempted"], 1)
        self.assertEqual(resolved["provider_calls_succeeded"], 1)

    def test_nflverse_resolver_falls_back_to_official_raw_games_csv_when_release_asset_missing(self):
        with patch('src.automation_scheduler_legacy.open_sports_history_import._urlopen_json', return_value={"assets": []}):
            resolved = resolve_nflverse_schedules_source()

        self.assertTrue(resolved["source_url_verified"])
        self.assertEqual(resolved["selected_source_url_kind"], "nflverse_nfldata_games_csv_fallback")
        self.assertEqual(resolved["selected_source_host"], "raw.githubusercontent.com")
        self.assertEqual(resolved["selected_asset_name"], "games.csv")
        self.assertTrue(resolved["fallback_used"])
        self.assertEqual(resolved["url_resolution_blocker"], "source_not_available")
        self.assertEqual(resolved["_download_url"], NFLVERSE_RAW_GAMES_CSV_FALLBACK_URL)

    def test_nflverse_resolver_can_report_unresolved_without_fallback(self):
        with patch('src.automation_scheduler_legacy.open_sports_history_import._urlopen_json', return_value={"assets": []}):
            resolved = resolve_nflverse_schedules_source(allow_fallback=False)

        self.assertFalse(resolved["source_url_verified"])
        self.assertEqual(resolved["url_resolution_blocker"], "source_not_available")
        self.assertFalse(resolved["fallback_used"])
        self.assertIsNone(resolved["_download_url"])

    def test_nflverse_resolver_falls_back_after_provider_error(self):
        with patch('src.automation_scheduler_legacy.open_sports_history_import._urlopen_json', side_effect=urllib.error.URLError("boom")):
            resolved = resolve_nflverse_schedules_source()

        self.assertTrue(resolved["fallback_used"])
        self.assertEqual(resolved["url_resolution_blocker"], "provider_error")
        self.assertEqual(resolved["provider_calls_attempted"], 1)
        self.assertEqual(resolved["provider_calls_succeeded"], 0)

    def test_source_url_classifier_rejects_unofficial_download_hosts(self):
        official = classify_open_data_source_url("https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv")
        fallback = classify_open_data_source_url(NFLVERSE_RAW_GAMES_CSV_FALLBACK_URL)
        unofficial = classify_open_data_source_url("https://example.com/games.csv")

        self.assertTrue(official["source_url_verified"])
        self.assertEqual(official["selected_source_url_kind"], "nflverse_data_release_asset")
        self.assertTrue(fallback["source_url_verified"])
        self.assertEqual(fallback["selected_source_url_kind"], "nflverse_nfldata_games_csv_fallback")
        self.assertFalse(unofficial["source_url_verified"])
        self.assertEqual(unofficial["url_resolution_blocker"], "source_url_unverified")

    def test_nflverse_schedule_columns_are_validated(self):
        valid, missing = validate_nflverse_schedule_columns(
            ["game_id", "gameday", "season", "home_team", "away_team", "home_score", "away_score"]
        )
        invalid, invalid_missing = validate_nflverse_schedule_columns(["game_id", "season"])

        self.assertTrue(valid)
        self.assertEqual(missing, [])
        self.assertFalse(invalid)
        self.assertIn("event_date", invalid_missing)
        self.assertIn("home_score", invalid_missing)

    def test_nflverse_download_uses_python_http_and_compact_official_metadata_only(self):
        release = {
            "assets": [
                {
                    "name": "games.csv",
                    "browser_download_url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv",
                    "size": 321,
                }
            ]
        }
        csv_text = "\n".join(
            [
                "game_id,gameday,season,week,game_type,home_team,away_team,home_score,away_score",
                "2023_01_A_B,2023-09-01,2023,1,REG,A,B,10,7",
                "2024_01_BAL_KC,2024-09-05,2024,1,REG,KC,BAL,27,20",
                "2024_02_BUF_MIA,2024-09-12,2024,2,REG,MIA,BUF,31,28",
            ]
        )
        calls = []

        def fake_urlopen(request, timeout=20):
            url = getattr(request, "full_url", str(request))
            calls.append((url, timeout))
            if url.endswith("/releases/tags/schedules"):
                return FakeHttpResponse(json.dumps(release))
            if url.endswith("/releases/download/schedules/games.csv"):
                return FakeHttpResponse(csv_text)
            raise AssertionError(f"unexpected url {url}")

        with patch('src.automation_scheduler_legacy.open_sports_history_import.urllib.request.urlopen', side_effect=fake_urlopen):
            report = build_open_sports_history_import_report(
                source_id="nflverse_nfl",
                season=2024,
                allow_download=True,
                max_records=10,
            )

        rendered = json.dumps(report, sort_keys=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["records_received"], 2)
        self.assertEqual(report["records_valid"], 2)
        self.assertEqual(report["downloads_attempted"], 1)
        self.assertEqual(report["downloads_succeeded"], 1)
        self.assertEqual(report["provider_calls_attempted"], 1)
        self.assertEqual(report["provider_calls_succeeded"], 1)
        self.assertEqual(report["data_kind"], "real_open_data")
        self.assertFalse(report["is_synthetic"])
        self.assertEqual(report["selected_source_url_kind"], "nflverse_data_release_asset")
        self.assertEqual(report["selected_asset_name"], "games.csv")
        self.assertEqual(report["source_availability"]["all_available_completed_seasons"], ["2023", "2024"])
        self.assertEqual(report["source_availability"]["latest_available_completed_season"], "2024")
        self.assertEqual({row["season"] for row in report["validated_preview_rows"]}, {"2024"})
        self.assertEqual({row["game_type"] for row in report["validated_preview_rows"]}, {"REG"})
        self.assertTrue(all(row["data_kind"] == "real_open_data" for row in report["validated_preview_rows"]))
        self.assertTrue(all(row["is_synthetic"] is False for row in report["validated_preview_rows"]))
        self.assertEqual([url for url, _ in calls], [
            "https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules",
            "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv",
        ])
        self.assertNotIn("browser_download_url", rendered)
        self.assertNotIn('"assets"', rendered)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_nflverse_source_availability_marks_incomplete_future_seasons(self):
        availability = build_nflverse_schedule_availability(
            [
                {"game_id": "2024_01_A_B", "season": "2024", "gameday": "2024-09-01", "game_type": "REG", "home_team": "A", "away_team": "B", "home_score": "10", "away_score": "7"},
                {"game_id": "2025_01_A_B", "season": "2025", "gameday": "2025-09-01", "game_type": "REG", "home_team": "A", "away_team": "B", "home_score": "", "away_score": ""},
            ]
        )

        self.assertEqual(availability["target_coverage_strategy"], "all_available_completed_seasons")
        self.assertEqual(availability["earliest_available_season"], "2024")
        self.assertEqual(availability["latest_available_completed_season"], "2024")
        self.assertEqual(availability["all_available_completed_seasons"], ["2024"])
        self.assertEqual(availability["incomplete_or_future_seasons"], ["2025"])
        self.assertEqual(availability["source_completion_status"]["2025"]["status"], "incomplete_or_future")

    def test_import_module_has_no_browser_or_html_scraping_dependency(self):
        source = inspect.getsource(open_sports_history_import)
        self.assertIn("urllib.request", source)
        self.assertNotIn("BeautifulSoup", source)
        self.assertNotIn("playwright", source)
        self.assertNotIn("selenium", source)

    def test_max_records_default_and_hard_cap_are_enforced(self):
        defaulted = build_open_sports_history_import_report(source_id="retrosheet_mlb", input_path="missing.csv")
        capped = build_open_sports_history_import_report(source_id="retrosheet_mlb", input_path="missing.csv", max_records=9999)
        self.assertEqual(defaulted["max_records_effective"], 25)
        self.assertEqual(capped["max_records_effective"], HARD_MAX_RECORDS)

    def test_unsupported_and_paid_sources_are_rejected(self):
        unsupported = build_open_sports_history_import_report(source_id="not_real", input_path="sample.csv")
        self.assertFalse(unsupported["ok"])
        self.assertEqual(unsupported["blocked_reason"], "unsupported_source")
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
            "supports_direct_download": False,
        }
        with patch('src.automation_scheduler_legacy.open_sports_history_import.source_by_id', return_value=paid_source):
            paid = build_open_sports_history_import_report(source_id="paid_fixture", input_path="sample.csv")
        self.assertFalse(paid["ok"])
        self.assertEqual(paid["blocked_reason"], "paid_source_not_approved")

    def test_sports_reference_download_is_blocked(self):
        report = build_open_sports_history_import_report(
            source_id="sports_reference_manual_export",
            allow_download=True,
        )
        self.assertFalse(report["ok"])
        self.assertEqual(report["blocked_reason"], "sports_reference_scraping_blocked")
        self.assertEqual(report["downloads_attempted"], 0)

    def test_retrosheet_fixture_maps_aliases_and_derived_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "retrosheet.csv"
            self._write_csv(
                path,
                [
                    {
                        "GAME_ID": "MLB202404010",
                        "GAME_DT": "20240401",
                        "HOME_TEAM_ID": "BOS",
                        "AWAY_TEAM_ID": "NYY",
                        "HOME_SCORE_CT": "5",
                        "AWAY_SCORE_CT": "3",
                    }
                ],
            )
            report = build_open_sports_history_import_report(source_id="retrosheet_mlb", input_path=path)

        row = self._row(report)
        self.assertTrue(report["ok"])
        self.assertEqual(row["module"], "baseball_mlb")
        self.assertEqual(row["event_id"], "MLB202404010")
        self.assertEqual(row["event_date"], "2024-04-01")
        self.assertEqual(row["season"], 2024)
        self.assertEqual(row["home_participant"], "BOS")
        self.assertEqual(row["away_participant"], "NYY")
        self.assertEqual(row["home_score"], 5)
        self.assertEqual(row["away_score"], 3)
        self.assertEqual(row["winner"], "BOS")
        self.assertEqual(row["final_margin"], 2)
        self.assertEqual(row["total_score"], 8)
        self.assertEqual(row["blocked_reason"], "available")
        self.assertRegex(row["source_record_hash"], r"^[0-9a-f]{64}$")

    def test_retrosheet_common_date_team_and_score_aliases_work(self):
        row = normalize_open_sports_history_row(
            {
                "game_id": "mlb-2",
                "Date": "2024-04-02",
                "Home": "LAD",
                "Away": "SFG",
                "home_runs": "4",
                "away_runs": "7",
            },
            source_id="retrosheet_mlb",
            module="baseball_mlb",
        )
        self.assertEqual(row["event_date"], "2024-04-02")
        self.assertEqual(row["home_participant"], "LAD")
        self.assertEqual(row["away_participant"], "SFG")
        self.assertEqual(row["winner"], "SFG")
        self.assertEqual(row["final_margin"], -3)
        self.assertEqual(row["total_score"], 11)

    def test_retrosheet_missing_fields_are_rejected(self):
        missing_date = normalize_open_sports_history_row(
            {"game_id": "mlb-3", "home_team": "A", "away_team": "B", "home_score": "1", "away_score": "0"},
            source_id="retrosheet_mlb",
            module="baseball_mlb",
        )
        missing_participant = normalize_open_sports_history_row(
            {"game_id": "mlb-4", "date": "2024-04-03", "home_team": "A", "home_score": "1", "away_score": "0"},
            source_id="retrosheet_mlb",
            module="baseball_mlb",
        )
        missing_score = normalize_open_sports_history_row(
            {"game_id": "mlb-5", "date": "2024-04-03", "home_team": "A", "away_team": "B"},
            source_id="retrosheet_mlb",
            module="baseball_mlb",
        )
        self.assertEqual(missing_date["blocked_reason"], "missing_event_date")
        self.assertEqual(missing_participant["blocked_reason"], "missing_participants")
        self.assertEqual(missing_score["blocked_reason"], "missing_scores_or_results")

    def test_nflverse_fixture_maps_aliases_and_week(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nflverse.csv"
            self._write_csv(
                path,
                [
                    {
                        "game_id": "2024_01_BAL_KC",
                        "gameday": "2024-09-05",
                        "season": "2024",
                        "week": "1",
                        "game_type": "REG",
                        "home_team": "KC",
                        "away_team": "BAL",
                        "home_score": "27",
                        "away_score": "20",
                    }
                ],
            )
            report = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path)

        row = self._row(report)
        self.assertTrue(report["ok"])
        self.assertEqual(row["module"], "americanfootball_nfl")
        self.assertEqual(row["event_id"], "2024_01_BAL_KC")
        self.assertEqual(row["event_date"], "2024-09-05")
        self.assertEqual(row["season"], "2024")
        self.assertEqual(row["week_or_round"], "1")
        self.assertEqual(row["game_type"], "REG")
        self.assertTrue(row["source_label_fields_present"])
        self.assertIsNone(row["playoff_round"])
        self.assertEqual(row["home_participant"], "KC")
        self.assertEqual(row["away_participant"], "BAL")
        self.assertEqual(row["winner"], "KC")
        self.assertEqual(row["final_margin"], 7)
        self.assertEqual(row["total_score"], 47)

    def test_nflverse_postseason_label_fields_are_preserved_without_inference(self):
        row = normalize_open_sports_history_row(
            {
                "game_id": "2024_SB_A_B",
                "gameday": "2025-02-09",
                "season": "2024",
                "week": "22",
                "game_type": "SB",
                "home_team": "A",
                "away_team": "B",
                "home_score": "31",
                "away_score": "24",
            },
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
        )
        no_label = normalize_open_sports_history_row(
            {
                "game_id": "2024_22_A_B",
                "gameday": "2025-02-09",
                "season": "2024",
                "week": "22",
                "home_team": "A",
                "away_team": "B",
                "home_score": "31",
                "away_score": "24",
            },
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
        )

        self.assertEqual(row["game_type"], "SB")
        self.assertEqual(row["playoff_round"], "SB")
        self.assertTrue(row["source_label_fields_present"])
        self.assertIsNone(row["postseason_flag"])
        self.assertIsNone(no_label["game_type"])
        self.assertIsNone(no_label["playoff_round"])
        self.assertFalse(no_label["source_label_fields_present"])

    def test_nflverse_old_ids_and_point_aliases_work(self):
        row = normalize_open_sports_history_row(
            {
                "old_game_id": "2023_02_MIN_PHI",
                "game_date": "2023-09-14",
                "home_team": "PHI",
                "away_team": "MIN",
                "home_points": "34",
                "away_points": "28",
            },
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
        )
        self.assertEqual(row["event_id"], "2023_02_MIN_PHI")
        self.assertEqual(row["event_date"], "2023-09-14")
        self.assertEqual(row["winner"], "PHI")
        self.assertEqual(row["final_margin"], 6)

    def test_nflverse_missing_and_nonnumeric_values_are_rejected(self):
        missing_date = normalize_open_sports_history_row(
            {"game_id": "nfl-1", "home_team": "A", "away_team": "B", "home_score": "10", "away_score": "7"},
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
        )
        missing_participant = normalize_open_sports_history_row(
            {"game_id": "nfl-2", "gameday": "2024-09-01", "home_team": "A", "home_score": "10", "away_score": "7"},
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
        )
        nonnumeric = normalize_open_sports_history_row(
            {"game_id": "nfl-3", "gameday": "2024-09-01", "home_team": "A", "away_team": "B", "home_score": "ten", "away_score": "7"},
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
        )
        self.assertEqual(missing_date["blocked_reason"], "missing_event_date")
        self.assertEqual(missing_participant["blocked_reason"], "missing_participants")
        self.assertEqual(nonnumeric["blocked_reason"], "nonnumeric_score")

    def test_raw_payload_secret_and_duplicates_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.json"
            path.write_text(
                json.dumps(
                    {
                        "records": [
                            {"game_id": "nfl-dup", "gameday": "2024-09-01", "home_team": "A", "away_team": "B", "home_score": 21, "away_score": 17},
                            {"game_id": "nfl-dup", "gameday": "2024-09-01", "home_team": "A", "away_team": "B", "home_score": 21, "away_score": 17},
                            {"game_id": "nfl-raw", "gameday": "2024-09-01", "home_team": "A", "away_team": "B", "home_score": 21, "away_score": 17, "raw_payload": {"x": 1}},
                            {"game_id": "nfl-secret", "gameday": "2024-09-01", "home_team": "A", "away_team": "B", "home_score": 21, "away_score": 17, "api_token": "do-not-leak"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            report = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path, max_records=10)
            rendered = json.dumps(report, sort_keys=True).lower()

        self.assertEqual(report["records_valid"], 1)
        self.assertEqual(report["blocked_reason_counts"]["duplicate_record"], 1)
        self.assertEqual(report["blocked_reason_counts"]["raw_payload_risk"], 1)
        self.assertEqual(report["blocked_reason_counts"]["secret_risk"], 1)
        self.assertNotIn("do-not-leak", rendered)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_persist_preview_writes_only_compact_preview_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "retrosheet.csv"
            self._write_csv(
                path,
                [{"game_id": "mlb-1", "date": "2024-04-01", "home_team": "BOS", "away_team": "NYY", "home_runs": "5", "away_runs": "3"}],
            )
            report = build_open_sports_history_import_report(source_id="retrosheet_mlb", input_path=path, persist_preview=True, base_data_dir=tmp)
            paths = write_open_sports_history_import_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            by_source = Path(tmp, paths["by_source_paths"][0])
            by_module = Path(tmp, paths["by_module_paths"][0])
            by_season = Path(tmp, paths["by_season_paths"][0])
            self.assertTrue(latest.exists())
            self.assertTrue(by_source.exists())
            self.assertTrue(by_module.exists())
            self.assertTrue(by_season.exists())

        self.assertIn("data_sources/open_sports_history/validated/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/open_sports_history/validated/by_source/retrosheet_mlb.json", paths["by_source_paths"][0])
        self.assertIn("data_sources/open_sports_history/validated/by_module/baseball_mlb.json", paths["by_module_paths"][0])
        self.assertIn("data_sources/open_sports_history/validated/by_season/baseball_mlb/2024.json", paths["by_season_paths"][0])
        self.assertEqual(report["outcome_persistence_attempted"], False)
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])

    def test_persist_preview_enriches_duplicate_nflverse_event_labels_without_changing_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            first_path = Path(tmp) / "nflverse_missing_label.csv"
            self._write_csv(
                first_path,
                [
                    {
                        "game_id": "2024_01_BAL_KC",
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
            first = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=first_path, persist_preview=True, base_data_dir=tmp)
            write_open_sports_history_import_report(first, base_data_dir=tmp)
            second_path = Path(tmp) / "nflverse_with_label.csv"
            self._write_csv(
                second_path,
                [
                    {
                        "game_id": "2024_01_BAL_KC",
                        "gameday": "2024-09-05",
                        "season": "2024",
                        "week": "1",
                        "game_type": "REG",
                        "home_team": "KC",
                        "away_team": "BAL",
                        "home_score": "99",
                        "away_score": "0",
                    }
                ],
            )
            second = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=second_path, persist_preview=True, base_data_dir=tmp)
            write_open_sports_history_import_report(second, base_data_dir=tmp)
            by_source = Path(tmp) / "data_sources" / "open_sports_history" / "validated" / "by_source" / "nflverse_nfl.json"
            rows = json.loads(by_source.read_text(encoding="utf-8"))["validated_preview_rows"]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_id"], "2024_01_BAL_KC")
        self.assertEqual(rows[0]["game_type"], "REG")
        self.assertTrue(rows[0]["source_label_fields_present"])
        self.assertEqual(rows[0]["home_score"], 27)
        self.assertEqual(rows[0]["away_score"], 20)


if __name__ == "__main__":
    unittest.main()
