import unittest

from automation_scheduler.nfl_mlb_active_discovery import build_schema_expansion_report


class TestSchemaExpansionReport(unittest.TestCase):
    def test_new_fields_include_provenance(self):
        nfl_report = build_schema_expansion_report(sport="nfl")
        mlb_report = build_schema_expansion_report(sport="mlb")
        for report in (nfl_report, mlb_report):
            self.assertGreater(report["new_fields_created_count"], 0)
            for row in report["new_fields_created"]:
                for key in ("field_name", "source_id", "source_family", "source_url_hash", "retrieval_method", "first_seen_at", "validation_status", "cutoff_safe", "future_leakage_risk", "confidence"):
                    self.assertIn(key, row)


if __name__ == "__main__":
    unittest.main()

