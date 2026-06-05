import unittest

from automation_scheduler.golf_license_parser import evaluate_golf_license
from automation_scheduler.golf_source_policy_review import golf_candidate_source_catalog


class TestGolfLicenseParser(unittest.TestCase):
    def test_license_review_returns_license_status(self):
        result = evaluate_golf_license(golf_candidate_source_catalog()[0])
        self.assertTrue(result["license_checked"])
        self.assertIn("license_confidence", result)
        self.assertFalse(result.get("secrets_included", False))


if __name__ == "__main__":
    unittest.main()
