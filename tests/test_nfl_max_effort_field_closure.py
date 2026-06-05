import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_max_effort_field_closure import build_nfl_max_effort_field_closure_report, write_nfl_max_effort_field_closure_report


class TestNflMaxEffortFieldClosure(unittest.TestCase):
    def test_nfl_closure_counts_match_current_state(self):
        report = build_nfl_max_effort_field_closure_report()

        self.assertEqual(len(report["field_closure_entries"]), 17)
        self.assertEqual(report["fields_closed_this_pass"], 0)
        self.assertEqual(report["fields_partially_closed_this_pass"], 0)
        self.assertEqual(report["new_remaining_incomplete_fields"], 17)

    def test_nfl_closure_writes_report_files(self):
        report = build_nfl_max_effort_field_closure_report()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nfl_max_effort_field_closure_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
