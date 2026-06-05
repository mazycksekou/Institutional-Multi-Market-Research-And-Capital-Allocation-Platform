import unittest
from automation_scheduler.ncaaf_license_parser import evaluate_ncaaf_license
from automation_scheduler.ncaaf_source_policy_review import ncaaf_candidate_source_catalog

class TestNcaafLicenseParser(unittest.TestCase):
    def test_license_review_runs(self):
        result = evaluate_ncaaf_license(ncaaf_candidate_source_catalog()[0])
        self.assertTrue(result["license_checked"])
        self.assertIn("license_confidence", result)

if __name__ == "__main__":
    unittest.main()
