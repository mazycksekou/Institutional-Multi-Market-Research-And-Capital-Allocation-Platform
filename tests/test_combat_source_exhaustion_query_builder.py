import unittest

from automation_scheduler.combat_source_exhaustion_query_builder import QUERY_FAMILIES, build_combat_source_exhaustion_query_plan


class TestCombatSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_query_plan_satisfies_minimums(self):
        report = build_combat_source_exhaustion_query_plan()
        self.assertTrue(report["minimum_query_count_satisfied"])
        self.assertGreaterEqual(report["query_count"], 125)
        self.assertTrue(set(QUERY_FAMILIES).issubset(set(report["query_families"])))
        self.assertFalse(report["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
