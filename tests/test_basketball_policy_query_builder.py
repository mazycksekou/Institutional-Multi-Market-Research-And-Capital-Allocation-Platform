import unittest

from automation_scheduler.basketball_policy_query_builder import build_basketball_policy_query_plan


class TestBasketballPolicyQueryBuilder(unittest.TestCase):
    def test_query_plan_has_breadth(self):
        plan = build_basketball_policy_query_plan()
        self.assertGreaterEqual(plan["query_count"], 25)
        self.assertIn("source_api_docs", plan["query_families"])


if __name__ == "__main__":
    unittest.main()

