import unittest

from automation_scheduler.nfl_mlb_active_discovery import build_schema_expansion_report


class TestNflSchemaExpansion(unittest.TestCase):
    def test_nfl_proposals_exist(self):
        report = build_schema_expansion_report(sport="nfl")
        self.assertGreater(report["new_fields_created_count"], 0)
        self.assertTrue(any(row["field_name"] == "coaching_staff_role_history" for row in report["new_fields_created"]))


if __name__ == "__main__":
    unittest.main()

