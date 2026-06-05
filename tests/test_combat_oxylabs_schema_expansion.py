import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatOxylabsSchemaExpansion(unittest.TestCase):
    def test_oxylabs_schema_report_exists(self):
        artifacts = combat_artifacts()
        report = artifacts["oxylabs_schema_report"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["new_fields_created_count"], artifacts["schema_report"]["new_fields_created_count"])
        self.assertTrue(all(row["oxylabs_used"] for row in report["new_fields_created"]))


if __name__ == "__main__":
    unittest.main()
