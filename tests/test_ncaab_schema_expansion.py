import unittest

from automation_scheduler.ncaab_schema_expansion import build_ncaab_schema_expansion_report


class TestNcaabSchemaExpansion(unittest.TestCase):
    def test_ncaab_schema_expansion_includes_college_context(self):
        report = build_ncaab_schema_expansion_report()
        fields = {row["field_name"] for row in report["new_fields_created"]}
        self.assertEqual(report["sport"], "basketball_ncaab")
        self.assertIn("conference_tournament_context", fields)


if __name__ == "__main__":
    unittest.main()
