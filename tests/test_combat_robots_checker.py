import unittest

from automation_scheduler.combat_robots_checker import evaluate_combat_robots


class TestCombatRobotsChecker(unittest.TestCase):
    def test_robots_wrapper_returns_expected_keys(self):
        result = evaluate_combat_robots(
            {
                "source_id": "x",
                "source_domain": "example.com",
                "source_path_or_path_pattern": "/x",
                "robots_url": "https://example.com/robots.txt",
            }
        )
        self.assertTrue(result["robots_checked"])
        self.assertIn(result["robots_decision"], {"allow", "block", "not_checked"})
        self.assertEqual(result["oxylabs_calls_attempted"], 1)


if __name__ == "__main__":
    unittest.main()
