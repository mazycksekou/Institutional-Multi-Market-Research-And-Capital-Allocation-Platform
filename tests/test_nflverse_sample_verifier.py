import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class FakeAdapter:
    def __init__(self, result):
        self.result = result

    def run_tiny_sample(self, **kwargs):
        return self.result


class TestNflverseSampleVerifier(unittest.TestCase):
    def test_report_counts_open_and_blocked_sources(self):
        def lookup(source_id):
            if source_id in {"nflverse_schedules_results", "nflverse_rosters"}:
                return FakeAdapter({"status": "sample_ready", "records_validated": 2, "records_rejected": 0, "fields_available": ["game_id", "season"], "field_count": 2, "downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1, "provider_calls_succeeded": 1, "provider_calls_failed": 0, "blocked_reason": None})
            return FakeAdapter({"status": "blocked", "blocked_reason": "terms_review_required", "records_validated": 0, "records_rejected": 0, "fields_available": [], "field_count": 0, "downloads_attempted": 1, "downloads_succeeded": 0, "provider_calls_attempted": 1, "provider_calls_succeeded": 0, "provider_calls_failed": 1})

        with patch.object(mod, "nfl_adapter_by_id", side_effect=lookup):
            report = mod.build_nflverse_sample_verification_report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["report_name"], "NFLVERSE_SAMPLE_VERIFICATION_REPORT")
        self.assertEqual(report["sample_verified_count"], 2)
        self.assertGreaterEqual(report["sample_blocked_count"], 3)


if __name__ == "__main__":
    unittest.main()
