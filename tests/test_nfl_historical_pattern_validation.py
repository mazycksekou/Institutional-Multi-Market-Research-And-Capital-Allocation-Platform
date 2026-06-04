import csv
import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_historical_pattern_lab import (
    HOLDOUT_ALLOWED_SIMILARITY_FEATURES,
    build_holdout_leakage_guard,
    build_historical_holdout_validation_scorecard,
    build_regular_season_snapshot_profiles,
    build_team_game_profiles,
    build_validation_guard_summary,
    derive_postseason_target_labels,
    evaluate_comps_against_targets,
    find_prior_season_comps,
    write_nfl_historical_holdout_validation_report,
)
from automation_scheduler.open_sports_history_import import (
    build_open_sports_history_import_report,
    write_open_sports_history_import_report,
)


class TestNflHistoricalPatternValidation(unittest.TestCase):
    def _write_csv(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _rows(self, seasons=range(2019, 2025)):
        rows = []
        teams = ["A", "B", "C", "D"]
        for season in seasons:
            rows.extend(
                [
                    {
                        "game_id": f"{season}_REG_01_A_B",
                        "gameday": f"{season}-09-01",
                        "season": str(season),
                        "week": "1",
                        "game_type": "REG",
                        "home_team": "A",
                        "away_team": "B",
                        "home_score": str(28 + season % 3),
                        "away_score": "17",
                    },
                    {
                        "game_id": f"{season}_REG_02_C_D",
                        "gameday": f"{season}-09-02",
                        "season": str(season),
                        "week": "1",
                        "game_type": "REG",
                        "home_team": "C",
                        "away_team": "D",
                        "home_score": "13",
                        "away_score": "20",
                    },
                    {
                        "game_id": f"{season}_REG_03_A_C",
                        "gameday": f"{season}-09-08",
                        "season": str(season),
                        "week": "2",
                        "game_type": "REG",
                        "home_team": "C",
                        "away_team": "A",
                        "home_score": "14",
                        "away_score": str(24 + season % 4),
                    },
                    {
                        "game_id": f"{season}_REG_04_B_D",
                        "gameday": f"{season}-09-09",
                        "season": str(season),
                        "week": "2",
                        "game_type": "REG",
                        "home_team": "D",
                        "away_team": "B",
                        "home_score": "21",
                        "away_score": "14",
                    },
                ]
            )
            rows.append(
                {
                    "game_id": f"{season}_WC_B_A",
                    "gameday": f"{season + 1}-01-05",
                    "season": str(season),
                    "week": "19",
                    "game_type": "WC",
                    "home_team": "A",
                    "away_team": "B",
                    "home_score": "27",
                    "away_score": "10",
                }
            )
            rows.append(
                {
                    "game_id": f"{season}_CON_D_A",
                    "gameday": f"{season + 1}-01-19",
                    "season": str(season),
                    "week": "21",
                    "game_type": "CON",
                    "home_team": "A",
                    "away_team": "D",
                    "home_score": "24",
                    "away_score": "20",
                }
            )
            if season % 2 == 0:
                rows.append(
                    {
                        "game_id": f"{season}_SB_C_A",
                        "gameday": f"{season + 1}-02-09",
                        "season": str(season),
                        "week": "22",
                        "game_type": "SB",
                        "home_team": "A",
                        "away_team": "C",
                        "home_score": "31",
                        "away_score": "28",
                    }
                )
        return rows

    def _persist_rows(self, tmp, rows=None, path_name="nflverse.csv"):
        path = Path(tmp) / path_name
        self._write_csv(path, rows or self._rows())
        report = build_open_sports_history_import_report(
            source_id="nflverse_nfl",
            input_path=path,
            max_records=500,
            persist_preview=True,
            base_data_dir=tmp,
        )
        self.assertTrue(report["ok"])
        write_open_sports_history_import_report(report, base_data_dir=tmp)
        return report

    def test_validation_consumes_real_open_data_only_and_ignores_synthetic(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_rows(tmp)
            imports_path = Path(tmp) / "data_sources" / "open_sports_history" / "imports" / "nflverse_nfl" / "sample.csv"
            self._write_csv(imports_path, self._rows(seasons=[2025]))
            synthetic = build_open_sports_history_import_report(
                source_id="nflverse_nfl",
                input_path=imports_path,
                max_records=50,
                persist_preview=True,
                base_data_dir=tmp,
            )
            self.assertTrue(synthetic["ok"])
            write_open_sports_history_import_report(synthetic, base_data_dir=tmp)
            report = build_historical_holdout_validation_scorecard(base_data_dir=tmp)

        self.assertGreater(report["real_rows_consumed"], 0)
        self.assertGreater(report["synthetic_rows_ignored"], 0)
        self.assertTrue(report["no_predictive_claim"])

    def test_regular_season_snapshot_excludes_postseason_games_and_labels(self):
        preview = self._persist_preview_only()
        games = build_team_game_profiles(preview["validated_preview_rows"])
        snapshots = build_regular_season_snapshot_profiles(games)
        team_a = [profile for profile in snapshots if profile["season"] == "2020" and profile["team"] == "A"][0]

        self.assertEqual(team_a["regular_season_games"], 2)
        self.assertTrue(team_a["regular_season_snapshot_only"])
        self.assertNotIn("postseason_flag", team_a)
        self.assertNotIn("super_bowl_flag", team_a)
        self.assertNotIn("playoff_game_count", team_a)

    def _persist_preview_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            return self._persist_rows(tmp)

    def test_prior_comps_exclude_same_and_future_seasons(self):
        preview = self._persist_preview_only()
        games = build_team_game_profiles(preview["validated_preview_rows"])
        snapshots = build_regular_season_snapshot_profiles(games)
        anchor = [profile for profile in snapshots if profile["season"] == "2022" and profile["team"] == "A"][0]
        comps = find_prior_season_comps(anchor, snapshots, top_k=20)

        self.assertTrue(comps)
        self.assertTrue(all(int(comp["comp_season"]) < 2022 for comp in comps))
        self.assertFalse(any(comp["comp_season"] == "2022" for comp in comps))
        self.assertFalse(any(int(comp["comp_season"]) > 2022 for comp in comps))

    def test_targets_derive_from_explicit_game_type_labels(self):
        preview = self._persist_preview_only()
        games = build_team_game_profiles(preview["validated_preview_rows"])
        targets = derive_postseason_target_labels(games)
        team_a_2020 = targets[("2020", "A")]["target_values"]
        team_b_2020 = targets[("2020", "B")]["target_values"]

        self.assertTrue(team_a_2020["made_playoffs"])
        self.assertTrue(team_a_2020["won_playoff_game"])
        self.assertTrue(team_a_2020["reached_conference_championship"])
        self.assertTrue(team_a_2020["reached_super_bowl"])
        self.assertTrue(team_a_2020["won_super_bowl"])
        self.assertTrue(team_b_2020["made_playoffs"])
        self.assertFalse(team_b_2020["won_playoff_game"])

    def test_leakage_guard_blocks_target_fields_as_inputs(self):
        for field in ("postseason_flag", "super_bowl_flag", "playoff_game_count"):
            guard = build_holdout_leakage_guard(HOLDOUT_ALLOWED_SIMILARITY_FEATURES + [field])
            self.assertEqual(guard["status"], "blocked_leakage_detected")
            self.assertIn(field, guard["leaked_features"])

    def test_validation_computes_base_comp_rate_lift_and_k_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_rows(tmp)
            report = build_historical_holdout_validation_scorecard(base_data_dir=tmp)

        self.assertEqual(report["similarity_k_values"], [5, 10, 20])
        self.assertIn("made_playoffs", report["validation_by_target"])
        made = report["validation_by_target"]["made_playoffs"]
        self.assertIsNotNone(made["base_rate"])
        self.assertIn("5", report["validation_by_k"])
        self.assertIn("10", report["validation_by_k"])
        self.assertIn("20", report["validation_by_k"])
        k5 = [row for row in report["validation_by_k"]["5"] if row["target"] == "made_playoffs"][0]
        self.assertIsNotNone(k5["average_comp_positive_rate"])
        self.assertIsNotNone(k5["lift_vs_base_rate"])
        self.assertTrue(k5["no_predictive_claim"])

    def test_insufficient_samples_produce_honest_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_rows(tmp, rows=self._rows(seasons=[2023]))
            report = build_historical_holdout_validation_scorecard(base_data_dir=tmp)

        self.assertIn(report["status"], {"insufficient_samples", "insufficient_labels", "insufficient_features"})
        self.assertTrue(report["blockers"])
        self.assertTrue(report["no_predictive_claim"])

    def test_leakage_guard_blocks_validation_status_when_leakage_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_rows(tmp)
            report = build_historical_holdout_validation_scorecard(
                base_data_dir=tmp,
                allowed_similarity_features=HOLDOUT_ALLOWED_SIMILARITY_FEATURES + ["postseason_flag"],
            )

        self.assertEqual(report["status"], "blocked_leakage_detected")
        self.assertEqual(report["leakage_guard"]["status"], "blocked_leakage_detected")
        self.assertEqual(report["anchor_profiles_evaluated"], 0)

    def test_validation_guard_blocks_new_feature_families_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._seed_nfl_lane(tmp, "nflverse_snap_counts", ["season", "week", "team", "player", "offense_snaps"])
            self._seed_nfl_lane(tmp, "nflverse_injuries", ["season", "week", "team", "report_status"])
            self._seed_nfl_lane(tmp, "nflverse_play_by_play", ["play_id", "posteam", "yards_gained", "epa"])
            summary = build_validation_guard_summary(base_data_dir=tmp)

        self.assertGreater(summary["candidate_features_count"], summary["allowed_validation_features_count"])
        self.assertEqual(summary["allowed_validation_features_count"], len(HOLDOUT_ALLOWED_SIMILARITY_FEATURES))
        self.assertIn("injury_availability", summary["blocked_by_leakage"])
        self.assertIn("player_usage_snaps", summary["blocked_by_leakage"])
        self.assertIn("team_game_efficiency_candidates", summary["blocked_by_cutoff"])
        self.assertEqual(summary["blocked_by_future_data"], [])
        self.assertTrue(summary["market_features_cutoff_sensitive_by_default"])
        self.assertTrue(summary["postseason_labels_target_only"])
        self.assertTrue(summary["no_predictive_claim"])

    def test_validation_guard_blocks_missing_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = build_validation_guard_summary(base_data_dir=tmp)
        self.assertTrue(summary["blocked_by_missing_provenance"])

    def test_scorecard_includes_validation_guard_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_rows(tmp)
            report = build_historical_holdout_validation_scorecard(base_data_dir=tmp)
        self.assertIn("validation_guard_summary", report)
        guard = report["validation_guard_summary"]
        self.assertEqual(guard["allowed_validation_features_count"], len(HOLDOUT_ALLOWED_SIMILARITY_FEATURES))
        self.assertTrue(guard["no_predictive_claim"])

    def _seed_nfl_lane(self, tmp, source_id, fields, *, records=200, seasons=("2023", "2024")):
        path = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / source_id / "latest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "fields_available": list(fields),
                    "records_validated": records,
                    "seasons_backfilled": list(seasons),
                    "data_category": source_id.replace("nflverse_", ""),
                }
            ),
            encoding="utf-8",
        )

    def test_report_writes_compact_outputs_and_safety_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._persist_rows(tmp)
            report = build_historical_holdout_validation_scorecard(base_data_dir=tmp)
            paths = write_nfl_historical_holdout_validation_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()

        self.assertTrue(latest_exists)
        self.assertIn("data_sources/open_sports_history/nfl_pattern_validation/latest.json", paths["latest_json_path"])
        self.assertIn("validation_by_target", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_response", rendered)
        self.assertNotIn("authorization", rendered)
        self.assertFalse(report["confirmed_bets_created"])
        self.assertFalse(report["no_bet_rows_modified"])
        self.assertFalse(report["outcome_store_written"])
        self.assertFalse(report["paper_ledger_written"])
        self.assertFalse(report["kalshi_calibration_mutated"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["downloads_succeeded"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])


if __name__ == "__main__":
    unittest.main()
