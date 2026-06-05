import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatSchemaExpansion(unittest.TestCase):
    def test_schema_expansion_creates_fields_for_verified_lanes(self):
        report = combat_artifacts()["schema_report"]
        self.assertTrue(report["ok"])
        self.assertGreater(report["new_fields_created_count"], 0)
        self.assertGreater(report["new_tables_created_count"], 0)


if __name__ == "__main__":
    unittest.main()
