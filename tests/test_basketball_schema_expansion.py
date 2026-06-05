import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS, build_basketball_schema_expansion_report


class TestBasketballSchemaExpansion(unittest.TestCase):
    def test_schema_expansion_creates_sourced_fields_and_tables(self):
        report = build_basketball_schema_expansion_report()
        self.assertTrue(report["ok"])
        self.assertGreater(report["new_fields_created_count"], 0)
        self.assertGreater(report["new_tables_created_count"], 0)
        self.assertEqual({row["sport"] for row in report["new_fields_created"]}, set(SPORTS))
        for row in report["new_fields_created"]:
            self.assertIn("source_url_hash", row)
            self.assertNotIn("http", str(row["source_url_hash"]).lower())
            self.assertIn("field_catalog_entry", row)
            self.assertTrue(row["tests"])


if __name__ == "__main__":
    unittest.main()
