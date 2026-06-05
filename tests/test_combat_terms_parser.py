import unittest

from automation_scheduler.combat_terms_parser import evaluate_combat_terms


class TestCombatTermsParser(unittest.TestCase):
    def test_terms_wrapper_returns_expected_keys(self):
        result = evaluate_combat_terms(
            {
                "source_id": "x",
                "source_domain": "example.com",
                "terms_url": "https://example.com",
            }
        )
        self.assertTrue(result["terms_checked"])
        self.assertTrue(result["source_policy_reviewed"])
        self.assertEqual(result["oxylabs_calls_attempted"], 1)


if __name__ == "__main__":
    unittest.main()
