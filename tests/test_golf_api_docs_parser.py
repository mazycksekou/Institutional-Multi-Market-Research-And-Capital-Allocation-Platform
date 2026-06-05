import unittest

from automation_scheduler.golf_api_docs_parser import evaluate_golf_api_docs
from automation_scheduler.golf_source_policy_review import golf_candidate_source_catalog


class TestGolfApiDocsParser(unittest.TestCase):
    def test_api_docs_review_reports_dictionary_presence(self):
        result = evaluate_golf_api_docs(golf_candidate_source_catalog()[0])
        self.assertTrue(result["api_docs_checked"])
        self.assertIn("data_dictionary_checked", result)


if __name__ == "__main__":
    unittest.main()
