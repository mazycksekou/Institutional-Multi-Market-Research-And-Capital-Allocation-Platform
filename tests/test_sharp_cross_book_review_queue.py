import os
import unittest
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

from automation_scheduler import get_scheduler_review_queue
from automation_scheduler.response_compactor import compact_review_queue_response
from automation_scheduler.scheduler_runner import run_scheduler_once


def _single_book_snapshot() -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "ok": True,
        "status": "live_snapshot_complete",
        "provider_id": "sharp_sportsbook",
        "provider_enabled": True,
        "live_calls_enabled": True,
        "credential_status": "ok",
        "records_received": 2,
        "records_valid": 2,
        "records_rejected": 0,
        "schema_version": "automation_scheduler.v1.sharp_sportsbook.v1",
        "records": [
            {
                "provider_id": "sharp_sportsbook",
                "event_id": "evt2",
                "event_name": "C vs D",
                "sport": "basketball",
                "league": "NBA",
                "book": "book_a",
                "market": "moneyline",
                "selection": "c",
                "odds": -110,
                "implied_probability": 0.52381,
                "timestamp": now_iso,
            },
            {
                "provider_id": "sharp_sportsbook",
                "event_id": "evt2",
                "event_name": "C vs D",
                "sport": "basketball",
                "league": "NBA",
                "book": "book_a",
                "market": "moneyline",
                "selection": "d",
                "odds": -110,
                "implied_probability": 0.52381,
                "timestamp": now_iso,
            },
        ],
        "blockers": [],
        "timestamp": now_iso,
    }


class TestSharpCrossBookReviewQueue(unittest.TestCase):
    def setUp(self):
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        os.environ["SHARP_API_KEY"] = "sharp_key_test_value"

    def tearDown(self):
        os.environ.pop("SHARP_PROVIDER_ENABLED", None)
        os.environ.pop("SHARP_LIVE_READS_ENABLED", None)
        os.environ.pop("SHARP_API_KEY", None)

    @patch("automation_scheduler.scheduler_runner.SharpSportsbookAdapter.fetch_snapshot")
    def test_single_book_no_fake_arbitrage_and_compact_fields(self, mock_snapshot):
        mock_snapshot.return_value = _single_book_snapshot()
        with TemporaryDirectory() as tmp:
            run_scheduler_once(base_data_dir=tmp, dry_run=True)
            queue_payload = get_scheduler_review_queue(base_data_dir=tmp)
            compact = compact_review_queue_response(queue_payload)
            self.assertGreaterEqual(compact["count"], 1)
            self.assertLessEqual(len(compact["items"]), 10)
            self.assertNotIn("raw_payload", str(compact).lower())
            self.assertNotIn("provider_payload", str(compact).lower())
            self.assertNotIn("guaranteed", str(compact).lower())
            self.assertTrue(all(item.get("auto_execution_enabled") is False for item in compact["items"]))
            self.assertTrue(all(item.get("candidate_type") != "arbitrage_candidate" for item in compact["items"]))
            first = compact["items"][0]
            self.assertIn("provider_id", first)
            self.assertIn("event_id", first)
            self.assertIn("best_odds", first)
            self.assertIn("recommended_action", first)


if __name__ == "__main__":
    unittest.main()
