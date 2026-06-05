import unittest
from automation_scheduler.ncaaf_api_docs_parser import evaluate_ncaaf_api_docs
from automation_scheduler.ncaaf_source_policy_review import ncaaf_candidate_source_catalog

class TestNcaafApiDocsParser(unittest.TestCase):
    def test_api_docs_review_runs(self):
        result = evaluate_ncaaf_api_docs(ncaaf_candidate_source_catalog()[0])
        self.assertTrue(result["api_docs_checked"])
        self.assertIn("data_dictionary_checked", result)

if __name__ == "__main__":
    unittest.main()
