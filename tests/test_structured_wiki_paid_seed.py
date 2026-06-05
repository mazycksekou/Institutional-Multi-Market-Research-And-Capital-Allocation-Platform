import unittest

from automation_scheduler.active_source_discovery_policy import build_paid_retrieval_policy_registry


class TestStructuredWikiPaidSeed(unittest.TestCase):
    def test_paid_registry_marks_mlb_enabled(self):
        registry = build_paid_retrieval_policy_registry(sport="mlb")
        self.assertEqual(registry["paid_source_enabled_count"], 1)
        self.assertEqual(registry["sport"], "mlb")


if __name__ == "__main__":
    unittest.main()

