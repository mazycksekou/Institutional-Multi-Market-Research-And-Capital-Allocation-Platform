import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_free_open_exhaustion import (
    build_nhl_manual_import_templates,
    write_nhl_manual_import_docs,
    write_nhl_manual_import_templates,
)


class TestNhlFreeOpenExhaustionHelpers(unittest.TestCase):
    def test_manual_templates_cover_unresolved_lanes(self):
        report = build_nhl_manual_import_templates(
            source_ledger={
                "source_ledger_rows": [
                    {"sport": "icehockey_nhl", "lane_name": "injuries_availability", "field_or_feature_group": "injuries", "entity_level": "player_game", "free_or_paid_category": "free_open_manual_import_needed", "final_reason": "manual", "candidate_source_name": "Team page", "license_or_terms_note": "manual"},
                    {"sport": "icehockey_nhl", "lane_name": "schedule_results", "field_or_feature_group": "schedule", "entity_level": "game", "free_or_paid_category": "free_open_populated", "final_reason": "", "candidate_source_name": "API", "license_or_terms_note": ""},
                ]
            },
            audit_report={"source_candidate_rows": [{"lane_name": "injuries_availability", "oxylabs_transport_used": "web_scraper_api", "oxylabs_calls_attempted": 1, "final_actionable_state": "manual_import_required"}]},
        )
        self.assertEqual(report["template_count"], 1)

    def test_template_and_docs_writers_create_files(self):
        report = {
            "template_rows": [
                {
                    "sport": "icehockey_nhl",
                    "field_name": "injuries",
                    "lane_name": "injuries_availability",
                    "exact_reason_automation_failed": "manual",
                    "oxylabs_attempts_summary": "transport=web_scraper_api",
                    "required_columns": "sport,lane_name",
                    "example_row": "icehockey_nhl,injuries_availability",
                    "validation_rules": "rule",
                    "cutoff_safe_requirement": "rule",
                    "source_required": "true",
                    "source_url_hash_required": "true",
                    "paid_source_recommended": "",
                    "notes": "note",
                }
            ],
            "template_count": 1,
        }
        with tempfile.TemporaryDirectory() as tmp:
            template_paths = write_nhl_manual_import_templates(report, output_dir=Path(tmp) / "data")
            docs_paths = write_nhl_manual_import_docs(report, docs_dir=Path(tmp) / "docs")
            self.assertTrue(Path(template_paths["template_path"]).exists())
            self.assertTrue(Path(docs_paths["manual_import_docs_path"]).exists())


if __name__ == "__main__":
    unittest.main()
