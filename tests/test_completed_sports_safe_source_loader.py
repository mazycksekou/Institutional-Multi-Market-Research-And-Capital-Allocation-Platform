import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.completed_sports_safe_source_loader import build_completed_sports_policy_backfill_final_state_report


class TestCompletedSportsSafeSourceLoader(unittest.TestCase):
    def test_final_state_report_writes_session_rows(self):
        matrix = {"policy_matrix_rows": [{"sport": "soccer", "source_id": "soccer_football_data", "source_name": "football-data", "source_path": "/data.php", "path_level_decision": "accepted_for_automated_normalized_backfill", "final_state": "free_open_backfilled", "exact_blocker_or_allowance": "allowed"}]}
        sample = {"sample_rows": [{"source_path_hash": "7f1f3609216dcf5f4d9ef75b8ac9f00f4df0b513db682002ca2e7f0b9fe66cb2", "normalized_records_added": 2, "sample_rows": [{"a": 1}, {"a": 2}]}]}
        with tempfile.TemporaryDirectory() as tmp, patch("automation_scheduler.completed_sports_safe_source_loader.COMPLETED_SPORTS_DATA_ROOT", Path(tmp) / "data"):
            report = build_completed_sports_policy_backfill_final_state_report(policy_matrix=matrix, sample_report=sample)
        self.assertEqual(report["final_state_row_count"], 1)
        self.assertTrue(report["paths"]["session_root"])


if __name__ == "__main__":
    unittest.main()

