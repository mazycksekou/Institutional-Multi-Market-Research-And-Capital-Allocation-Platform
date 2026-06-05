import unittest

from automation_scheduler.nhl_policy_query_builder import build_nhl_policy_query_plan


class TestNhlPolicyQueryBuilder(unittest.TestCase):
    def test_query_plan_has_breadth(self):
        plan = build_nhl_policy_query_plan()
        self.assertGreaterEqual(plan["query_count"], 25)
        self.assertIn("source_license", plan["query_families"])


if __name__ == "__main__":
    unittest.main()

