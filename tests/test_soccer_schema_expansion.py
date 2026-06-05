import tempfile
import unittest
from pathlib import Path

from automation_scheduler.soccer_schema_expansion import build_soccer_schema_expansion_report, write_soccer_schema_expansion_report


class TestSoccerSchemaExpansion(unittest.TestCase):
    def test_schema_expansion_builds_entries(self):
        report = build_soccer_schema_expansion_report(
            sample_verification_results={
                "source_result_index": {
                    "soccer::team_strength_ratings": {"validation_status": "sample_verified"},
                    "soccer::rest_travel_fixture_congestion": {"validation_status": "sample_verified"},
                }
            }
        )
        self.assertTrue(report["new_fields_created_count"] > 0)

    def test_writer_creates_files(self):
        report = {"new_fields_created_count": 1, "new_tables_created_count": 1, "new_fields_created": [{"field_name": "team_form_rating", "table": "soccer_team_strength_context", "validation_status": "sample_verified"}]}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_schema_expansion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
