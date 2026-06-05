import unittest

from automation_scheduler.tennis_api_docs_parser import evaluate_tennis_api_docs


class TestTennisApiDocsParser(unittest.TestCase):
    def test_missing_urls_are_safe(self):
        result = evaluate_tennis_api_docs({"source_id": "x", "source_domain": "example.com", "source_url": "https://example.com"})
        self.assertFalse(result["api_docs_checked"])
        self.assertFalse(result["data_dictionary_checked"])
        self.assertEqual(result["oxylabs_calls_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
