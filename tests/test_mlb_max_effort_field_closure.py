import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_max_effort_field_closure import build_mlb_max_effort_field_closure_report, write_mlb_max_effort_field_closure_report


class TestMlbMaxEffortFieldClosure(unittest.TestCase):
    def test_mlb_closure_counts_match_current_state(self):
        report = build_mlb_max_effort_field_closure_report()

        self.assertEqual(len(report["field_closure_entries"]), 256)
        self.assertEqual(report["fields_closed_this_pass"], 161)
        self.assertEqual(report["fields_partially_closed_this_pass"], 33)
        self.assertEqual(report["new_remaining_incomplete_fields"], 95)

    def test_mlb_closure_writes_report_files(self):
        report = build_mlb_max_effort_field_closure_report()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_mlb_max_effort_field_closure_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
