import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_open_data_field_catalog import (
    FEATURE_FAMILIES,
    build_existing_mlb_field_index,
    build_mlb_open_data_field_catalog,
    compare_candidate_fields_to_existing_catalog,
    write_mlb_open_data_field_catalog,
)


def _seed_latest(base, source_id, *, fields, seasons=("2024",)):
    path = Path(base) / "data_sources" / "mlb_open_data" / "validated" / source_id / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "records_validated": 10,
                "fields_available": list(fields),
                "field_types": {field: "string" for field in fields},
                "seasons_available": list(seasons),
                "seasons_backfilled": list(seasons),
            }
        ),
        encoding="utf-8",
    )


class TestMlbOpenDataFieldCatalog(unittest.TestCase):
    def test_unverified_fields_are_research_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_mlb_open_data_field_catalog(base_data_dir=tmp)
        self.assertGreater(report["field_entries_created"], 0)
        unverified = [entry for entry in report["entries"] if entry["source_status"] == "unverified"]
        self.assertTrue(unverified)
        self.assertTrue(all(entry["implementation_status"] == "research_required" for entry in unverified))

    def test_verified_latest_fields_become_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(tmp, "batting_stats_lahman", fields=["playerID", "yearID", "AB", "H", "HR", "BB", "SO"])
            report = build_mlb_open_data_field_catalog(base_data_dir=tmp)
        entries = [entry for entry in report["entries"] if entry["source_id"] == "batting_stats_lahman"]
        self.assertTrue(any(entry["field_name"] == "AB" and entry["implementation_status"] == "available" for entry in entries))
        self.assertTrue(all(entry["model_feature_family"] == "batting_profile" for entry in entries if entry["field_name"] == "AB"))

    def test_catalog_maps_fields_to_feature_families_and_leakage(self):
        report = build_mlb_open_data_field_catalog()
        families = {entry["model_feature_family"] for entry in report["entries"]}
        self.assertTrue(families.issubset(set(FEATURE_FAMILIES)))
        market_entries = [entry for entry in report["entries"] if entry["model_feature_family"] == "market_odds"]
        self.assertTrue(market_entries)
        self.assertTrue(all(entry["requires_season_cutoff"] for entry in market_entries))
        self.assertTrue(all(entry["target_leakage_safe"] is False for entry in market_entries))

    def test_candidate_field_novelty_uses_existing_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = build_existing_mlb_field_index(base_data_dir=tmp)
            rows = compare_candidate_fields_to_existing_catalog(
                [
                    {"field_name": "game_id", "join_key": True, "new_entity_coverage": False},
                    {"field_name": "fresh_metric", "new_entity_coverage": True},
                ],
                base_data_dir=tmp,
                existing_index=index,
            )
        exact = [row for row in rows if row["field_name"] == "game_id"][0]
        fresh = [row for row in rows if row["field_name"] == "fresh_metric"][0]
        self.assertEqual(exact["novelty"], "exact_duplicate")
        self.assertFalse(exact["ingestible"])
        self.assertEqual(fresh["novelty"], "new_entity_coverage")
        self.assertTrue(fresh["ingestible"])

    def test_catalog_writes_latest_and_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_mlb_open_data_field_catalog(base_data_dir=tmp)
            paths = write_mlb_open_data_field_catalog(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            rendered = latest.read_text(encoding="utf-8").lower()
            self.assertTrue(latest.exists())

        self.assertIn("data_sources/mlb_open_data/field_catalog/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/mlb_open_data/field_catalog/items/", paths["item_json_path"])
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("do-not-leak", rendered)


if __name__ == "__main__":
    unittest.main()
