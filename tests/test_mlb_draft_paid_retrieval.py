import unittest

from automation_scheduler.nfl_mlb_active_discovery import build_schema_expansion_report


class TestMlbDraftPaidRetrieval(unittest.TestCase):
    def test_draft_schema_is_proposed(self):
        report = build_schema_expansion_report(sport="mlb")
        fields = {row["field_name"] for row in report["new_fields_created"]}
        self.assertIn("draft_pick_origin", fields)


if __name__ == "__main__":
    unittest.main()

