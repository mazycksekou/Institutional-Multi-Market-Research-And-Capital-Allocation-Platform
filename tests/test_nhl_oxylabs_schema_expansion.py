import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_oxylabs_schema_expansion import build_nhl_oxylabs_schema_expansion_report, write_nhl_oxylabs_schema_expansion_report


SAMPLE_RESULTS = {
    "source_result_index": {
        "icehockey_nhl::shot_events": {"validation_status": "sample_verified", "source_url_hash": "hash-shot"},
    }
}


class TestNhlOxylabsSchemaExpansion(unittest.TestCase):
    def test_oxylabs_schema_report_adds_transport(self):
        report = build_nhl_oxylabs_schema_expansion_report(
            source_exhaustion_report={"source_candidate_rows": [{"lane_name": "shot_events", "oxylabs_transport_used": "both", "source_url_hash": "hash-shot"}]},
            backfill_report={"backfill_rows": [{"lane_name": "shot_events", "oxylabs_transport_used": "residential_proxy", "source_url_hash": "hash-shot"}]},
            sample_verification_results=SAMPLE_RESULTS,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["new_fields_created"][0]["oxylabs_transport_used"], "residential_proxy")

    def test_writer_creates_files(self):
        report = build_nhl_oxylabs_schema_expansion_report(
            source_exhaustion_report={"source_candidate_rows": []},
            backfill_report={"backfill_rows": []},
            sample_verification_results=SAMPLE_RESULTS,
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_oxylabs_schema_expansion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
