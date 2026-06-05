import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import build_paid_data_requirement_matrix


class TestNflMlbPaidDataRequirementMatrix(unittest.TestCase):
    def test_matrix_includes_required_counts(self):
        source_ledger = {
            "source_ledger_rows": [
                {"sport": "nfl", "source_id": "free_lane", "access_tier": "free_open", "sample_status": "sample_verified", "recommended_action": "eligible_for_calibration", "notes": ""},
                {"sport": "mlb", "source_id": "paid_lane", "access_tier": "paid_required", "sample_status": "not_run", "recommended_action": "request_paid_retrieval_authorization", "notes": ""},
                {"sport": "mlb", "source_id": "manual_lane", "access_tier": "manual_csv", "sample_status": "not_run", "recommended_action": "prepare_manual_import_template", "notes": ""},
            ]
        }
        report = build_paid_data_requirement_matrix(source_ledger=source_ledger)
        self.assertTrue(report["ok"])
        self.assertEqual(report["requirement_count"], 2)
        self.assertEqual(report["paid_required_count"], 1)
        self.assertEqual(report["manual_import_required_count"], 1)


if __name__ == "__main__":
    unittest.main()
