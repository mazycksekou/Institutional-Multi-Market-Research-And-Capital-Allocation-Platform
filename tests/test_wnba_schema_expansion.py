import unittest

from automation_scheduler.wnba_schema_expansion import build_wnba_schema_expansion_report


class TestWnbaSchemaExpansion(unittest.TestCase):
    def test_wnba_schema_expansion_includes_lineup_continuity(self):
        report = build_wnba_schema_expansion_report()
        fields = {row["field_name"] for row in report["new_fields_created"]}
        self.assertEqual(report["sport"], "basketball_wnba")
        self.assertIn("lineup_continuity", fields)


if __name__ == "__main__":
    unittest.main()
