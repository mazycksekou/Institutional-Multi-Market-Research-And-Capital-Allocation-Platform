import tempfile
import unittest
from pathlib import Path

from automation_scheduler.soccer_free_open_exhaustion import build_soccer_paid_data_requirement_matrix, write_soccer_paid_data_requirement_matrix


class TestSoccerPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_matrix_builds_rows(self):
        report = build_soccer_paid_data_requirement_matrix(
            source_ledger={"source_ledger_rows": [{"lane_name": "tracking_360_context", "free_or_paid_category": "paid_data_subscription_required", "sport": "soccer"}]},
            audit_report={"source_candidate_rows": [{"lane_name": "tracking_360_context", "oxylabs_transport_used": "web_scraper_api", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0}]},
        )
        self.assertTrue(report["paid_required_count"] >= 1)

    def test_writer_creates_files(self):
        report = {"paid_required_count": 1, "requirement_rows": [{"lane_name": "tracking_360_context", "priority": "high", "oxylabs_transport_used": "web_scraper_api", "recommendation": "paid_subscription_required"}]}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_paid_data_requirement_matrix(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
