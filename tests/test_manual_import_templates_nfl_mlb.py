import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.remaining_field_closure import build_remaining_manual_templates, write_remaining_manual_templates


class TestManualImportTemplatesNflMlb(unittest.TestCase):
    def test_build_templates_counts_match_current_gap_shape(self):
        report = build_remaining_manual_templates()

        self.assertEqual(report["nfl_template_count"], 10)
        self.assertEqual(report["mlb_template_count"], 160)
        self.assertEqual(len(report["nfl_templates"]), 10)
        self.assertEqual(len(report["mlb_templates"]), 160)

    def test_write_templates_creates_csv_files(self):
        report = build_remaining_manual_templates()
        with tempfile.TemporaryDirectory() as tmp:
            template_root = Path(tmp) / "manual_import_templates"
            with patch("automation_scheduler.max_effort_source_discovery._manual_template_root", return_value=template_root):
                paths = write_remaining_manual_templates(report)
                nfl_path = Path(paths["nfl_template_path"])
                mlb_path = Path(paths["mlb_template_path"])
                with nfl_path.open(encoding="utf-8", newline="") as handle:
                    nfl_rows = list(csv.reader(handle))
                with mlb_path.open(encoding="utf-8", newline="") as handle:
                    mlb_rows = list(csv.reader(handle))

                self.assertTrue(nfl_path.exists())
                self.assertTrue(mlb_path.exists())
                self.assertEqual(len(nfl_rows), report["nfl_template_count"] + 1)
                self.assertEqual(len(mlb_rows), report["mlb_template_count"] + 1)
                self.assertEqual(nfl_rows[0], [
                    "sport",
                    "field_name",
                    "entity_level",
                    "required_columns",
                    "example_row",
                    "validation_rules",
                    "cutoff_safe_requirement",
                    "source_required",
                    "source_url_hash_required",
                    "notes",
                ])


if __name__ == "__main__":
    unittest.main()
