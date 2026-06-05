import unittest

from automation_scheduler.nba_schema_expansion import build_nba_schema_expansion_report


class TestNbaSchemaExpansion(unittest.TestCase):
    def test_nba_schema_expansion_has_cutoff_safe_fields(self):
        report = build_nba_schema_expansion_report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["sport"], "basketball_nba")
        self.assertGreater(report["new_fields_created_count"], 0)
        self.assertTrue(all(row["cutoff_safe"] for row in report["new_fields_created"]))


if __name__ == "__main__":
    unittest.main()
