import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafSchemaExpansion(unittest.TestCase):
    def test_schema_fields_created(self):
        report = ncaaf_artifacts()["schema"]
        self.assertGreater(report["new_fields_created_count"], 0)
        self.assertGreater(report["new_tables_created_count"], 0)

if __name__ == "__main__":
    unittest.main()
