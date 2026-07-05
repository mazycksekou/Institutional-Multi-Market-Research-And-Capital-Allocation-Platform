import json
import tempfile
import unittest
from pathlib import Path

from src.services.streamlit_dashboard_facade import FEATURE_BUILDER_SPECS, build_expanded_feature_readiness, build_nfl_feature_builder_report, nfl_feature_availability_flags
from src.providers.nfl_open_data_feature_readiness import build_nfl_feature_readiness_report, write_nfl_feature_readiness_report


def _write_validated(base, source_id, *, fields, records=100, seasons=("2023", "2024")):
    path = Path(base) / "data_sources" / "nfl_open_data" / "validated" / source_id / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "fields_available": list(fields),
                "records_validated": records,
                "seasons_backfilled": list(seasons),
                "seasons_available": list(seasons),
                "data_category": source_id.replace("nflverse_", ""),
            }
        ),
        encoding="utf-8",
    )


def _full_data(base):
    _write_validated(base, "nflverse_pace_or_play_volume", fields=["game_id", "play_id", "posteam", "defteam", "epa"])
    _write_validated(base, "nflverse_play_by_play", fields=["play_id", "posteam", "yards_gained", "epa", "success", "interception", "fumble_lost"])
    _write_validated(base, "nflverse_snap_counts", fields=["season", "week", "team", "player", "offense_snaps", "offense_pct", "defense_snaps", "st_snaps"])
    _write_validated(base, "nflverse_participation", fields=["nflverse_game_id", "play_id", "offense_players", "offense_personnel"])
    _write_validated(base, "nflverse_weekly_rosters", fields=["season", "team", "gsis_id", "week", "position", "status"])
    _write_validated(base, "nflverse_injuries", fields=["season", "week", "team", "report_status", "practice_status"])
    _write_validated(base, "nflverse_depth_charts", fields=["season", "week", "team", "pos_rank", "depth_team", "pos_grp"])
    _write_validated(base, "nflverse_nextgen_stats", fields=["season", "player_gsis_id", "team_abbr", "avg_time_to_throw", "aggressiveness"])
    _write_validated(base, "nflverse_betting_lines_or_market_odds", fields=["game_id", "season", "spread_line", "total_line", "home_moneyline"])


class TestNflOpenDataFeatureBuilders(unittest.TestCase):
    def test_all_builders_available_when_fields_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        self.assertEqual(report["feature_builder_count"], len(FEATURE_BUILDER_SPECS))
        self.assertEqual(report["feature_builder_blocked_count"], 0)
        self.assertTrue(report["no_predictive_claim"])
        self.assertTrue(report["no_fabricated_values"])

    def test_feature_builders_include_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        for row in report["feature_builders"]:
            provenance = row["provenance"]
            self.assertIn("source_id", provenance)
            self.assertIn("source_fields_used", provenance)
            self.assertIn("seasons_supported", provenance)
            self.assertIn("granularity", provenance)
            self.assertIn("cutoff_required", provenance)
            self.assertIn("leakage_risk", provenance)

    def test_feature_builders_block_missing_source_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_validated(tmp, "nflverse_snap_counts", fields=["season", "week"])  # missing player/offense_snaps
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        snaps = [row for row in report["feature_builders"] if row["feature_name"] == "player_usage_snaps"][0]
        self.assertEqual(snaps["status"], "blocked")
        self.assertEqual(snaps["blocked_reason"], "missing_required_source_fields")
        self.assertTrue(snaps["provenance"]["missing_required_fields"])

    def test_builders_block_when_no_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_validated(tmp, "nflverse_injuries", fields=["season", "week", "team", "report_status"], records=0)
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        injuries = [row for row in report["feature_builders"] if row["feature_name"] == "injury_availability"][0]
        self.assertEqual(injuries["status"], "blocked")
        self.assertEqual(injuries["blocked_reason"], "no_validated_records_for_source")

    def test_no_future_data_and_no_postseason_target_as_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        for row in report["feature_builders"]:
            self.assertFalse(row["uses_future_data"])
            self.assertFalse(row["uses_postseason_target_label_as_feature"])
            self.assertFalse(row["allowed_for_postseason_target"])

    def test_all_builders_are_cutoff_required_and_leakage_aware(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        self.assertEqual(report["cutoff_sensitive_feature_count"], report["feature_builder_count"])
        self.assertEqual(report["leakage_sensitive_feature_count"], report["feature_builder_count"])

    def test_market_odds_availability_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            report = build_nfl_feature_builder_report(base_data_dir=tmp)
        self.assertTrue(report["feature_availability"]["nfl_market_odds_available"])

    def test_availability_flags_helper_exposes_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            flags = nfl_feature_availability_flags(base_data_dir=tmp)
        for key in (
            "nfl_play_by_play_efficiency_available",
            "nfl_snap_usage_available",
            "nfl_feature_builder_count",
            "nfl_cutoff_sensitive_feature_count",
            "nfl_leakage_sensitive_feature_count",
        ):
            self.assertIn(key, flags)
        self.assertTrue(flags["nfl_play_by_play_efficiency_available"])

    def test_expanded_readiness_lists_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            expanded = build_expanded_feature_readiness(base_data_dir=tmp)
        self.assertTrue(expanded["expanded_feature_catalog_available"])
        self.assertEqual(expanded["source_supported_feature_builder_count"], len(FEATURE_BUILDER_SPECS))
        self.assertIn("team_game_efficiency_candidates", expanded["expanded_feature_families_available"])
        self.assertTrue(expanded["no_predictive_claim"])

    def test_readiness_report_diffs_and_writes_without_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            report = build_nfl_feature_readiness_report(base_data_dir=tmp)
            paths = write_nfl_feature_readiness_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()
        self.assertTrue(latest_exists)
        self.assertIn("data_sources/nfl_open_data/feature_readiness/latest.json", paths["latest_json_path"])
        self.assertGreaterEqual(report["field_catalog_entries_after"], report["field_catalog_entries_before"])
        self.assertGreater(report["verified_fields_after"], 0)
        self.assertTrue(report["feature_builders_added"])
        self.assertTrue(report["no_predictive_claim"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["downloads_succeeded"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("authorization", rendered)

    def test_readiness_reports_no_new_fields_honestly_on_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            _full_data(tmp)
            first = build_nfl_feature_readiness_report(base_data_dir=tmp)
            write_nfl_feature_readiness_report(first, base_data_dir=tmp)
            from src.services.streamlit_dashboard_facade import build_nfl_open_data_field_catalog, write_nfl_open_data_field_catalog

            catalog = build_nfl_open_data_field_catalog(base_data_dir=tmp)
            write_nfl_open_data_field_catalog(catalog, base_data_dir=tmp)
            second = build_nfl_feature_readiness_report(base_data_dir=tmp)
        self.assertEqual(second["new_fields_discovered_count"], 0)


if __name__ == "__main__":
    unittest.main()
