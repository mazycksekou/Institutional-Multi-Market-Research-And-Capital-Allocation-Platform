import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class FakeAdapter:
    def run_tiny_sample(self, **kwargs):
        return {"status": "blocked", "blocked_reason": "no_records_found", "records_validated": 0, "records_rejected": 0, "fields_available": [], "field_count": 0, "downloads_attempted": 1, "downloads_succeeded": 0, "provider_calls_attempted": 1, "provider_calls_succeeded": 0, "provider_calls_failed": 1}


class TestMlbRetrosheetPitchByPitchLoader(unittest.TestCase):
    def test_loader_returns_safe_blocked_sample(self):
        with patch.object(mod, "mlb_adapter_by_id", return_value=FakeAdapter()):
            report = mod.load_mlb_retrosheet_pitch_by_pitch_sample()
        self.assertEqual(report["source_id"], "retrosheet_play_by_play_events")
        self.assertEqual(report["blocked_reason"], "no_records_found")


if __name__ == "__main__":
    unittest.main()
