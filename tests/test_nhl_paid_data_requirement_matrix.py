import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_free_open_exhaustion import build_nhl_paid_data_requirement_matrix, write_nhl_paid_data_requirement_matrix


class TestNhlPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_matrix_keeps_paid_lane(self):
        report = build_nhl_paid_data_requirement_matrix(
            source_ledger={
                "source_ledger_rows": [
                    {"sport": "icehockey_nhl", "lane_name": "goalie_gsaax_dataset", "free_or_paid_category": "paid_data_subscription_required", "fields": ["goalie_recent_goals_saved_above_expected_proxy"], "candidate_source_name": "Paid vendor"}
                ]
            },
            audit_report={"source_candidate_rows": [{"lane_name": "goalie_gsaax_dataset", "oxylabs_transport_used": "web_scraper_api", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0}]},
        )
        self.assertEqual(report["paid_required_count"], 1)
        self.assertEqual(report["requirement_rows"][0]["recommendation"], "paid_subscription_required")

    def test_writer_creates_files(self):
        report = {
            "paid_required_count": 1,
            "requirement_rows": [{"lane_name": "goalie_gsaax_dataset", "priority": "high", "oxylabs_transport_used": "web_scraper_api", "recommendation": "paid_subscription_required"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_paid_data_requirement_matrix(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
