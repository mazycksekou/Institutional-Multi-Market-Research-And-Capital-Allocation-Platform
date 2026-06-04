import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_open_data_backfill import (
    build_mlb_open_data_backfill_report,
    build_mlb_open_data_coverage_matrix,
    write_mlb_open_data_backfill_report,
)
from automation_scheduler.mlb_open_data_sources import BLOCKED_FEATURE_FAMILIES, REQUIRED_DATA_CATEGORIES


def _seed_latest(base, source_id, *, fields, records=100, seasons=("2024", "2025"), status="full_backfill_complete", gate="full_available_backfill"):
    path = Path(base) / "data_sources" / "mlb_open_data" / "validated" / source_id / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "status": status,
                "gate": gate,
                "records_validated": records,
                "records_rejected": 0,
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


class TestMlbOpenDataBackfill(unittest.TestCase):
    def test_coverage_matrix_includes_every_required_category_and_blocked_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_mlb_open_data_coverage_matrix(base_data_dir=tmp)
        categories = {row["data_category"] for row in report["coverage_rows"]}
        self.assertTrue(set(REQUIRED_DATA_CATEGORIES).issubset(categories))
        self.assertTrue(set(BLOCKED_FEATURE_FAMILIES).issubset(set(report["feature_families_still_blocked"])))
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])

    def test_coverage_matrix_reflects_validated_latest_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(
                tmp,
                "team_stats_lahman",
                fields=["yearID", "teamID", "R", "RA"],
                records=20,
                seasons=("2023", "2024"),
            )
            report = build_mlb_open_data_coverage_matrix(base_data_dir=tmp)
            row = {item["source_id"]: item for item in report["coverage_rows"]}["team_stats_lahman"]

        self.assertEqual(row["records_validated"], 20)
        self.assertEqual(row["full_backfill_status"], "succeeded")
        self.assertTrue(report["feature_availability"]["mlb_team_game_run_profile_available"])

    def test_metadata_only_check_does_not_download(self):
        report = build_mlb_open_data_backfill_report(source_id="team_stats_lahman", mode="metadata_check")
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertTrue(report["ok"])

    def test_backfill_report_writes_session_and_coverage_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = build_mlb_open_data_backfill_report(
                source_id="team_stats_lahman",
                mode="metadata_check",
                base_data_dir=tmp,
            )
            session_paths = write_mlb_open_data_backfill_report(session, base_data_dir=tmp)
            coverage = build_mlb_open_data_backfill_report(mode="coverage_report", base_data_dir=tmp)
            coverage_paths = write_mlb_open_data_backfill_report(coverage, base_data_dir=tmp)

        self.assertIn("data_sources/mlb_open_data/backfill_sessions/latest.json", session_paths["session_latest_json_path"])
        self.assertIn("data_sources/mlb_open_data/coverage_matrix/latest.json", coverage_paths["coverage_latest_json_path"])
        self.assertIn("data_sources/mlb_open_data/coverage_matrix/items/", coverage_paths["coverage_item_json_path"])


if __name__ == "__main__":
    unittest.main()
