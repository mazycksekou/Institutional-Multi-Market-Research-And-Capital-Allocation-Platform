import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_mlb_integration_report import build_nfl_mlb_integration_report, write_nfl_mlb_integration_report


class TestNflMlbIntegrationReport(unittest.TestCase):
    def test_report_exposes_required_fields(self):
        report = build_nfl_mlb_integration_report(
            nfl_status="COMPLETE",
            mlb_status="COMPLETE_WITH_POLICY_BLOCKED_SOURCES",
            tests_run=["pytest tests -q"],
            tests_passed=["pytest tests -q"],
            files_changed=["a.py"],
            shared_files_touched=["b.py"],
            merge_conflicts_resolved=[],
            remaining_manual_actions=[],
            commit_hash="integration-abc123",
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["combined_verdict"], "COMPLETE_WITH_POLICY_BLOCKED_SOURCES")
        for key in (
            "integration_branch",
            "integration_commit_hash",
            "nfl_commit_hash",
            "mlb_commit_hash",
            "nfl_status",
            "mlb_status",
            "nfl_record_count_total",
            "mlb_record_count_total",
            "total_records_populated",
            "nfl_source_family_summary",
            "mlb_source_family_summary",
            "nfl_feature_groups_model_eligible",
            "mlb_feature_groups_model_eligible",
            "blocked_policy_sources",
            "research_sources",
            "cutoff_safety_summary",
            "future_leakage_checks_passed",
            "oxylabs_residential_proxy_status",
            "oxylabs_web_scraper_api_status",
            "safety_invariants",
            "secret_scan_result",
            "raw_payload_scan_result",
            "tests_run",
            "tests_passed",
            "tests_failed",
            "files_changed",
            "shared_files_touched",
            "merge_conflicts_resolved",
            "remaining_manual_actions",
        ):
            self.assertIn(key, report)

    def test_report_writes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_mlb_integration_report(commit_hash="integration-abc123")
            paths = write_nfl_mlb_integration_report(report, output_dir=Path(tmp) / "reports")
        self.assertTrue(paths["latest_json_path"].endswith("reports/NFL_MLB_INTEGRATION_FINAL_REPORT.json"))
        self.assertTrue(paths["latest_markdown_path"].endswith("reports/NFL_MLB_INTEGRATION_FINAL_REPORT.md"))


if __name__ == "__main__":
    unittest.main()
