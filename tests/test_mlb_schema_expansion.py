import unittest

from automation_scheduler.nfl_mlb_active_discovery import build_schema_expansion_report


class TestMlbSchemaExpansion(unittest.TestCase):
    def test_mlb_proposals_exist(self):
        report = build_schema_expansion_report(sport="mlb")
        self.assertGreater(report["new_fields_created_count"], 0)
        self.assertTrue(any(row["field_name"] == "manager_coach_role_history" for row in report["new_fields_created"]))


if __name__ == "__main__":
    unittest.main()

