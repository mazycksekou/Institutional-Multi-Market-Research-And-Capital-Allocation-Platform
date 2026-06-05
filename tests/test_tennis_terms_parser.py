import unittest

from automation_scheduler.tennis_terms_parser import evaluate_tennis_terms


class TestTennisTermsParser(unittest.TestCase):
    def test_missing_terms_url_is_safe(self):
        result = evaluate_tennis_terms({"source_id": "x", "source_domain": "example.com"})
        self.assertFalse(result["terms_checked"])
        self.assertEqual(result["oxylabs_calls_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
