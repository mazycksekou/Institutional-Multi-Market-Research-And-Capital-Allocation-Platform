import unittest

from automation_scheduler.tennis_robots_checker import evaluate_tennis_robots


class TestTennisRobotsChecker(unittest.TestCase):
    def test_missing_robots_url_is_handled_safely(self):
        result = evaluate_tennis_robots({"source_id": "x", "source_domain": "example.com", "source_path_or_path_pattern": "/x"})
        self.assertFalse(result["robots_checked"])
        self.assertEqual(result["robots_decision"], "not_checked")
        self.assertEqual(result["oxylabs_calls_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
