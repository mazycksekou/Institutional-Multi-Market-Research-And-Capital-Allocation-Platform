import tempfile
import unittest
from pathlib import Path

from automation_scheduler.basketball_oxylabs_schema_expansion import (
    build_basketball_oxylabs_schema_expansion_report,
    write_basketball_oxylabs_schema_expansion_report,
)


class TestBasketballOxylabsSchemaExpansion(unittest.TestCase):
    def test_schema_expansion_report_keeps_oxylabs_metadata_without_new_fields(self):
        report = build_basketball_oxylabs_schema_expansion_report(
            source_exhaustion_report={
                "oxylabs_residential_proxy_used": True,
                "oxylabs_web_scraper_api_used": True,
                "oxylabs_total_calls_attempted": 5,
                "oxylabs_total_calls_successful": 5,
                "oxylabs_total_calls_failed": 0,
            },
            backfill_report={"loader_ready_lanes_backfilled": 1},
        )
        self.assertTrue(report["ok"])
        self.assertTrue(report["oxylabs_used"])
        self.assertEqual(report["oxylabs_new_fields_created_count"], 0)
        self.assertEqual(report["oxylabs_new_tables_created_count"], 0)

    def test_writer_creates_report_files(self):
        report = build_basketball_oxylabs_schema_expansion_report()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_basketball_oxylabs_schema_expansion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
