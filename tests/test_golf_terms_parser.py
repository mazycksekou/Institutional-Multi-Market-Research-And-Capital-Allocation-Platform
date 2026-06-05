import unittest

from automation_scheduler.golf_source_policy_review import golf_candidate_source_catalog
from automation_scheduler.golf_terms_parser import evaluate_golf_terms


class TestGolfTermsParser(unittest.TestCase):
    def test_terms_review_returns_safe_decision_data(self):
        result = evaluate_golf_terms(golf_candidate_source_catalog()[0])
        self.assertTrue(result["terms_checked"])
        self.assertIn("automated_access_allowed", result)
        self.assertFalse(result.get("raw_html_persisted", False))


if __name__ == "__main__":
    unittest.main()
