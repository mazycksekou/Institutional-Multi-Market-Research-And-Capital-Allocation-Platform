import csv
import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_historical_pattern_lab import (
    build_nfl_historical_pattern_lab_report,
    compute_team_profile_similarity,
    write_nfl_historical_pattern_lab_report,
)
from automation_scheduler.open_sports_history_import import (
    build_open_sports_history_import_report,
    write_open_sports_history_import_report,
)


class TestNflHistoricalPatternLab(unittest.TestCase):
    def _write_csv(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _rows(self):
        return [
            {"game_id": "2024_01_B_A", "gameday": "2024-09-01", "season": "2024", "week": "1", "game_type": "REG", "home_team": "A", "away_team": "B", "home_score": "10", "away_score": "0"},
            {"game_id": "2024_02_A_C", "gameday": "2024-09-08", "season": "2024", "week": "2", "game_type": "REG", "home_team": "C", "away_team": "A", "home_score": "10", "away_score": "0"},
            {"game_id": "2024_03_D_A", "gameday": "2024-09-15", "season": "2024", "week": "3", "game_type": "REG", "home_team": "A", "away_team": "D", "home_score": "21", "away_score": "14"},
            {"game_id": "2024_04_E_A", "gameday": "2024-09-22", "season": "2024", "week": "4", "game_type": "REG", "home_team": "A", "away_team": "E", "home_score": "28", "away_score": "7"},
            {"game_id": "2024_05_A_F", "gameday": "2024-09-29", "season": "2024", "week": "5", "game_type": "REG", "home_team": "F", "away_team": "A", "home_score": "14", "away_score": "14"},
            {"game_id": "2024_06_G_A", "gameday": "2024-10-06", "season": "2024", "week": "6", "game_type": "SB", "home_team": "A", "away_team": "G", "home_score": "35", "away_score": "21"},
        ]

    def _persist_real_rows(self, tmp, rows=None, path_name="nflverse.csv"):
        path = Path(tmp) / path_name
        self._write_csv(path, rows or self._rows())
        preview = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path, max_records=50, base_data_dir=tmp)
        self.assertTrue(preview["ok"])
        write_open_sports_history_import_report(preview, base_data_dir=tmp)
        return preview

    def _team(self, report, team):
        return {
            (profile["season"], profile["team"]): profile
            for profile in report["team_season_profiles"]
        }[("2024", team)]

    def test_team_season_profiles_are_created_from_real_open_data_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)

        self.assertEqual(report["real_rows_consumed"], 6)
        self.assertEqual(report["synthetic_rows_ignored"], 0)
        self.assertIn("2024", report["seasons_analyzed"])
        self.assertIn("A", report["teams_profiled"])
        self.assertGreaterEqual(report["team_season_profiles_created"], 7)
        self.assertEqual({profile["source_data_kind"] for profile in report["team_season_profiles"]}, {"real_open_data"})
        self.assertFalse(report["raw_payload_included"])

    def test_synthetic_rows_are_ignored_by_pattern_lab(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data_sources" / "open_sports_history" / "imports" / "nflverse_nfl" / "sample.csv"
            self._write_csv(path, self._rows())
            preview = build_open_sports_history_import_report(source_id="nflverse_nfl", input_path=path, max_records=50, base_data_dir=tmp)
            self.assertTrue(preview["ok"])
            write_open_sports_history_import_report(preview, base_data_dir=tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)

        self.assertEqual(report["real_rows_consumed"], 0)
        self.assertGreater(report["synthetic_rows_ignored"], 0)
        self.assertEqual(report["team_season_profiles_created"], 0)
        self.assertEqual(report["backtest_readiness_status"], "blocked_insufficient_real_history")

    def test_basic_team_metrics_derive_without_fabrication(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)
            team_a = self._team(report, "A")

        self.assertEqual(team_a["games_played"], 6)
        self.assertEqual(team_a["wins"], 4)
        self.assertEqual(team_a["losses"], 1)
        self.assertEqual(team_a["ties"], 1)
        self.assertEqual(team_a["points_for"], 108)
        self.assertEqual(team_a["points_against"], 66)
        self.assertEqual(team_a["point_differential"], 42)
        self.assertEqual(team_a["average_points_for"], 18)
        self.assertEqual(team_a["average_points_against"], 11)
        self.assertEqual(team_a["average_margin"], 7)
        self.assertEqual(team_a["home_record"]["wins"], 4)
        self.assertEqual(team_a["away_record"]["losses"], 1)
        self.assertEqual(team_a["close_game_record"]["games"], 2)
        self.assertEqual(team_a["blowout_wins"], 1)
        self.assertGreater(team_a["scoring_volatility"], 0)
        self.assertGreater(team_a["defensive_volatility"], 0)
        self.assertIsNotNone(team_a["schedule_strength_proxy"])

    def test_late_season_form_derives_chronologically(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)
            team_a = self._team(report, "A")

        self.assertEqual(team_a["late_season_form"]["games_used"], 5)
        self.assertEqual(team_a["late_season_form"]["wins"], 3)
        self.assertEqual(team_a["late_season_form"]["losses"], 1)
        self.assertEqual(team_a["late_season_form"]["ties"], 1)
        self.assertEqual(team_a["late_season_form"]["point_differential"], 32)
        self.assertEqual(team_a["late_season_win_rate"], 0.7)

    def test_playoff_and_super_bowl_labels_use_source_game_type_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)
            team_a = self._team(report, "A")

        self.assertEqual(report["playoff_super_bowl_labels_available"], "available")
        self.assertEqual(team_a["playoff_game_count"], 1)
        self.assertTrue(team_a["postseason_flag"])
        self.assertTrue(team_a["super_bowl_flag"])
        self.assertEqual(team_a["blocked_reasons"], [])

    def test_missing_playoff_and_super_bowl_labels_are_blocked_not_fabricated(self):
        rows = [{k: v for k, v in row.items() if k != "game_type"} for row in self._rows()]
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp, rows=rows)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)
            team_a = self._team(report, "A")

        self.assertEqual(report["playoff_super_bowl_labels_available"], "blocked")
        self.assertIn("playoff_round_labels_missing", report["label_blockers"])
        self.assertIn("super_bowl_label_missing", report["label_blockers"])
        self.assertIsNone(team_a["playoff_game_count"])
        self.assertIsNone(team_a["postseason_flag"])
        self.assertIsNone(team_a["super_bowl_flag"])

    def test_similarity_scoring_uses_only_available_numeric_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)
            profiles = {profile["team"]: profile for profile in report["team_season_profiles"] if profile["season"] == "2024"}
            similarity = compute_team_profile_similarity(profiles["A"], profiles["B"])

        self.assertIsNotNone(similarity["similarity_score"])
        self.assertGreaterEqual(len(similarity["features_compared"]), 3)
        self.assertIn("average_points_for", similarity["features_compared"])
        self.assertFalse(similarity["predictive_claim_made"])
        self.assertFalse(similarity["provider_write"])
        self.assertFalse(similarity["execution_allowed"])

    def test_similarity_scoring_returns_insufficient_data_for_sparse_profiles(self):
        similarity = compute_team_profile_similarity({"team": "A", "average_margin": 1}, {"team": "B"})

        self.assertIsNone(similarity["similarity_score"])
        self.assertEqual(similarity["blocked_reason"], "insufficient_data")
        self.assertEqual(similarity["confidence"], "insufficient")
        self.assertFalse(similarity["predictive_claim_made"])

    def test_report_writes_compact_outputs_and_safety_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)
            paths = write_nfl_historical_pattern_lab_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()

        self.assertTrue(latest_exists)
        self.assertIn("data_sources/open_sports_history/nfl_pattern_lab/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/open_sports_history/nfl_pattern_lab/items/", paths["item_json_path"])
        self.assertIn("team_season_profiles", rendered)
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["downloads_succeeded"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["outcome_store_written"])
        self.assertFalse(report["paper_ledger_written"])
        self.assertFalse(report["kalshi_calibration_mutated"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertFalse((Path(tmp) / "outcome_store").exists())
        self.assertFalse((Path(tmp) / "paper_ledger").exists())
        self.assertFalse((Path(tmp) / "data_sources" / "kalshi_calibration").exists())

    def test_similarity_feature_catalog_blocks_unavailable_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_real_rows(tmp)
            report = build_nfl_historical_pattern_lab_report(base_data_dir=tmp)

        self.assertIn("average_points_for", report["similarity_features_available"])
        self.assertIn("schedule_strength_proxy", report["similarity_features_available"])
        self.assertIn("market_price_or_odds", report["similarity_features_blocked"])
        self.assertIn("roster_continuity", report["similarity_features_blocked"])
        self.assertIn("injury_lineup_profile", report["similarity_features_blocked"])
        self.assertIn("pace_or_advanced_efficiency", report["similarity_features_blocked"])
        self.assertEqual(report["backtest_readiness_status"], "profile_scaffold_ready_no_predictive_validation")
        self.assertFalse(report["predictive_claim_made"])


if __name__ == "__main__":
    unittest.main()
