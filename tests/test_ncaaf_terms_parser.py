import unittest
from automation_scheduler.ncaaf_source_policy_review import ncaaf_candidate_source_catalog
from automation_scheduler.ncaaf_terms_parser import evaluate_ncaaf_terms

class TestNcaafTermsParser(unittest.TestCase):
    def test_terms_review_runs(self):
        result = evaluate_ncaaf_terms(ncaaf_candidate_source_catalog()[0])
        self.assertTrue(result["terms_checked"])
        self.assertIn("automated_access_allowed", result)

if __name__ == "__main__":
    unittest.main()
