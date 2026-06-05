import unittest

from automation_scheduler.combat_license_parser import evaluate_combat_license


class TestCombatLicenseParser(unittest.TestCase):
    def test_license_wrapper_returns_expected_keys(self):
        result = evaluate_combat_license(
            {
                "source_id": "x",
                "source_domain": "example.com",
                "license_url": "https://example.com",
            }
        )
        self.assertTrue(result["license_checked"])
        self.assertIn("license_name_if_any", result)
        self.assertEqual(result["oxylabs_calls_attempted"], 1)


if __name__ == "__main__":
    unittest.main()
