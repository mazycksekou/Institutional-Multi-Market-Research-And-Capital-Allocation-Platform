import unittest
from unittest.mock import patch

from src.services.streamlit_dashboard_facade import ops_workflow


class TestOutcomeReconciliation(unittest.TestCase):
    def _package(self):
        return {
            "ok": True,
            "migration_version": "kalshi_outcome_migration_v1",
            "records": [
                {"provider_id": "kalshi_prediction_market", "ticker": "KX1", "contract_id": "KX1", "final_outcome": "yes", "outcome_status": "settled", "settled_at": "2026-05-29T00:00:00+00:00", "source": "read_only_settlement"},
                {"provider_id": "kalshi_prediction_market", "ticker": "KX2", "contract_id": "KX2", "final_outcome": "no", "outcome_status": "settled", "settled_at": "2026-05-29T00:01:00+00:00", "source": "read_only_settlement"},
            ],
            "supporting_paper_decisions": [{"decision_id": "decision_1", "ticker": "KX1"}],
            "records_rejected": 0,
            "duplicate_count": 0,
            "supporting_paper_decision_count": 1,
        }

    def test_reconciliation_without_base_url_builds_local_package_only(self):
        with patch('src.automation_scheduler_legacy.outcome_migration.build_kalshi_outcome_migration_package', return_value=self._package()):
            result = ops_workflow.check_outcome_reconciliation(None)

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "local_package_built")
        self.assertEqual(result["local_package_count"], 2)
        self.assertEqual(result["recommendation"], "set_APP_BASE_URL_and_run_dry_run_import")
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])

    def test_reconciliation_reports_local_render_state_mismatch_and_progress(self):
        dry_run = {
            "ok": True,
            "data": {
                "records_received": 2,
                "records_valid": 2,
                "records_rejected": 0,
                "duplicate_count": 0,
                "would_insert_count": 2,
                "matched_paper_decision_count": 2,
                "unmatched_count": 0,
                "render_existing_outcomes_count": 4,
                "render_outcomes_after_import_if_persisted": 6,
            },
        }
        with patch('src.automation_scheduler_legacy.outcome_migration.build_kalshi_outcome_migration_package', return_value=self._package()):
            with patch('src.automation_scheduler_legacy.ops_workflow.safe_post_json', return_value=dry_run):
                with patch('src.automation_scheduler_legacy.ops_workflow.check_calibration_status', return_value={"matched_outcomes_count": 4}):
                    result = ops_workflow.check_outcome_reconciliation("https://example.test")

        self.assertEqual(result["status"], "local_render_state_mismatch")
        self.assertEqual(result["local_package_count"], 2)
        self.assertEqual(result["render_outcomes_count"], 4)
        self.assertEqual(result["local_only_count"], 2)
        self.assertEqual(result["would_insert_count"], 2)
        self.assertEqual(result["matched_after_import_estimate"], 6)
        self.assertEqual(result["progress_to_100_after_import"]["count"], 6)
        self.assertEqual(result["progress_to_100_after_import"]["target"], 100)
        self.assertEqual(result["progress_to_300_after_import"]["count"], 6)
        self.assertEqual(result["progress_to_300_after_import"]["target"], 300)
        self.assertEqual(result["progress_to_1000_after_import"]["count"], 6)
        self.assertEqual(result["progress_to_1000_after_import"]["target"], 1000)
        self.assertEqual(result["recommendation"], "user_approval_required_to_persist_import")

    def test_reconciliation_recommends_paper_matching_fix_when_unmatched(self):
        dry_run = {
            "ok": True,
            "data": {
                "records_received": 1,
                "records_valid": 1,
                "records_rejected": 0,
                "duplicate_count": 0,
                "would_insert_count": 1,
                "matched_paper_decision_count": 0,
                "unmatched_count": 1,
                "render_existing_outcomes_count": 4,
                "render_outcomes_after_import_if_persisted": 5,
            },
        }
        package = self._package()
        package["records"] = package["records"][:1]
        with patch('src.automation_scheduler_legacy.outcome_migration.build_kalshi_outcome_migration_package', return_value=package):
            with patch('src.automation_scheduler_legacy.ops_workflow.safe_post_json', return_value=dry_run):
                with patch('src.automation_scheduler_legacy.ops_workflow.check_calibration_status', return_value={"matched_outcomes_count": 4}):
                    result = ops_workflow.check_outcome_reconciliation("https://example.test")

        self.assertEqual(result["unmatched_count"], 1)
        self.assertEqual(result["recommendation"], "fix_paper_ledger_matching_before_import")


if __name__ == "__main__":
    unittest.main()
