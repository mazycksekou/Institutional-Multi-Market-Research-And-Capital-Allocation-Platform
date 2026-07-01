import csv
import tempfile
import unittest
from pathlib import Path

from src.providers.nfl_coaching_adapters import ManualCsvCoachingImportAdapter
from src.services.streamlit_dashboard_facade import coaching_source_by_id
from src.market_intelligence.nfl_coaching_feature_builders import COACHING_FEATURE_BUILDERS, build_coordinator_continuity_candidates, build_nfl_coaching_feature_report, build_nfl_coaching_acquisition_report, build_nfl_coaching_features, write_nfl_coaching_acquisition_report


def _seed_rows(tmp, rows):
    path = Path(tmp) / "manual_imports" / "nfl_coaching" / "seed.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    adapter = ManualCsvCoachingImportAdapter(coaching_source_by_id("manual_csv_import"))
    adapter.run_manual_import(allow_manual_import=True, persist_preview=True, base_data_dir=tmp)


class TestNflCoachingFeatureBuilders(unittest.TestCase):
    def test_no_records_blocks_all_builders(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_coaching_feature_report(base_data_dir=tmp)
        self.assertEqual(report["coaching_records_loaded"], 0)
        self.assertEqual(report["coaching_feature_builders_available"], [])
        blockers = {row["blocked_reason"] for row in report["coaching_feature_builder_blockers"]}
        self.assertEqual(blockers, {"no_coaching_records_available"})

    def test_feature_builders_include_provenance(self):
        rows = [
            {"team": "KC", "season": "2023", "staff_name": "Andy Reid", "staff_role": "Head Coach", "source_label": "m", "source_license": "CC0"},
            {"team": "KC", "season": "2024", "staff_name": "Andy Reid", "staff_role": "Head Coach", "source_label": "m", "source_license": "CC0"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            _seed_rows(tmp, rows)
            report = build_nfl_coaching_feature_report(base_data_dir=tmp)
        for feature in report["feature_builders"]:
            provenance = feature["provenance"]
            for key in ("source_id", "source_fields_used", "seasons_supported", "teams_supported", "granularity", "cutoff_required", "leakage_risk"):
                self.assertIn(key, provenance)
            self.assertIn("confidence", feature)
        self.assertIn("head_coach_by_team_season", report["coaching_feature_builders_available"])
        self.assertIn("coaching_continuity_candidates", report["coaching_feature_builders_available"])

    def test_coordinator_continuity_blocks_if_adjacent_season_missing(self):
        rows = [
            {"team": "KC", "season": "2024", "staff_name": "Steve Spagnuolo", "staff_role": "Defensive Coordinator", "source_label": "m", "source_license": "CC0"},
        ]
        feature = build_coordinator_continuity_candidates(
            [{"team": "KC", "season": "2024", "staff_name": "Steve Spagnuolo", "role_group": "defensive_coordinator"}]
        )
        self.assertEqual(feature["status"], "blocked")
        self.assertEqual(feature["blocked_reason"], "adjacent_season_missing")

    def test_coordinator_continuity_available_with_adjacent_seasons(self):
        rows = [
            {"team": "KC", "season": "2023", "staff_name": "Steve Spagnuolo", "role_group": "defensive_coordinator"},
            {"team": "KC", "season": "2024", "staff_name": "Steve Spagnuolo", "role_group": "defensive_coordinator"},
        ]
        feature = build_coordinator_continuity_candidates(rows)
        self.assertEqual(feature["status"], "available")
        self.assertEqual(feature["values"]["adjacent_season_pairs_evaluated"], 1)
        self.assertEqual(feature["values"]["continuous_pairs"], 1)

    def test_unknown_role_not_used_for_coordinator_continuity(self):
        rows = [
            {"team": "KC", "season": "2023", "staff_name": "X", "role_group": "unknown"},
            {"team": "KC", "season": "2024", "staff_name": "X", "role_group": "unknown"},
        ]
        feature = build_coordinator_continuity_candidates(rows)
        self.assertEqual(feature["status"], "blocked")
        self.assertEqual(feature["blocked_reason"], "no_eligible_role_rows")

    def test_all_feature_builders_are_named(self):
        features = build_nfl_coaching_features([])
        names = {row["feature_name"] for row in features}
        self.assertEqual(names, set(COACHING_FEATURE_BUILDERS))

    def test_feature_builders_activate_from_wikidata_seed(self):
        from src.services.streamlit_dashboard_facade import adapter_by_id

        def fake(query):
            return {
                "results": {
                    "bindings": [
                        {"teamLabel": {"value": "KC"}, "coachLabel": {"value": "Andy Reid"}, "start": {"value": "+2013-09-08T00:00:00Z"}, "end": {"value": "+2014-09-01T00:00:00Z"}},
                    ]
                }
            }

        with tempfile.TemporaryDirectory() as tmp:
            adapter = adapter_by_id("wikidata_coaching_seed")
            adapter.run_structured_seed_import(allow_structured_seed=True, persist_preview=True, fetch_fn=fake, base_data_dir=tmp)
            report = build_nfl_coaching_feature_report(base_data_dir=tmp)
        self.assertGreater(report["coaching_records_loaded"], 0)
        self.assertIn("head_coach_by_team_season", report["coaching_feature_builders_available"])
        self.assertIn("coaching_continuity_candidates", report["coaching_feature_builders_available"])

    def test_acquisition_report_writes_safely(self):
        rows = [
            {"team": "KC", "season": "2024", "staff_name": "Andy Reid", "staff_role": "Head Coach", "source_label": "m", "source_license": "CC0"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            _seed_rows(tmp, rows)
            report = build_nfl_coaching_acquisition_report(allow_manual_import=True, base_data_dir=tmp)
            paths = write_nfl_coaching_acquisition_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            coverage = Path(tmp, paths["coverage_latest_json_path"])
            latest_exists = latest.exists()
            coverage_exists = coverage.exists()
            rendered = latest.read_text(encoding="utf-8").lower()
        self.assertTrue(latest_exists)
        self.assertTrue(coverage_exists)
        self.assertEqual(report["sources_checked"], 13)
        self.assertFalse(report["spoofing_used"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_payload", rendered)


if __name__ == "__main__":
    unittest.main()
