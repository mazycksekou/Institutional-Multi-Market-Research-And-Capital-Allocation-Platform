import unittest

from automation_scheduler.soccer_policy_query_builder import build_soccer_policy_query_plan


class TestSoccerPolicyQueryBuilder(unittest.TestCase):
    def test_query_plan_has_breadth(self):
        plan = build_soccer_policy_query_plan()
        self.assertGreaterEqual(plan["query_count"], 25)
        self.assertIn("source_data_dictionary", plan["query_families"])


if __name__ == "__main__":
    unittest.main()

