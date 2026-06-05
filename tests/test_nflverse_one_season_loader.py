import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class FakeAdapter:
    def run_one_season_import(self, **kwargs):
        return {"status": "one_season_import_complete", "records_validated": 4, "records_rejected": 0, "fields_available": ["season", "week"], "field_count": 2, "downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1, "provider_calls_succeeded": 1, "provider_calls_failed": 0}


class TestNflverseOneSeasonLoader(unittest.TestCase):
    def test_loader_returns_one_season_result(self):
        with patch.object(mod, "nfl_adapter_by_id", return_value=FakeAdapter()):
            report = mod.load_nflverse_one_season_sample(source_id="nflverse_schedules_results", season=2024)
        self.assertEqual(report["source_id"], "nflverse_schedules_results")
        self.assertEqual(report["records_validated"], 4)


if __name__ == "__main__":
    unittest.main()
