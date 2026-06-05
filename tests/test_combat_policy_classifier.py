import unittest

from automation_scheduler.combat_policy_classifier import classify_combat_source


class TestCombatPolicyClassifier(unittest.TestCase):
    def test_classifier_returns_manual_only_final_state(self):
        row = classify_combat_source(
            {
                "sport": "combat",
                "source_id": "x",
                "source_name": "Example",
                "source_domain": "example.com",
                "source_path_or_path_pattern": "/",
                "source_type": "docs",
                "policy_mode": "manual_only",
                "repo_field_mapping": [],
                "source_url": "https://example.com",
                "normalized_entity_level": "fighter",
            },
            source_page={"ok": True, "transport": "web_scraper_api"},
            robots_review={"robots_decision": "allow", "robots_checked": True, "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
            terms_review={"scraping_allowed": True, "terms_checked": True, "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
            license_review={"license_name_if_any": "MIT", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
            api_docs_review={"api_docs_checked": True, "data_dictionary_checked": True, "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0},
        )
        self.assertEqual(row["path_level_decision"], "accepted_for_manual_import_only")
        self.assertEqual(row["final_state"], "manual_import_required")


if __name__ == "__main__":
    unittest.main()
