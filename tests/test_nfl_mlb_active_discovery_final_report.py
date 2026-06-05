import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_mlb_active_discovery import build_active_discovery_final_report, write_active_discovery_final_report


class TestNflMlbActiveDiscoveryFinalReport(unittest.TestCase):
    def test_report_exposes_required_fields(self):
        report = build_active_discovery_final_report(
            tests_run=["pytest tests -q"],
            tests_passed=["pytest tests -q"],
            tests_failed=[],
            files_changed=["automation_scheduler/nfl_mlb_active_discovery.py"],
            remaining_manual_actions=[],
            final_verdict="PARTIAL_DISCOVERY_SUCCESS",
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["final_verdict"], "PARTIAL_DISCOVERY_SUCCESS")
        for key in (
            "branch_name",
            "commit_hash",
            "run_mode",
            "nfl_status",
            "mlb_status",
            "paid_source_enabled_count",
            "active_discovery_performed",
            "source_queries_run_count",
            "sources_discovered_count",
            "sources_accepted_count",
            "sources_rejected_count",
            "source_discovery_log_path",
            "field_inventory_before_path",
            "nfl_schema_expansion_report_path",
            "mlb_schema_expansion_report_path",
            "nfl_paid_retrieval_report_path",
            "mlb_paid_retrieval_report_path",
            "existing_fields_total",
            "existing_fields_completed_count",
            "existing_fields_still_empty_count",
            "new_fields_created_count",
            "new_tables_created_count",
            "nfl_records_before",
            "nfl_records_after",
            "nfl_records_added",
            "mlb_records_before",
            "mlb_records_after",
            "mlb_records_added",
            "nfl_coaching_before_after",
            "mlb_managers_coaches_before_after",
            "mlb_draft_before_after",
            "structured_wiki_seed_before_after",
            "source_lanes_still_blocked",
            "source_lanes_still_research",
            "new_feature_groups_created",
            "feature_groups_model_eligible",
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
            "remaining_manual_actions",
            "inventory_summary",
            "discovery_log_preview",
            "final_verdict",
        ):
            self.assertIn(key, report)

    def test_report_writes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_active_discovery_final_report(
                tests_run=["pytest tests -q"],
                tests_passed=["pytest tests -q"],
                tests_failed=[],
                files_changed=["automation_scheduler/nfl_mlb_active_discovery.py"],
                remaining_manual_actions=[],
                final_verdict="PARTIAL_DISCOVERY_SUCCESS",
            )
            paths = write_active_discovery_final_report(report, output_dir=Path(tmp) / "reports")
        self.assertTrue(paths["latest_json_path"].endswith("reports/NFL_MLB_ACTIVE_DISCOVERY_FINAL_REPORT.json"))
        self.assertTrue(paths["latest_markdown_path"].endswith("reports/NFL_MLB_ACTIVE_DISCOVERY_FINAL_REPORT.md"))


if __name__ == "__main__":
    unittest.main()
