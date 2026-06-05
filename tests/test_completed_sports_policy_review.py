import unittest

from automation_scheduler.completed_sports_policy_review import (
    build_completed_sports_candidate_source_inventory,
    build_completed_sports_policy_review_plan,
    build_completed_sports_policy_review_template,
)


class TestCompletedSportsPolicyReview(unittest.TestCase):
    def test_plan_and_inventory_build(self):
        plan = build_completed_sports_policy_review_plan()
        inventory = build_completed_sports_candidate_source_inventory()
        self.assertGreater(plan["manual_lane_count"], 0)
        self.assertGreater(inventory["candidate_source_count"], 20)

    def test_template_collects_unresolved_rows(self):
        matrix = {
            "policy_matrix_rows": [
                {"sport": "soccer", "source_name": "Understat", "source_domain": "understat.com", "source_url_hash": "hash", "final_state": "license_terms_unclear", "exact_blocker_or_allowance": "unclear", "terms_checked": True, "license_checked": False, "robots_checked": True, "api_docs_checked": False, "data_dictionary_checked": False, "required_attribution_text_or_url_hash": "hash", "cutoff_safety_reason": "n/a"},
            ]
        }
        template = build_completed_sports_policy_review_template(policy_matrix=matrix)
        self.assertEqual(template["template_count"], 1)


if __name__ == "__main__":
    unittest.main()

