import tempfile
import unittest
from pathlib import Path

from automation_scheduler.schema_expansion_v2 import build_nfl_mlb_schema_expansion_report, build_schema_expansion_v2, write_nfl_mlb_schema_expansion_report, write_schema_expansion_v2


class TestSchemaExpansionV2(unittest.TestCase):
    def test_schema_expansion_reports_expose_expected_counts(self):
        report = build_schema_expansion_v2()
        combined = build_nfl_mlb_schema_expansion_report()

        self.assertEqual(report["new_fields_created_count"], 8)
        self.assertEqual(report["new_tables_created_count"], 4)
        self.assertEqual(len(report["new_fields_created"]), 8)
        self.assertEqual(
            set(report["model_eligible_features_added"]),
            {
                "coaching_staff_role_history",
                "staff_turnover_severity",
                "official_assignment_tendency",
                "stadium_surface_roof_state",
                "manager_coach_role_history",
                "draft_pick_origin",
                "umpire_assignment_tendency",
            },
        )
        self.assertEqual(combined["nfl_schema_expansion"]["new_fields_created_count"], 4)
        self.assertEqual(combined["mlb_schema_expansion"]["new_fields_created_count"], 4)
        self.assertEqual(combined["nfl_schema_expansion"]["new_tables_created_count"], 2)
        self.assertEqual(combined["mlb_schema_expansion"]["new_tables_created_count"], 2)

    def test_schema_expansion_reports_write_expected_files(self):
        report = build_schema_expansion_v2()
        combined = build_nfl_mlb_schema_expansion_report()
        with tempfile.TemporaryDirectory() as tmp:
            report_paths = write_schema_expansion_v2(report, output_dir=Path(tmp) / "reports")
            combined_paths = write_nfl_mlb_schema_expansion_report(combined, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(report_paths["latest_json_path"]).exists())
            self.assertTrue(Path(report_paths["latest_markdown_path"]).exists())
            self.assertTrue(Path(combined_paths["latest_json_path"]).exists())
            self.assertTrue(Path(combined_paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
