import unittest

from automation_scheduler.tennis_license_parser import evaluate_tennis_license


class TestTennisLicenseParser(unittest.TestCase):
    def test_missing_license_url_is_safe(self):
        result = evaluate_tennis_license({"source_id": "x", "source_domain": "example.com"})
        self.assertFalse(result["license_checked"])
        self.assertEqual(result["oxylabs_calls_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
