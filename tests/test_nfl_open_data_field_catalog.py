import json
import tempfile
import unittest
from pathlib import Path

from src.services.streamlit_dashboard_facade import FEATURE_FAMILIES, build_nfl_open_data_field_catalog, write_nfl_open_data_field_catalog


class TestNflOpenDataFieldCatalog(unittest.TestCase):
    def test_unverified_fields_are_research_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_open_data_field_catalog(base_data_dir=tmp)
        self.assertGreater(report["field_entries_created"], 0)
        unverified = [entry for entry in report["entries"] if entry["source_status"] == "unverified"]
        self.assertTrue(unverified)
        self.assertTrue(all(entry["implementation_status"] == "research_required" for entry in unverified))
        self.assertTrue(all(entry["current_phase_allowed"] is False for entry in unverified))

    def test_catalog_maps_fields_to_feature_families_and_leakage(self):
        report = build_nfl_open_data_field_catalog()
        families = {entry["model_feature_family"] for entry in report["entries"]}
        self.assertTrue(families.issubset(set(FEATURE_FAMILIES)))
        market_entries = [entry for entry in report["entries"] if entry["model_feature_family"] == "market_odds"]
        self.assertTrue(market_entries)
        self.assertTrue(all(entry["requires_season_cutoff"] for entry in market_entries))
        self.assertTrue(all(entry["target_leakage_safe"] is False for entry in market_entries))

    def test_verified_latest_fields_become_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / "nflverse_schedules_results" / "latest.json"
            latest.parent.mkdir(parents=True)
            latest.write_text(
                json.dumps(
                    {
                        "fields_available": ["game_id", "season", "home_score"],
                        "field_types": {"game_id": "string", "season": "integer", "home_score": "integer"},
                        "seasons_available": ["2024"],
                    }
                ),
                encoding="utf-8",
            )
            report = build_nfl_open_data_field_catalog(base_data_dir=tmp)
            entries = [entry for entry in report["entries"] if entry["source_id"] == "nflverse_schedules_results"]

        self.assertTrue(any(entry["field_name"] == "game_id" and entry["implementation_status"] == "available" for entry in entries))
        self.assertTrue(any(entry["field_name"] == "home_score" and entry["leakage_risk"] != "low" for entry in entries))

    def _seed_lane(self, tmp, source_id, fields, *, seasons=("2023", "2024")):
        latest = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / source_id / "latest.json"
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(
            json.dumps(
                {
                    "fields_available": list(fields),
                    "field_types": {field: "number" for field in fields},
                    "seasons_available": list(seasons),
                }
            ),
            encoding="utf-8",
        )

    def _entries_for(self, report, source_id):
        return {entry["field_name"]: entry for entry in report["entries"] if entry["source_id"] == source_id}

    def test_reseed_classifies_every_completed_feature_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._seed_lane(tmp, "nflverse_snap_counts", ["season", "week", "team", "player", "offense_pct", "defense_snaps"])
            self._seed_lane(tmp, "nflverse_participation", ["nflverse_game_id", "play_id", "offense_personnel", "defense_personnel"])
            self._seed_lane(tmp, "nflverse_depth_charts", ["season", "week", "team", "pos_rank", "pos_grp"])
            self._seed_lane(tmp, "nflverse_injuries", ["season", "week", "team", "report_status", "practice_status"])
            self._seed_lane(tmp, "nflverse_weekly_rosters", ["season", "team", "gsis_id", "status"])
            self._seed_lane(tmp, "nflverse_nextgen_stats", ["season", "player_gsis_id", "team_abbr", "avg_time_to_throw"])
            self._seed_lane(tmp, "nflverse_play_by_play", ["play_id", "posteam", "yards_gained", "epa"])
            report = build_nfl_open_data_field_catalog(base_data_dir=tmp)

        snap = self._entries_for(report, "nflverse_snap_counts")
        self.assertEqual(snap["offense_pct"]["model_feature_family"], "player_availability")
        self.assertTrue(snap["offense_pct"]["cutoff_required"])
        self.assertFalse(snap["offense_pct"]["validation_feature_candidate"])
        self.assertFalse(snap["offense_pct"]["allowed_for_regular_season_snapshot"])

        part = self._entries_for(report, "nflverse_participation")
        self.assertEqual(part["offense_personnel"]["model_feature_family"], "player_availability")
        self.assertTrue(part["offense_personnel"]["cutoff_required"])

        depth = self._entries_for(report, "nflverse_depth_charts")
        self.assertEqual(depth["pos_rank"]["model_feature_family"], "depth_chart")
        self.assertTrue(depth["pos_rank"]["cutoff_required"])
        self.assertFalse(depth["pos_rank"]["validation_feature_candidate"])

        inj = self._entries_for(report, "nflverse_injuries")
        self.assertEqual(inj["report_status"]["model_feature_family"], "injury_lineup")
        self.assertTrue(inj["report_status"]["cutoff_required"])
        self.assertFalse(inj["report_status"]["validation_feature_candidate"])

        roster = self._entries_for(report, "nflverse_weekly_rosters")
        self.assertEqual(roster["status"]["model_feature_family"], "roster_continuity")
        self.assertTrue(roster["status"]["cutoff_required"])

        ngs = self._entries_for(report, "nflverse_nextgen_stats")
        self.assertEqual(ngs["avg_time_to_throw"]["model_feature_family"], "play_by_play_efficiency")
        self.assertTrue(ngs["avg_time_to_throw"]["cutoff_required"])

        pbp = self._entries_for(report, "nflverse_play_by_play")
        self.assertEqual(pbp["epa"]["model_feature_family"], "play_by_play_efficiency")
        self.assertTrue(pbp["epa"]["cutoff_required"])
        self.assertTrue(pbp["epa"]["allowed_for_regular_season_snapshot"])
        self.assertTrue(pbp["epa"]["derived_feature_candidate"])

    def test_structural_join_keys_are_leakage_safe_but_not_feature_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._seed_lane(tmp, "nflverse_snap_counts", ["season", "week", "team", "player", "offense_pct"])
            report = build_nfl_open_data_field_catalog(base_data_dir=tmp)
        snap = self._entries_for(report, "nflverse_snap_counts")
        self.assertTrue(snap["season"]["structural_or_join_key"])
        self.assertTrue(snap["season"]["target_leakage_safe"])
        self.assertFalse(snap["season"]["cutoff_required"])
        self.assertFalse(snap["season"]["validation_feature_candidate"])
        self.assertFalse(snap["season"]["pattern_feature_candidate"])

    def test_market_odds_fields_are_cutoff_sensitive_not_validation_candidates(self):
        report = build_nfl_open_data_field_catalog()
        market = [entry for entry in report["entries"] if entry["model_feature_family"] == "market_odds"]
        self.assertTrue(market)
        self.assertTrue(all(entry["cutoff_required"] for entry in market))
        self.assertTrue(all(entry["validation_feature_candidate"] is False for entry in market))
        self.assertTrue(all(entry["allowed_for_regular_season_snapshot"] is False for entry in market))

    def test_catalog_summary_counts_present(self):
        report = build_nfl_open_data_field_catalog()
        for key in (
            "verified_field_count",
            "cutoff_sensitive_field_count",
            "leakage_sensitive_field_count",
            "fields_by_feature_family",
            "join_keys",
        ):
            self.assertIn(key, report)

    def test_catalog_writes_latest_and_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_open_data_field_catalog(base_data_dir=tmp)
            paths = write_nfl_open_data_field_catalog(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            rendered = latest.read_text(encoding="utf-8").lower()
            self.assertTrue(latest.exists())

        self.assertIn("data_sources/nfl_open_data/field_catalog/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/nfl_open_data/field_catalog/items/", paths["item_json_path"])
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("do-not-leak", rendered)


if __name__ == "__main__":
    unittest.main()
