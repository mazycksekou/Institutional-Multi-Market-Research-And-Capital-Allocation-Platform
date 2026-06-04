import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_open_data_feature_builders import (
    FEATURE_BUILDER_SPECS,
    build_expanded_feature_readiness,
    build_mlb_feature_availability_flags,
    build_mlb_feature_builder_report,
)


def _seed_latest(base, source_id, *, fields, records=100, seasons=("2024", "2025")):
    path = Path(base) / "data_sources" / "mlb_open_data" / "validated" / source_id / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "records_validated": records,
                "fields_available": list(fields),
                "field_types": {field: "string" for field in fields},
                "seasons_available": list(seasons),
                "seasons_backfilled": list(seasons),
                "sample_rows": [{field: f"{field}-value" for field in fields}],
                "validated_rows": [{field: f"{field}-value" for field in fields}],
            }
        ),
        encoding="utf-8",
    )


def _seed_full_data(base):
    _seed_latest(base, "team_stats_lahman", fields=["yearID", "teamID", "R", "RA", "W", "L"])
    _seed_latest(base, "batting_stats_lahman", fields=["playerID", "yearID", "AB", "H", "HR", "BB", "SO"])
    _seed_latest(base, "pitching_stats_lahman", fields=["playerID", "yearID", "ERA", "G", "GS", "IPouts"])
    _seed_latest(base, "fielding_stats_lahman", fields=["playerID", "yearID", "teamID", "pos", "PO", "A", "E"])
    _seed_latest(base, "bullpen_usage_mlb_stats_api", fields=["game_pk", "team_id", "player_id", "pitch_count", "innings_pitched"])
    _seed_latest(base, "starting_pitchers_mlb_stats_api", fields=["game_pk", "team_id", "player_id", "start_flag", "innings_pitched"])
    _seed_latest(base, "rosters_mlb_stats_api", fields=["team_id", "player_id", "season", "status"])
    _seed_latest(base, "lineups_mlb_stats_api", fields=["game_pk", "team_id", "player_id", "batting_order"])
    _seed_latest(base, "injuries_mlb_stats_api", fields=["player_id", "team_id", "report_date", "status"])
    _seed_latest(base, "park_factors_lahman", fields=["park_id", "yearID", "runs_factor"])
    _seed_latest(base, "weather_mlb_stats_api", fields=["game_pk", "game_date", "temperature", "wind_speed"])
    _seed_latest(base, "postseason_labels_retrosheet", fields=["game_id", "season", "game_type"])
    _seed_latest(base, "managers_coaches_mlb_stats_api", fields=["team_id", "season", "manager_name"])
    _seed_latest(base, "franchises_lahman", fields=["franchID", "team_name"])
    _seed_latest(base, "people_identifiers_chadwick", fields=["key_mlbam", "key_retro", "key_bbref"])
    _seed_latest(base, "pitch_by_pitch_research_lane", fields=["game_pk", "pitch_number", "pitcher", "batter"])
    _seed_latest(base, "statcast_batted_ball_research_lane", fields=["game_pk", "pitch_number", "batter", "launch_speed"])
    _seed_latest(base, "market_odds_blocked", fields=["game_id", "date", "moneyline", "spread_line", "total_line"])


class TestMlbOpenDataFeatureBuilders(unittest.TestCase):
    def test_feature_builders_include_provenance_and_blocked_lanes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_full_data(tmp)
            report = build_mlb_feature_builder_report(base_data_dir=tmp)
        self.assertEqual(report["feature_builder_count"], len([row for row in report["feature_builders"] if row["status"] == "available"]))
        self.assertGreater(report["feature_builder_count"], 0)
        self.assertGreater(report["feature_builder_blocked_count"], 0)
        self.assertTrue(report["no_predictive_claim"])
        self.assertTrue(report["no_fabricated_values"])

        for row in report["feature_builders"]:
            provenance = row["provenance"]
            self.assertIn("source_id", provenance)
            self.assertIn("source_fields_used", provenance)
            self.assertIn("seasons_supported", provenance)
            self.assertIn("granularity", provenance)
            self.assertIn("cutoff_required", provenance)
            self.assertIn("leakage_risk", provenance)

        blocked = {row["feature_name"]: row for row in report["feature_builders_blocked"]}
        self.assertIn("market_odds_candidates", blocked)
        self.assertIn("pitch_quality_candidates", blocked)
        self.assertIn("batted_ball_quality_candidates", blocked)

    def test_feature_builders_block_when_required_fields_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(tmp, "rosters_mlb_stats_api", fields=["team_id", "player_id", "season"])  # missing status
            report = build_mlb_feature_builder_report(base_data_dir=tmp)
        roster = [row for row in report["feature_builders"] if row["feature_name"] == "roster_continuity"][0]
        self.assertEqual(roster["status"], "blocked")
        self.assertEqual(roster["blocked_reason"], "missing_required_source_fields")
        self.assertTrue(roster["provenance"]["missing_required_fields"])

    def test_availability_flags_helper_exposes_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_full_data(tmp)
            flags = build_mlb_feature_availability_flags(base_data_dir=tmp)
        for key in (
            "mlb_team_game_run_profile_available",
            "mlb_batting_profile_available",
            "mlb_feature_builder_count",
            "mlb_cutoff_sensitive_feature_count",
            "mlb_leakage_sensitive_feature_count",
        ):
            self.assertIn(key, flags)
        self.assertTrue(flags["mlb_team_game_run_profile_available"])
        self.assertGreater(flags["mlb_feature_builder_count"], 0)

    def test_expanded_readiness_lists_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_full_data(tmp)
            expanded = build_expanded_feature_readiness(base_data_dir=tmp)
        self.assertTrue(expanded["expanded_feature_catalog_available"])
        self.assertIn("team_game_run_profile", expanded["expanded_feature_families_available"])
        self.assertTrue(expanded["structured_seed_available"])


if __name__ == "__main__":
    unittest.main()
