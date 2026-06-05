import unittest

from automation_scheduler.completed_sports_policy_classifier import classify_completed_sports_source, map_policy_decision_to_final_state


class TestCompletedSportsPolicyClassifier(unittest.TestCase):
    def test_manual_only_maps_to_manual_import(self):
        candidate = {
            "sport": "soccer",
            "source_id": "soccer_bundesliga_official_pages",
            "source_name": "Bundesliga official public pages",
            "source_domain": "bundesliga.com",
            "source_path_or_path_pattern": "/en/bundesliga",
            "source_type": "official_league_page",
            "policy_mode": "manual_only",
            "repo_field_mapping": ["injuries_availability"],
            "normalized_entity_level": "matchday_page",
            "sport_model_relevance": "high",
            "future_leakage_risk": "low",
            "cutoff_safe": True,
            "cutoff_safety_reason": "manual timestamps",
            "required_attribution_text_or_url_hash": "hash",
            "normalized_fact_persistence_allowed": True,
            "aggregate_feature_persistence_allowed": False,
            "exact_blocker_or_allowance": "manual only",
            "source_url": "https://www.bundesliga.com/en/bundesliga",
        }
        row = classify_completed_sports_source(
            candidate,
            source_page={"ok": True, "transport": "web_scraper_api"},
            robots_review={"robots_checked": True, "robots_decision": "allow", "robots_decision_reason": "ok", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
            terms_review={"terms_checked": True, "scraping_allowed": True, "exact_blocker_or_allowance": "manual only", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
            license_review={"license_checked": True, "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
            api_docs_review={"api_docs_checked": False, "data_dictionary_checked": False, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0},
        )
        self.assertEqual(row["path_level_decision"], "accepted_for_manual_import_only")
        self.assertEqual(row["final_state"], "manual_import_required")

    def test_decision_to_state_paid(self):
        candidate = {"policy_mode": "paid"}
        self.assertEqual(map_policy_decision_to_final_state(candidate, "rejected_terms_blocked"), "paid_subscription_required")


if __name__ == "__main__":
    unittest.main()

