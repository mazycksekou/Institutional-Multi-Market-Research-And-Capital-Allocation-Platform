import unittest

from automation_scheduler.combat_api_docs_parser import evaluate_combat_api_docs


class TestCombatApiDocsParser(unittest.TestCase):
    def test_api_docs_wrapper_returns_expected_keys(self):
        result = evaluate_combat_api_docs(
            {
                "source_id": "x",
                "source_domain": "example.com",
                "source_url": "https://example.com/data.csv",
                "source_type": "open_csv_docs_page",
                "api_docs_url": "https://example.com",
                "data_dictionary_url": "https://example.com",
                "repo_field_mapping": ["a", "b"],
            }
        )
        self.assertTrue(result["api_docs_checked"])
        self.assertTrue(result["data_dictionary_checked"])
        self.assertEqual(result["oxylabs_calls_attempted"], 2)


if __name__ == "__main__":
    unittest.main()
