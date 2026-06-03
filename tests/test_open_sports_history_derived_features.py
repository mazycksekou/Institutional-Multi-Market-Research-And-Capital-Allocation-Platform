import csv
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.derived_feature_backfill_report import build_derived_feature_backfill_report
from automation_scheduler.open_sports_history_import import (
    build_open_sports_history_import_report,
    write_open_sports_history_import_report,
)


class TestOpenSportsHistoryDerivedFeatures(unittest.TestCase):
    def _write_csv(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _feature(self, report, module, feature):
        modules = {row["module"]: row for row in report["modules"]}
        rows = {row["feature_name"]: row for row in modules[module]["feature_rows"]}
        return rows[feature]

    def test_derived_report_consumes_validated_retrosheet_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "retrosheet.csv"
            self._write_csv(
                path,
                [{"game_id": "mlb-1", "date": "2024-04-01", "home_team": "BOS", "away_team": "NYY", "home_runs": "5", "away_runs": "3"}],
            )
            preview = build_open_sports_history_import_report(source_id="retrosheet_mlb", input_path=path, base_data_dir=tmp)
            write_open_sports_history_import_report(preview, base_data_dir=tmp)
            report = build_derived_feature_backfill_report(base_data_dir=tmp, module="baseball_mlb")

        self.assertEqual(report["open_sports_history_preview_rows_consumed"], 1)
        self.assertIn("data_sources/open_sports_history/validated/latest.json", report["reports_consumed"])
        self.assertIn("baseball_mlb", report["modules_ready_for_tier0_backfill"])
        self.assertTrue(self._feature(report, "baseball_mlb", "total_runs")["can_derive_now"])
        self.assertTrue(self._feature(report, "baseball_mlb", "winner")["can_derive_now"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertFalse(report["outcome_persistence_attempted"])

    def test_derived_report_consumes_validated_nflverse_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nflverse.csv"
            self._write_csv(
                path,
                [{"game_id": "nfl-1", "gameday": "2024-09-05", "season": "2024", "week": "1", "home_team": "KC", "away_team": "BAL", "home_score": "27", "away_score": "20"}],
            )
            preview = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path, base_data_dir=tmp)
            write_open_sports_history_import_report(preview, base_data_dir=tmp)
            report = build_derived_feature_backfill_report(base_data_dir=tmp, module="americanfootball_nfl")

        self.assertEqual(report["open_sports_history_preview_rows_consumed"], 1)
        self.assertIn("americanfootball_nfl", report["modules_ready_for_tier0_backfill"])
        self.assertTrue(self._feature(report, "americanfootball_nfl", "total_points")["can_derive_now"])
        self.assertTrue(self._feature(report, "americanfootball_nfl", "winner")["can_derive_now"])

    def test_tier1_features_require_sufficient_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short_nflverse.csv"
            self._write_csv(
                path,
                [{"game_id": "nfl-1", "gameday": "2024-09-05", "season": "2024", "week": "1", "home_team": "KC", "away_team": "BAL", "home_score": "27", "away_score": "20"}],
            )
            preview = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path, base_data_dir=tmp)
            write_open_sports_history_import_report(preview, base_data_dir=tmp)
            report = build_derived_feature_backfill_report(base_data_dir=tmp, module="americanfootball_nfl")

        row = self._feature(report, "americanfootball_nfl", "rolling_points_for")
        self.assertFalse(row["can_derive_now"])
        self.assertEqual(row["blocked_reason"], "insufficient_history")
        self.assertEqual(row["history_available"], 1)
        self.assertNotIn("americanfootball_nfl", report["modules_ready_for_tier1_derived_backfill"])

    def test_tier1_features_unlock_with_enough_valid_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nflverse.csv"
            rows = [
                {"game_id": f"nfl-{i}", "gameday": f"2024-09-{5 + i:02d}", "season": "2024", "week": str(i), "home_team": "KC", "away_team": "BAL", "home_score": str(20 + i), "away_score": "17"}
                for i in range(1, 6)
            ]
            self._write_csv(path, rows)
            preview = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path, max_records=10, base_data_dir=tmp)
            write_open_sports_history_import_report(preview, base_data_dir=tmp)
            report = build_derived_feature_backfill_report(base_data_dir=tmp, module="americanfootball_nfl")

        self.assertIn("americanfootball_nfl", report["modules_ready_for_tier1_derived_backfill"])
        self.assertTrue(self._feature(report, "americanfootball_nfl", "rolling_points_for")["can_derive_now"])
        self.assertTrue(self._feature(report, "americanfootball_nfl", "volatility")["can_derive_now"])
        self.assertTrue(self._feature(report, "americanfootball_nfl", "close_game_rate")["can_derive_now"])

    def test_sports_preview_rows_do_not_affect_prediction_market_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "retrosheet.csv"
            self._write_csv(
                path,
                [{"game_id": "mlb-1", "date": "2024-04-01", "home_team": "BOS", "away_team": "NYY", "home_runs": "5", "away_runs": "3"}],
            )
            preview = build_open_sports_history_import_report(source_id="retrosheet_mlb", input_path=path, base_data_dir=tmp)
            write_open_sports_history_import_report(preview, base_data_dir=tmp)
            report = build_derived_feature_backfill_report(base_data_dir=tmp)

        self.assertIn("baseball_mlb", report["modules_ready_for_tier0_backfill"])
        self.assertNotIn("prediction_markets", report["modules_ready_for_tier0_backfill"])
        self.assertNotIn("kalshi", report["modules_ready_for_tier0_backfill"])
        self.assertNotIn("polymarket", report["modules_ready_for_tier0_backfill"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["persisted_outcomes"])


if __name__ == "__main__":
    unittest.main()
