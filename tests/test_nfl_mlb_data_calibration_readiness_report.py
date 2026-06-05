import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class TestNflMlbDataCalibrationReadinessReport(unittest.TestCase):
    def test_report_includes_score_and_blocked_lanes(self):
        source_ledger = {
            "summary": {"source_count": 4, "free_open_source_count": 2, "paid_required_source_count": 1, "policy_blocked_source_count": 1},
            "source_ledger_rows": [
                {"source_id": "free_lane", "access_tier": "free_open", "sample_status": "sample_verified", "recommended_action": "eligible_for_calibration", "sample_blocked_reason": None},
                {"source_id": "free_lane_2", "access_tier": "free_open", "sample_status": "sample_verified", "recommended_action": "eligible_for_calibration", "sample_blocked_reason": None},
                {"source_id": "paid_lane", "access_tier": "paid_required", "sample_status": "not_run", "recommended_action": "request_paid_retrieval_authorization", "sample_blocked_reason": None},
                {"source_id": "blocked_lane", "access_tier": "policy_blocked", "sample_status": "blocked", "recommended_action": "hold_for_policy_review", "sample_blocked_reason": "terms_review_required"},
            ],
        }
        sample = {
            "reports": {"mlb_retrosheet": {"fields_verified_union": ["a", "b"]}, "nflverse": {"fields_verified_union": ["c"]}},
            "sample_verified_count": 2,
            "sample_blocked_count": 1,
            "sample_no_records_count": 1,
            "verified_fields_count": 3,
            "provider_calls_attempted": 4,
            "downloads_attempted": 3,
            "downloads_succeeded": 3,
        }
        with patch.object(mod, "_load_report", side_effect=lambda name: {"prior_existing_fields_total": 1770, "new_existing_fields_completed": 1658, "new_remaining_incomplete_fields": 112, "fields_closed_this_pass": 161, "fields_partially_closed_this_pass": 33, "gap_index_counts": {"fill_now_with_known_source": 161}} if name == "MAX_EFFORT_OXYLABS_ARCHITECTURE_FINAL_REPORT.json" else {"gap_index_counts": {"fill_now_with_known_source": 161}, "gap_rows_total": 200, "incomplete_fields_total": 112}), patch.object(mod, "build_nfl_completion_report", return_value={"record_count_total": 100, "feature_groups_built": ["a"], "feature_groups_blocked": ["b"], "cutoff_safe_feature_count": 1, "future_leakage_checks_passed": True}), patch.object(mod, "build_mlb_completion_report", return_value={"record_count_total": 200, "feature_groups_built": ["c"], "feature_groups_blocked": ["d"], "cutoff_safe_feature_count": 1, "future_leakage_checks_passed": True}), patch.object(mod, "build_nfl_feature_readiness_report", return_value={"verified_fields_after": 10, "feature_builders_added": ["a"], "feature_builders_blocked": ["b"]}), patch.object(mod, "build_mlb_feature_readiness_report", return_value={"verified_fields_after": 20, "feature_builders_added": ["c"], "feature_builders_blocked": ["d"]}):
            report = mod.build_data_calibration_readiness_report(source_ledger=source_ledger, sample_verification_results=sample)
        self.assertTrue(report["ok"])
        self.assertIn("calibration_readiness_state", report)
        self.assertGreaterEqual(report["calibration_readiness_score"], 0)
        self.assertIn("blocked_lane", report["blocked_lanes_remaining"])


if __name__ == "__main__":
    unittest.main()
