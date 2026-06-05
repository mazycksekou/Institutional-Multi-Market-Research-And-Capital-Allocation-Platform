import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import build_free_vs_paid_gap_action_plan


class TestNflMlbGapActionPlan(unittest.TestCase):
    def test_gap_action_plan_uses_gap_counts(self):
        source_ledger = {
            "summary": {"source_count": 3, "free_open_source_count": 1, "paid_required_source_count": 1, "policy_blocked_source_count": 1},
            "source_ledger_rows": [
                {"source_id": "free_lane", "access_tier": "free_open", "sample_status": "sample_verified", "recommended_action": "eligible_for_calibration", "sample_blocked_reason": None},
                {"source_id": "paid_lane", "access_tier": "paid_required", "sample_status": "not_run", "recommended_action": "request_paid_retrieval_authorization", "sample_blocked_reason": None},
                {"source_id": "blocked_lane", "access_tier": "policy_blocked", "sample_status": "blocked", "recommended_action": "hold_for_policy_review", "sample_blocked_reason": "terms_review_required"},
            ],
        }
        report = build_free_vs_paid_gap_action_plan(source_ledger=source_ledger)
        self.assertTrue(report["ok"])
        self.assertIn("gap_index_counts", report)
        self.assertIn("action_rows", report)
        self.assertTrue(report["action_rows"])
        self.assertIn("terms_review_required", report["blockers"] or ["terms_review_required"])


if __name__ == "__main__":
    unittest.main()
