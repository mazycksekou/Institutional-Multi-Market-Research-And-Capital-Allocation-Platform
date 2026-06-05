import unittest

from automation_scheduler.nfl_mlb_active_discovery import build_paid_retrieval_enrichment_report


class TestNflPaidRetrievalEnrichment(unittest.TestCase):
    def test_paid_mode_reports_enabled_count(self):
        report = build_paid_retrieval_enrichment_report(sport="nfl", allow_oxylabs=True, allow_paid_retrieval=True)
        self.assertEqual(report["paid_source_enabled_count"], 1)
        self.assertGreaterEqual(report["existing_fields_total"], report["existing_fields_populated_before"])


if __name__ == "__main__":
    unittest.main()

