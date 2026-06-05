import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafOxylabsSchemaExpansion(unittest.TestCase):
    def test_oxylabs_schema_fields_verified(self):
        report = ncaaf_artifacts()["oxylabs_schema"]
        self.assertEqual(report["new_fields_created_count"], report["oxylabs_verified_field_count"])
        self.assertGreater(report["oxylabs_verified_field_count"], 0)

if __name__ == "__main__":
    unittest.main()
