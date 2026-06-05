import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_schema_expansion import build_nhl_schema_expansion_report, write_nhl_schema_expansion_report


SAMPLE_RESULTS = {
    "source_result_index": {
        "icehockey_nhl::shot_events": {"validation_status": "sample_verified", "source_url_hash": "hash-shot"},
        "icehockey_nhl::goalie_starts": {"validation_status": "sample_verified", "source_url_hash": "hash-goalie"},
    }
}


class TestNhlSchemaExpansion(unittest.TestCase):
    def test_schema_report_creates_fields(self):
        report = build_nhl_schema_expansion_report(sample_verification_results=SAMPLE_RESULTS)
        self.assertTrue(report["ok"])
        self.assertGreater(report["new_fields_created_count"], 0)

    def test_writer_creates_files(self):
        report = build_nhl_schema_expansion_report(sample_verification_results=SAMPLE_RESULTS)
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_schema_expansion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
