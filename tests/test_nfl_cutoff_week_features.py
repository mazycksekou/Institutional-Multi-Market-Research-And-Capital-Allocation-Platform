import json
import tempfile
import unittest
from pathlib import Path

from src.automation_scheduler_legacy.nfl_cutoff_week_features import CutoffContextError, build_cutoff_feature_report, build_cutoff_week_context, compute_cutoff_feature_values, filter_records_by_cutoff, validate_no_future_data_used, write_cutoff_feature_report


def _seed(tmp, source_id, rows, *, season="2024"):
    path = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / source_id / "by_season" / f"{season}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sample_rows": rows, "season": season}), encoding="utf-8")


def _pbp_rows():
    return [
        {"season": "2024", "week": "1", "game_type": "REG", "posteam": "KC", "team": "KC", "play_id": "1", "yards_gained": "5", "epa": "0.1"},
        {"season": "2024", "week": "6", "game_type": "REG", "posteam": "KC", "team": "KC", "play_id": "2", "yards_gained": "9", "epa": "0.4"},
        {"season": "2024", "week": "12", "game_type": "REG", "posteam": "KC", "team": "KC", "play_id": "3", "yards_gained": "3", "epa": "-0.2"},
        {"season": "2024", "week": "20", "game_type": "SB", "posteam": "KC", "team": "KC", "play_id": "4", "yards_gained": "11", "epa": "0.9"},
    ]


class TestNflCutoffWeekFeatures(unittest.TestCase):
    def test_context_requires_season_and_cutoff_week(self):
        with self.assertRaises(CutoffContextError):
            build_cutoff_week_context(season=None, cutoff_week=8)
        with self.assertRaises(CutoffContextError):
            build_cutoff_week_context(season=2024, cutoff_week=None)
        context = build_cutoff_week_context(season=2024, cutoff_week=8)
        self.assertEqual(context["season"], "2024")
        self.assertEqual(context["cutoff_week"], 8)

    def test_cutoff_filter_excludes_future_weeks(self):
        context = build_cutoff_week_context(season=2024, cutoff_week=8)
        result = filter_records_by_cutoff(_pbp_rows(), context)
        self.assertEqual(result["kept_count"], 2)
        self.assertEqual(result["excluded_future"], 1)
        self.assertEqual(result["max_week_used"], 6)

    def test_cutoff_filter_excludes_postseason_by_default(self):
        context = build_cutoff_week_context(season=2024, cutoff_week=25)
        result = filter_records_by_cutoff(_pbp_rows(), context)
        self.assertEqual(result["excluded_postseason"], 1)
        included = build_cutoff_week_context(season=2024, cutoff_week=25, include_postseason=True)
        result2 = filter_records_by_cutoff(_pbp_rows(), included)
        self.assertEqual(result2["excluded_postseason"], 0)

    def test_validate_no_future_data(self):
        context = build_cutoff_week_context(season=2024, cutoff_week=8)
        self.assertFalse(validate_no_future_data_used(_pbp_rows(), context))
        kept = filter_records_by_cutoff(_pbp_rows(), context)["kept"]
        self.assertTrue(validate_no_future_data_used(kept, context))

    def test_features_include_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed(tmp, "nflverse_pace_or_play_volume", _pbp_rows())
            context = build_cutoff_week_context(season=2024, cutoff_week=8, team="KC", source_lanes=["team_game_play_volume"])
            features = compute_cutoff_feature_values(context, base_data_dir=tmp)
        row = features[0]
        self.assertEqual(row["status"], "available")
        provenance = row["provenance"]
        for key in ("source_id", "source_fields_used", "season", "max_week_used", "cutoff_week", "cutoff_passed", "leakage_risk", "cutoff_required"):
            self.assertIn(key, provenance)
        self.assertTrue(provenance["cutoff_passed"])
        self.assertLessEqual(provenance["max_week_used"], 8)

    def test_cutoff_sensitive_fields_blocked_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed(tmp, "nflverse_injuries", [{"season": "2024", "week": "1", "game_type": "REG", "team": "KC", "report_status": "Out"}])
            context = build_cutoff_week_context(season=2024, cutoff_week=8, team="KC", source_lanes=["injury_availability"])
            features = compute_cutoff_feature_values(context, base_data_dir=tmp)
        self.assertEqual(features[0]["status"], "blocked")
        self.assertEqual(features[0]["blocked_reason"], "cutoff_sensitive_field_requires_explicit_allow")

    def test_market_odds_blocked_unless_explicitly_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed(tmp, "nflverse_betting_lines_or_market_odds", [{"season": "2024", "week": "1", "game_type": "REG", "home_team": "KC", "spread_line": "-3"}])
            blocked = compute_cutoff_feature_values(
                build_cutoff_week_context(season=2024, cutoff_week=8, source_lanes=["market_odds"]),
                base_data_dir=tmp,
            )
            self.assertEqual(blocked[0]["status"], "blocked")
            allowed = compute_cutoff_feature_values(
                build_cutoff_week_context(season=2024, cutoff_week=8, source_lanes=["market_odds"], allow_cutoff_sensitive_fields=True),
                base_data_dir=tmp,
            )
        self.assertIn(allowed[0]["status"], {"available", "blocked"})
        if allowed[0]["status"] == "blocked":
            self.assertNotEqual(allowed[0]["blocked_reason"], "cutoff_sensitive_field_requires_explicit_allow")

    def test_roster_injury_depth_do_not_use_future_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed(tmp, "nflverse_weekly_rosters", [
                {"season": "2024", "week": "2", "game_type": "REG", "team": "KC", "gsis_id": "p1"},
                {"season": "2024", "week": "15", "game_type": "REG", "team": "KC", "gsis_id": "p2"},
            ])
            context = build_cutoff_week_context(
                season=2024, cutoff_week=8, team="KC", source_lanes=["roster_continuity"], allow_cutoff_sensitive_fields=True
            )
            features = compute_cutoff_feature_values(context, base_data_dir=tmp)
        row = features[0]
        if row["status"] == "available":
            self.assertLessEqual(row["provenance"]["max_week_used"], 8)
            self.assertTrue(row["provenance"]["cutoff_passed"])
            self.assertEqual(row["cutoff_filter"]["excluded_future"], 1)

    def test_report_excludes_future_and_writes_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed(tmp, "nflverse_pace_or_play_volume", _pbp_rows())
            report = build_cutoff_feature_report(season=2024, cutoff_week=8, team="KC", base_data_dir=tmp)
            paths = write_cutoff_feature_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()
        self.assertTrue(latest_exists)
        self.assertTrue(report["no_future_data_used"])
        self.assertTrue(report["no_target_labels_used"])
        self.assertTrue(report["no_predictive_claim"])
        self.assertEqual(report["nfl_cutoff_week_leakage_guard_status"], "passed")
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["downloads_succeeded"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertIn("data_sources/nfl_open_data/cutoff_features/latest.json", paths["latest_json_path"])
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_payload", rendered)


if __name__ == "__main__":
    unittest.main()
