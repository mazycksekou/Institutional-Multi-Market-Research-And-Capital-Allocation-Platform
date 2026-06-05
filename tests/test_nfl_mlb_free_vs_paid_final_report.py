import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class TestNflMlbFreeVsPaidFinalReport(unittest.TestCase):
    def test_final_report_exposes_requested_sections(self):
        sample = {
            "reports": {
                "mlb_retrosheet": {"fields_verified_union": ["a"], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0},
                "mlb_statcast": {"fields_verified_union": ["b"], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0},
                "mlb_official_public_web": {"fields_verified_union": ["c"], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0},
                "mlb_draft": {"fields_verified_union": ["d"], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0},
                "structured_wiki": {"fields_verified_union": [], "sample_verified_count": 0, "sample_blocked_count": 0, "sample_no_records_count": 1},
                "nflverse": {"fields_verified_union": ["n"], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0},
            },
            "sample_verified_count": 5,
            "sample_blocked_count": 0,
            "sample_no_records_count": 1,
            "verified_fields_count": 5,
            "provider_calls_attempted": 5,
            "downloads_attempted": 5,
            "downloads_succeeded": 5,
        }
        ledger = {"summary": {"source_count": 3, "free_open_source_count": 2, "paid_required_source_count": 1, "policy_blocked_source_count": 1}, "source_ledger_rows": [{"source_id": "free", "access_tier": "free_open", "sample_status": "sample_verified", "recommended_action": "eligible_for_calibration", "sample_blocked_reason": None}]}
        gap = {"gap_rows_total": 10, "incomplete_fields_total": 5, "blockers": ["terms_review_required"], "action_rows": []}
        paid = {"requirement_count": 1, "paid_required_count": 1, "policy_review_required_count": 0, "manual_import_required_count": 0, "supplemental_only_count": 0}
        readiness = {"calibration_readiness_state": "ready_for_free_open_calibration", "calibration_readiness_score": 75.0, "blocked_lanes_remaining": ["blocked"], "free_open_lane_count": 2, "paid_required_lane_count": 1, "policy_blocked_lane_count": 1}
        closure = {"fields_closed_count": 5, "sample_verified_source_count": 5, "sample_blocked_source_count": 0, "sample_no_records_source_count": 1}
        with patch.object(mod, "build_nfl_completion_report", return_value={"record_count_total": 100, "feature_groups_built": ["a"], "feature_groups_blocked": ["b"], "cutoff_safe_feature_count": 1, "future_leakage_checks_passed": True}), patch.object(mod, "build_mlb_completion_report", return_value={"record_count_total": 200, "feature_groups_built": ["c"], "feature_groups_blocked": ["d"], "cutoff_safe_feature_count": 1, "future_leakage_checks_passed": True}):
            report = mod.build_free_vs_paid_final_report(
                sample_verification_results=sample,
                source_ledger=ledger,
                gap_action_plan=gap,
                paid_matrix=paid,
                calibration_readiness=readiness,
                field_closure=closure,
            )
        self.assertTrue(report["ok"])
        self.assertEqual(report["final_verdict"], "FREE_VS_PAID_CALIBRATION_READY_WITH_BLOCKED_LANES")
        self.assertIn("reports", report)
        with tempfile.TemporaryDirectory() as tmp:
            paths = mod.write_free_vs_paid_final_report(report, output_dir=Path(tmp) / "reports")
        self.assertTrue(paths["latest_json_path"].endswith("reports/NFL_MLB_FREE_VS_PAID_FINAL_REPORT.json"))
        self.assertTrue(paths["latest_markdown_path"].endswith("reports/NFL_MLB_FREE_VS_PAID_FINAL_REPORT.md"))


if __name__ == "__main__":
    unittest.main()
