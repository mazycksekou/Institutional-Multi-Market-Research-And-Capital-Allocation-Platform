import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.automation_scheduler_legacy.nfl_open_data_adapters as nfl_open_data_adapters
from src.services.streamlit_dashboard_facade import NflOpenDataAdapter, adapter_by_id


class TestNflOpenDataAdapters(unittest.TestCase):
    def test_adapter_contract_methods_exist(self):
        adapter = adapter_by_id("nflverse_schedules_results")
        self.assertIsNotNone(adapter)
        for name in (
            "describe_source",
            "resolve_source_metadata",
            "list_expected_fields",
            "run_tiny_sample",
            "run_one_season_import",
            "run_full_available_backfill",
            "validate_sample_shape",
            "normalize_records",
            "write_compact_validated_rows",
            "build_compact_report",
        ):
            self.assertTrue(callable(getattr(adapter, name)))

    def test_tiny_sample_requires_allow_download_and_makes_no_call_when_blocked(self):
        adapter = adapter_by_id("nflverse_schedules_results")
        with patch('src.automation_scheduler_legacy.nfl_open_data_adapters.urllib.request.urlopen') as urlopen:
            report = adapter.run_tiny_sample(allow_download=False)
        self.assertFalse(report["ok"])
        self.assertEqual(report["blocked_reason"], "download_not_allowed")
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 0)
        urlopen.assert_not_called()

    def test_one_season_and_full_backfill_gates_are_enforced(self):
        adapter = adapter_by_id("nflverse_schedules_results")
        one = adapter.run_one_season_import(allow_download=True, tiny_sample_passed=False)
        full = adapter.run_full_available_backfill(allow_download=True, one_season_passed=False)
        self.assertEqual(one["blocked_reason"], "tiny_sample_required")
        self.assertEqual(full["blocked_reason"], "one_season_required")

    def test_terms_review_source_returns_clean_blocker(self):
        adapter = adapter_by_id("nflverse_ftn_charting_blocked")
        report = adapter.run_tiny_sample(allow_download=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["blocked_reason"], "terms_review_required")
        self.assertEqual(report["downloads_attempted"], 0)

    def test_sample_normalizes_compact_rows_and_writes_no_raw_payload(self):
        adapter = adapter_by_id("nflverse_schedules_results")
        metadata = {
            "ok": True,
            "seasons_available": ["2024"],
            "provider_calls_attempted": 1,
            "provider_calls_succeeded": 1,
            "_assets_private": [
                {
                    "asset_name_or_dataset_ref": "games.csv",
                    "season": None,
                    "file_format": "csv",
                    "_download_url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv",
                }
            ],
        }
        rows = [
            {"game_id": "2024_01_BAL_KC", "season": "2024", "week": "1", "home_team": "KC", "away_team": "BAL", "home_score": "27", "away_score": "20"},
            {"game_id": "2024_02_BUF_MIA", "season": "2024", "week": "2", "home_team": "MIA", "away_team": "BUF", "home_score": "31", "away_score": "28"},
        ]
        with patch.object(NflOpenDataAdapter, "resolve_source_metadata", return_value=metadata), patch(
            'src.automation_scheduler_legacy.nfl_open_data_adapters._iter_csv_rows_from_url',
            return_value=(list(rows[0]), rows, len(rows)),
        ):
            report = adapter.run_tiny_sample(allow_download=True, max_records=10)
            with tempfile.TemporaryDirectory() as tmp:
                paths = adapter.write_compact_validated_rows(report, base_data_dir=tmp)
                latest = Path(tmp, paths["latest_json_path"])
                rendered = latest.read_text(encoding="utf-8").lower()

        self.assertTrue(report["ok"])
        self.assertEqual(report["records_validated"], 2)
        self.assertEqual(report["downloads_attempted"], 1)
        self.assertEqual(report["downloads_succeeded"], 1)
        self.assertEqual(report["provider_calls_attempted"], 1)
        self.assertEqual(report["sample_rows"][0]["source_id"], "nflverse_schedules_results")
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertIn("data_sources/nfl_open_data/validated/nflverse_schedules_results/latest.json", paths["latest_json_path"])
        self.assertNotIn("browser_download_url", rendered)
        self.assertNotIn("provider_payload", rendered)

    def test_adapter_module_uses_no_browser_or_html_scraping(self):
        source = inspect.getsource(nfl_open_data_adapters)
        self.assertIn("urllib.request", source)
        self.assertNotIn("BeautifulSoup", source)
        self.assertNotIn("playwright", source)
        self.assertNotIn("selenium", source)
        self.assertNotIn("requests_html", source)


if __name__ == "__main__":
    unittest.main()
