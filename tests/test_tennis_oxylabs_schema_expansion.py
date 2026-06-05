import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisOxylabsSchemaExpansion(unittest.TestCase):
    def test_schema_expansion_report_exists_and_is_safe(self):
        report = tennis_artifacts()["oxylabs_schema_report"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["provider_write"], False)
        self.assertEqual(report["execution_allowed"], False)
        self.assertGreaterEqual(report["new_fields_created_count"], 0)


if __name__ == "__main__":
    unittest.main()
