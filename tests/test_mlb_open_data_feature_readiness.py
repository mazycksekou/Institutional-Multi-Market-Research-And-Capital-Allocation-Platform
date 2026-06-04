import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.derived_feature_backfill_report import build_derived_feature_backfill_report
from automation_scheduler.mlb_open_data_feature_readiness import (
    build_mlb_feature_readiness_report,
    write_mlb_feature_readiness_report,
)


def _seed_latest(base, source_id, *, fields, records=50, seasons=("2024", "2025")):
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


class TestMlbOpenDataFeatureReadiness(unittest.TestCase):
    def test_readiness_report_tracks_new_fields_and_support_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(tmp, "team_stats_lahman", fields=["yearID", "teamID", "R", "RA"])
            _seed_latest(tmp, "batting_stats_lahman", fields=["playerID", "yearID", "AB", "H", "HR", "BB", "SO"])
            _seed_latest(tmp, "pitching_stats_lahman", fields=["playerID", "yearID", "ERA", "G", "GS", "IPouts"])
            _seed_latest(tmp, "rosters_mlb_stats_api", fields=["team_id", "player_id", "season", "status"])
            _seed_latest(tmp, "people_identifiers_chadwick", fields=["key_mlbam", "key_retro", "key_bbref"])
            report = build_mlb_feature_readiness_report(base_data_dir=tmp)
            paths = write_mlb_feature_readiness_report(report, base_data_dir=tmp)

        self.assertGreater(report["new_fields_discovered_count"], 0)
        self.assertTrue(report["feature_builders_added"])
        self.assertIn("mlb_new_safe_sources_found", report["source_exhaustion"])
        self.assertIn("structured_seed_sources_used", report["structured_seed_summary"])
        self.assertIn("mlb_cutoff_date_features_available", report["cutoff_feature_availability"])
        self.assertIn("data_sources/mlb_open_data/feature_readiness/latest.json", paths["latest_json_path"])
        self.assertTrue(report["no_predictive_claim"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_derived_feature_report_exposes_mlb_readiness_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(tmp, "team_stats_lahman", fields=["yearID", "teamID", "R", "RA"])
            report = build_derived_feature_backfill_report(base_data_dir=tmp, module="baseball_mlb")
        self.assertIn("mlb_open_data_feature_availability", report)
        self.assertIn("mlb_open_data_feature_readiness", report)
        self.assertIn("mlb_pattern_readiness_available", report)
        self.assertIn("mlb_source_exhaustion_checked", report)


if __name__ == "__main__":
    unittest.main()
