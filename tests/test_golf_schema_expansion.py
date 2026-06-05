import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfSchemaExpansion(unittest.TestCase):
    def test_schema_expansion_tracks_verified_fields(self):
        report = golf_artifacts()["schema"]
        self.assertGreaterEqual(report["new_fields_created_count"], 8)
        self.assertGreaterEqual(report["new_tables_created_count"], 2)
        self.assertFalse(report["provider_write"])


if __name__ == "__main__":
    unittest.main()
