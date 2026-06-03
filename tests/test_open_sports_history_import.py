import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.open_sports_history_import import (
    HARD_MAX_RECORDS,
    build_open_sports_history_import_report,
    normalize_open_sports_history_row,
    write_open_sports_history_import_report,
)


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
        with patch("automation_scheduler.open_sports_history_import.urllib.request.urlopen") as urlopen:
            report = build_open_sports_history_import_report(source_id="nflverse_nfl", season=2024)
        self.assertEqual(report["blocked_reason"], "download_not_allowed")
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 0)
        urlopen.assert_not_called()

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
        with patch("automation_scheduler.open_sports_history_import.source_by_id", return_value=paid_source):
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
        self.assertEqual(row["home_participant"], "KC")
        self.assertEqual(row["away_participant"], "BAL")
        self.assertEqual(row["winner"], "KC")
        self.assertEqual(row["final_margin"], 7)
        self.assertEqual(row["total_score"], 47)

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
            self.assertTrue(latest.exists())

        self.assertIn("data_sources/open_sports_history/validated/latest.json", paths["latest_json_path"])
        self.assertEqual(report["outcome_persistence_attempted"], False)
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
