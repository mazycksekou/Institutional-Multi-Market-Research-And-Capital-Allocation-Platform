import unittest

from automation_scheduler.ncaaw_schema_expansion import build_ncaaw_schema_expansion_report


class TestNcaawSchemaExpansion(unittest.TestCase):
    def test_ncaaw_schema_expansion_uses_ncaaw_not_ncaab(self):
        report = build_ncaaw_schema_expansion_report()
        self.assertEqual(report["sport"], "basketball_ncaaw")
        self.assertTrue(all(row["sport"] == "basketball_ncaaw" for row in report["new_fields_created"]))


if __name__ == "__main__":
    unittest.main()
