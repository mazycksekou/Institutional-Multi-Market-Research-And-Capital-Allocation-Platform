import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_open_data_field_catalog import (
    FEATURE_FAMILIES,
    build_nfl_open_data_field_catalog,
    write_nfl_open_data_field_catalog,
)


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
