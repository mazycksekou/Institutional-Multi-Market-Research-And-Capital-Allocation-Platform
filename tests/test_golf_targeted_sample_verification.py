import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfTargetedSampleVerification(unittest.TestCase):
    def test_loader_samples_verify_and_blockers_are_final(self):
        report = golf_artifacts()["sample_verification"]
        statuses = {row["lane_name"]: row["validation_status"] for row in report["sample_results"]}
        self.assertEqual(statuses["course_identity_metadata"], "sample_verified")
        self.assertEqual(statuses["course_par_yardage"], "sample_verified")
        self.assertEqual(statuses["course_scorecard_context"], "sample_verified")
        self.assertEqual(statuses["owgr_ranking_context"], "hard_blocked")
        self.assertEqual(report["sample_failed_count"], 0)


if __name__ == "__main__":
    unittest.main()
