import tempfile
import unittest
from pathlib import Path

from automation_scheduler.remaining_field_closure import build_remaining_field_closure_report, write_remaining_field_closure_report


class TestRemainingFieldClosure(unittest.TestCase):
    def test_report_counts_match_current_gap_shape(self):
        report = build_remaining_field_closure_report()

        self.assertEqual(report["fields_closed_this_pass"], 161)
        self.assertEqual(report["fields_partially_closed_this_pass"], 33)
        self.assertEqual(report["new_remaining_incomplete_fields"], 112)
        self.assertEqual(len(report["field_closure_entries"]), 273)

    def test_report_writes_primary_and_alias_outputs(self):
        report = build_remaining_field_closure_report()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_remaining_field_closure_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())
            self.assertTrue(Path(paths["alias_json_path"]).exists())
            self.assertTrue(Path(paths["alias_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
