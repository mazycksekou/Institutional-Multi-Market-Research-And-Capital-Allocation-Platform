import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class FakeAdapter:
    def run_tiny_sample(self, **kwargs):
        return {"status": "no_records_found", "blocked_reason": "no_records_found", "records_validated": 0, "records_rejected": 0, "fields_available": [], "field_count": 0, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 1, "provider_calls_succeeded": 0, "provider_calls_failed": 1}


class TestStructuredWikiSampleVerifier(unittest.TestCase):
    def test_report_marks_wikidata_no_records_and_wikipedia_supplemental_only(self):
        with patch.object(mod, "mlb_structured_seed_adapter_by_id", return_value=FakeAdapter()):
            report = mod.build_structured_wiki_sample_verification_report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["report_name"], "STRUCTURED_WIKI_SAMPLE_VERIFICATION_REPORT")
        self.assertEqual(report["sample_no_records_count"], 1)


if __name__ == "__main__":
    unittest.main()
