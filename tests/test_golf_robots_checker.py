import unittest

from automation_scheduler.golf_robots_checker import evaluate_golf_robots
from automation_scheduler.golf_source_policy_review import golf_candidate_source_catalog


class TestGolfRobotsChecker(unittest.TestCase):
    def test_robots_review_returns_final_status(self):
        candidate = golf_candidate_source_catalog()[0]
        result = evaluate_golf_robots(candidate)
        self.assertIn("robots_decision", result)
        self.assertTrue(result["robots_checked"])


if __name__ == "__main__":
    unittest.main()
