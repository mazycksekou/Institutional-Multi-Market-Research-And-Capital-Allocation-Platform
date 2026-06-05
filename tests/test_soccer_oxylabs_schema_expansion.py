import tempfile
import unittest
from pathlib import Path

from automation_scheduler.soccer_oxylabs_schema_expansion import build_soccer_oxylabs_schema_expansion_report, write_soccer_oxylabs_schema_expansion_report


class TestSoccerOxylabsSchemaExpansion(unittest.TestCase):
    def test_oxylabs_schema_expansion_adds_transport(self):
        report = build_soccer_oxylabs_schema_expansion_report(
            sample_verification_results={"source_result_index": {"soccer::team_strength_ratings": {"validation_status": "sample_verified"}}},
            source_exhaustion_report={"source_candidate_rows": [{"lane_name": "team_strength_ratings", "source_url_hash": "hash", "oxylabs_transport_used": "both"}]},
            backfill_report={"backfill_rows": [{"lane_name": "team_strength_ratings", "source_url_hash": "hash", "oxylabs_transport_used": "residential_proxy"}]},
        )
        self.assertTrue(report["new_fields_created_count"] > 0)

    def test_writer_creates_files(self):
        report = {"new_fields_created_count": 1, "new_tables_created_count": 1, "new_fields_created": [{"field_name": "team_form_rating", "table": "soccer_team_strength_context", "validation_status": "sample_verified", "oxylabs_transport_used": "both"}]}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_oxylabs_schema_expansion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
