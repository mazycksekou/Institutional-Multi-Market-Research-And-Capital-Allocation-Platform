import unittest

from automation_scheduler.tennis_policy_classifier import classify_tennis_source


class TestTennisPolicyClassifier(unittest.TestCase):
    def test_manual_only_source_maps_to_manual_import_required(self):
        candidate = {
            "sport": "tennis",
            "source_id": "x",
            "source_name": "x",
            "source_domain": "example.com",
            "source_path_or_path_pattern": "/x",
            "source_type": "public_page",
            "source_url": "https://example.com/x",
            "policy_mode": "manual_only",
            "normalized_entity_level": "source",
            "repo_field_mapping": [],
            "new_fields_recommended": [],
            "future_leakage_risk": "low",
            "cutoff_safe": True,
            "normalized_fact_persistence_allowed": False,
            "aggregate_feature_persistence_allowed": False,
        }
        row = classify_tennis_source(
            candidate,
            source_page={"ok": True, "transport": "web_scraper_api"},
            robots_review={"robots_decision": "allow", "robots_checked": True, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0},
            terms_review={"scraping_allowed": True, "terms_checked": True, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0},
            license_review={"license_checked": False, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0},
            api_docs_review={"api_docs_checked": False, "data_dictionary_checked": False, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0},
        )
        self.assertEqual(row["final_state"], "manual_import_required")


if __name__ == "__main__":
    unittest.main()
