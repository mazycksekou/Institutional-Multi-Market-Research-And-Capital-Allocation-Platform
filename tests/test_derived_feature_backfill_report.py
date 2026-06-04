import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.derived_feature_backfill_report import (
    ALLOWED_BLOCKED_REASONS,
    build_derived_feature_backfill_report,
    normalize_schedule_result_record,
    write_derived_feature_backfill_report,
)


class TestDerivedFeatureBackfillReport(unittest.TestCase):
    def _feature(self, report, module, feature):
        modules = {row["module"]: row for row in report["modules"]}
        rows = {row["feature_name"]: row for row in modules[module]["feature_rows"]}
        return rows[feature]

    def test_report_persists_runtime_paths_and_latest_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_derived_feature_backfill_report(
                base_data_dir=tmp,
                module="basketball_nba",
                records_by_module={
                    "basketball_nba": [
                        {"home_team": "A", "away_team": "B", "home_score": 80, "away_score": 75, "event_date": "2026-01-01"}
                    ]
                },
            )
            paths = write_derived_feature_backfill_report(report, base_data_dir=tmp)
            latest_json = Path(tmp, paths["latest_json_path"])
            latest_md = Path(tmp, paths["latest_markdown_path"])
            item_md = Path(tmp, paths["item_markdown_path"])
            self.assertTrue(latest_json.exists())
            self.assertTrue(latest_md.exists())
            self.assertTrue(item_md.exists())
            markdown_lines = latest_md.read_text(encoding="utf-8").splitlines()

        self.assertIn("data_sources/derived_features/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/derived_features/latest.md", paths["latest_markdown_path"])
        self.assertIn("data_sources/derived_features/items/", paths["item_json_path"])
        self.assertIn("data_sources/derived_features/items/", paths["item_markdown_path"])
        self.assertIn("data_sources/derived_features/daily/", paths["daily_json_path"])
        self.assertIn("data_sources/derived_features/daily/", paths["daily_markdown_path"])
        self.assertNotIn("\\data_sources\\derived_features", str(latest_json.parent.parent.parent))
        self.assertEqual(len([line for line in markdown_lines if line[:2] in {f"{i}." for i in range(1, 9)}]), 8)

    def test_score_features_derive_from_local_results_without_fabrication(self):
        report = build_derived_feature_backfill_report(
            module="americanfootball_ncaaf",
            records_by_module={
                "americanfootball_ncaaf": [
                    {"home_team": "A", "away_team": "B", "home_score": 31, "away_score": 21, "event_date": "2026-01-01"}
                ]
            },
        )
        self.assertTrue(self._feature(report, "americanfootball_ncaaf", "final_margin")["can_derive_now"])
        self.assertTrue(self._feature(report, "americanfootball_ncaaf", "total_points")["can_derive_now"])
        self.assertTrue(self._feature(report, "americanfootball_ncaaf", "winner")["can_derive_now"])
        self.assertTrue(self._feature(report, "americanfootball_ncaaf", "final_margin")["no_fabrication_confirmed"])

    def test_rolling_features_require_enough_history(self):
        report = build_derived_feature_backfill_report(
            module="basketball_nba",
            records_by_module={
                "basketball_nba": [
                    {"home_team": "A", "away_team": "B", "home_score": 80, "away_score": 75, "event_date": "2026-01-01"},
                    {"home_team": "A", "away_team": "C", "home_score": 82, "away_score": 76, "event_date": "2026-01-03"},
                ]
            },
        )
        row = self._feature(report, "basketball_nba", "rolling_points_for")
        self.assertFalse(row["can_derive_now"])
        self.assertEqual(row["blocked_reason"], "insufficient_history")
        self.assertEqual(row["minimum_history_required"], 3)
        self.assertEqual(row["history_available"], 2)

    def test_missing_required_reasons_are_specific(self):
        report = build_derived_feature_backfill_report(
            module="soccer",
            records_by_module={"soccer": [{"home_team": "A", "away_team": "B"}]},
        )
        self.assertEqual(self._feature(report, "soccer", "final_margin")["blocked_reason"], "missing_scores_or_results")
        self.assertEqual(self._feature(report, "soccer", "rest_days")["blocked_reason"], "missing_event_dates")

    def test_missing_home_away_reason_is_specific(self):
        report = build_derived_feature_backfill_report(
            module="basketball_wnba",
            records_by_module={
                "basketball_wnba": [
                    {"home_score": 70, "away_score": 66, "final_result": "home"},
                    {"home_score": 73, "away_score": 60, "final_result": "home"},
                    {"home_score": 69, "away_score": 64, "final_result": "home"},
                ]
            },
        )
        row = self._feature(report, "basketball_wnba", "home_away_split")
        self.assertEqual(row["blocked_reason"], "missing_home_away_fields")

    def test_market_and_prediction_outcome_features_are_explicit(self):
        report = build_derived_feature_backfill_report(
            module="kalshi",
            records_by_module={
                "kalshi": [
                    {"provider": "kalshi", "ticker": "KXYES", "implied_probability": 0.57, "final_outcome": "yes"},
                    {"provider": "kalshi", "ticker": "KXNO", "implied_probability": 0.42, "final_outcome": "no"},
                ]
            },
        )
        self.assertTrue(self._feature(report, "kalshi", "market_implied_probability")["can_derive_now"])
        self.assertTrue(self._feature(report, "kalshi", "prediction_market_outcome")["can_derive_now"])

    def test_price_only_does_not_fabricate_prediction_market_outcome(self):
        report = build_derived_feature_backfill_report(
            module="polymarket",
            records_by_module={"polymarket": [{"provider": "polymarket", "market_id": "p1", "market_price_or_odds": 0.95}]},
        )
        self.assertTrue(self._feature(report, "polymarket", "market_implied_probability")["can_derive_now"])
        row = self._feature(report, "polymarket", "prediction_market_outcome")
        self.assertFalse(row["can_derive_now"])
        self.assertEqual(row["blocked_reason"], "missing_explicit_outcomes")

    def test_no_local_records_are_reported(self):
        report = build_derived_feature_backfill_report(
            module="baseball_mlb",
            records_by_module={},
        )
        row = self._feature(report, "baseball_mlb", "total_runs")
        self.assertEqual(row["blocked_reason"], "no_local_records_found")

    def test_safety_contract_and_no_secret_or_raw_payload_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_derived_feature_backfill_report(
                base_data_dir=tmp,
                module="kalshi",
                records_by_module={
                    "kalshi": [
                        {
                            "provider": "kalshi",
                            "ticker": "KX",
                            "implied_probability": 0.5,
                            "api_key": "do-not-leak",
                            "provider_payload": {"raw": "drop"},
                        }
                    ]
                },
            )
            paths = write_derived_feature_backfill_report(report, base_data_dir=tmp)
            rendered = Path(tmp, paths["latest_json_path"]).read_text(encoding="utf-8").lower()

        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["outcome_persistence_attempted"])
        self.assertFalse(report["import_or_persist_endpoint_called"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertNotIn("do-not-leak", rendered)
        self.assertNotIn("provider_payload", rendered)

    def test_report_exposes_nfl_feature_availability_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / "nflverse_snap_counts" / "latest.json"
            snap.parent.mkdir(parents=True, exist_ok=True)
            snap.write_text(
                json.dumps(
                    {
                        "fields_available": ["season", "week", "team", "player", "offense_snaps", "offense_pct"],
                        "records_validated": 500,
                        "seasons_backfilled": ["2023", "2024"],
                        "data_category": "snap_counts",
                    }
                ),
                encoding="utf-8",
            )
            report = build_derived_feature_backfill_report(base_data_dir=tmp)

        for key in (
            "nfl_play_by_play_efficiency_available",
            "nfl_pace_play_volume_available",
            "nfl_snap_usage_available",
            "nfl_participation_available",
            "nfl_depth_chart_available",
            "nfl_injury_availability_available",
            "nfl_roster_continuity_available",
            "nfl_nextgen_efficiency_available",
            "nfl_market_odds_available",
            "nfl_feature_builder_count",
            "nfl_feature_builder_blockers",
            "nfl_cutoff_sensitive_feature_count",
            "nfl_leakage_sensitive_feature_count",
        ):
            self.assertIn(key, report)
        self.assertTrue(report["nfl_snap_usage_available"])

    def test_report_exposes_exhaustion_coaching_cutoff_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_derived_feature_backfill_report(base_data_dir=tmp)
        for key in (
            "nfl_source_exhaustion_checked",
            "nfl_new_safe_sources_found",
            "nfl_redundant_sources_skipped",
            "nfl_blocked_sources",
            "nfl_coaching_data_available",
            "nfl_coaching_data_blocked_reason",
            "nfl_cutoff_week_features_available",
            "nfl_cutoff_week_feature_groups_available",
            "nfl_cutoff_week_leakage_guard_status",
            "nfl_cutoff_week_snapshot_count",
        ):
            self.assertIn(key, report)
        self.assertTrue(report["nfl_source_exhaustion_checked"])
        self.assertFalse(report["nfl_coaching_data_available"])

    def test_nfl_flags_default_when_records_provided(self):
        report = build_derived_feature_backfill_report(
            module="americanfootball_nfl",
            records_by_module={"americanfootball_nfl": [{"home_team": "A", "away_team": "B", "home_score": 1, "away_score": 0}]},
        )
        self.assertFalse(report["nfl_snap_usage_available"])
        self.assertEqual(report["nfl_feature_builder_count"], 0)

    def test_all_blocked_reasons_are_in_allowed_vocabulary(self):
        report = build_derived_feature_backfill_report(records_by_module={})
        reasons = {
            feature["blocked_reason"]
            for module in report["modules"]
            for feature in module["feature_rows"]
            if not feature["can_derive_now"]
        }
        self.assertTrue(reasons)
        self.assertTrue(reasons.issubset(ALLOWED_BLOCKED_REASONS))

    def test_normalized_shape_is_safe_and_compact(self):
        normalized = normalize_schedule_result_record(
            {
                "provider": "kalshi",
                "ticker": "KX",
                "home_score": 10,
                "away_score": 7,
                "api_secret": "do-not-leak",
                "provider_payload": {"raw": "drop"},
            },
            module="kalshi",
            data_source_path="test.json",
        )
        rendered = json.dumps(normalized, sort_keys=True).lower()
        self.assertEqual(normalized["final_margin"], 3.0)
        self.assertEqual(normalized["total_score"], 17.0)
        self.assertFalse(normalized["raw_payload_included"])
        self.assertNotIn("do-not-leak", rendered)
        self.assertNotIn("provider_payload", rendered)


if __name__ == "__main__":
    unittest.main()
