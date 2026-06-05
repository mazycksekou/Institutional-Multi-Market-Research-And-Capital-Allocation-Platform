import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfOxylabsSchemaExpansion(unittest.TestCase):
    def test_oxylabs_schema_report_mirrors_verified_fields(self):
        report = golf_artifacts()["oxylabs_schema"]
        self.assertEqual(report["new_fields_created_count"], report["oxylabs_verified_field_count"])
        self.assertGreater(report["oxylabs_verified_field_count"], 0)
        self.assertFalse(report["raw_html_persisted"])


if __name__ == "__main__":
    unittest.main()
