import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class FakeAdapter:
    def run_tiny_sample(self, **kwargs):
        return {"status": "no_records_found", "blocked_reason": "no_records_found", "records_validated": 0, "records_rejected": 0, "fields_available": [], "field_count": 0, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 1, "provider_calls_succeeded": 0, "provider_calls_failed": 1}


class TestStructuredWikiSeedLoader(unittest.TestCase):
    def test_loader_returns_safe_no_records_result(self):
        with patch.object(mod, "mlb_structured_seed_adapter_by_id", return_value=FakeAdapter()):
            report = mod.load_structured_wiki_seed_sample()
        self.assertEqual(report["source_id"], "wikidata_mlb_seed")
        self.assertEqual(report["records_validated"], 0)


if __name__ == "__main__":
    unittest.main()
