import unittest

from automation_scheduler.nfl_policy_query_builder import build_nfl_policy_query_plan


class TestNflPolicyQueryBuilder(unittest.TestCase):
    def test_query_plan_has_breadth(self):
        plan = build_nfl_policy_query_plan()
        self.assertGreaterEqual(plan["query_count"], 25)
        self.assertIn("exact_source_name", plan["query_families"])


if __name__ == "__main__":
    unittest.main()

