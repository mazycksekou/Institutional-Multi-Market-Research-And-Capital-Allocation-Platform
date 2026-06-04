import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_completion_report import build_nfl_completion_report, write_nfl_completion_report


class TestNflCompletionReport(unittest.TestCase):
    def test_report_exposes_required_safety_and_timing_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_completion_report(base_data_dir=tmp, run_mode="open_free_mode", tests_run=["one"], tests_passed=["one"], commit_hash="abc123")
            paths = write_nfl_completion_report(report, output_dir=Path(tmp) / "reports")
            latest_json = Path(tmp) / "reports" / "NFL_COMPLETION_FINAL_REPORT.json"
            latest_md = Path(tmp) / "reports" / "NFL_COMPLETION_FINAL_REPORT.md"
            self.assertTrue(latest_json.exists())
            self.assertTrue(latest_md.exists())

        self.assertTrue(report["ok"])
        self.assertEqual(report["run_mode"], "open_free_mode")
        self.assertIn("started_at", report)
        self.assertIn("completed_at", report)
        self.assertTrue(report["started_at"])
        self.assertTrue(report["completed_at"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["raw_screenshot_persisted"])
        self.assertFalse(report["secrets_included"])
        self.assertTrue(paths["latest_json_path"].endswith("reports/NFL_COMPLETION_FINAL_REPORT.json"))
        self.assertTrue(paths["latest_markdown_path"].endswith("reports/NFL_COMPLETION_FINAL_REPORT.md"))

    def test_report_includes_source_family_and_feature_sections(self):
        report = build_nfl_completion_report()
        for key in (
            "source_families_audited",
            "source_families_approved",
            "source_families_populated",
            "source_families_blocked",
            "source_families_research",
            "record_count_total",
            "rejected_count_total",
            "season_coverage",
            "date_coverage",
            "feature_groups_built",
            "feature_groups_model_eligible",
            "feature_groups_blocked",
            "cutoff_safe_feature_count",
            "future_leakage_checks_passed",
            "tests_run",
            "tests_passed",
            "blockers",
            "fallbacks_used",
            "commit_hash",
        ):
            self.assertIn(key, report)
        self.assertIsInstance(report["source_families_audited"], list)
        self.assertIsInstance(report["feature_groups_blocked"], list)


if __name__ == "__main__":
    unittest.main()
