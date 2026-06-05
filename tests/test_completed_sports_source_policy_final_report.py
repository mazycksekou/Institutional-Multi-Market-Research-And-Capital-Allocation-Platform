import unittest

from automation_scheduler.completed_sports_policy_review import build_completed_sports_source_policy_final_report


class TestCompletedSportsSourcePolicyFinalReport(unittest.TestCase):
    def test_final_report_reaches_success_with_unclear_paths(self):
        prior = {"nfl_mlb": {}, "basketball": {}, "nhl": {}, "soccer": {}}
        inventory = {"candidate_source_count": 2}
        discovery = {"oxylabs_residential_proxy_used": True, "oxylabs_web_scraper_api_used": True}
        policy_matrix = {
            "policy_matrix_rows": [
                {"sport": "soccer", "path_level_decision": "accepted_for_automated_normalized_backfill", "final_state": "free_open_backfilled", "repo_field_mapping": ["a"], "usable_for_prematch_model": True, "usable_for_postmatch_training_only": False, "oxylabs_calls_attempted": 3, "oxylabs_calls_successful": 3, "oxylabs_calls_failed": 0, "source_policy_reviewed": True, "robots_checked": True, "terms_checked": True, "license_checked": True, "api_docs_checked": True, "data_dictionary_checked": True},
                {"sport": "icehockey_nhl", "path_level_decision": "license_terms_unclear", "final_state": "license_terms_unclear", "repo_field_mapping": ["b"], "usable_for_prematch_model": False, "usable_for_postmatch_training_only": False, "oxylabs_calls_attempted": 2, "oxylabs_calls_successful": 2, "oxylabs_calls_failed": 0, "source_policy_reviewed": True, "robots_checked": True, "terms_checked": True, "license_checked": False, "api_docs_checked": False, "data_dictionary_checked": False},
            ],
            "decision_counts": {"accepted_for_automated_normalized_backfill": 1, "license_terms_unclear": 1},
        }
        sample = {"sample_rows": []}
        final_state = {"final_state_rows": [{"sport": "soccer", "final_state": "free_open_backfilled"}, {"sport": "icehockey_nhl", "final_state": "license_terms_unclear"}], "normalized_records_added": 3, "postmatch_training_records_added": 0, "metadata_only_records_added": 0}
        delta = {}
        report = build_completed_sports_source_policy_final_report(
            prior_reports=prior,
            candidate_inventory=inventory,
            discovery_log=discovery,
            policy_matrix=policy_matrix,
            sample_report=sample,
            final_state_report=final_state,
            delta_report=delta,
            tests_result="passed",
        )
        self.assertEqual(report["final_policy_review_verdict"], "COMPLETED_SPORTS_POLICY_REVIEW_COMPLETE_WITH_UNCLEAR_POLICY_PATHS")
        self.assertTrue(report["no_more_completed_sports_public_policy_search_required"])
        self.assertEqual(report["lanes_with_vague_status"], 0)


if __name__ == "__main__":
    unittest.main()

