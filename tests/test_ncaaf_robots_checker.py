import unittest
from automation_scheduler.ncaaf_robots_checker import evaluate_ncaaf_robots
from automation_scheduler.ncaaf_source_policy_review import ncaaf_candidate_source_catalog

class TestNcaafRobotsChecker(unittest.TestCase):
    def test_robots_review_runs(self):
        result = evaluate_ncaaf_robots(ncaaf_candidate_source_catalog()[0])
        self.assertTrue(result["robots_checked"])
        self.assertIn("robots_decision", result)

if __name__ == "__main__":
    unittest.main()
