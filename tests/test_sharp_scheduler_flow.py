import os
import unittest
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

from automation_scheduler import get_scheduler_review_queue
from automation_scheduler.scheduler_runner import run_scheduler_once


def _sharp_snapshot_two_books() -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "ok": True,
        "status": "live_snapshot_complete",
        "provider_id": "sharp_sportsbook",
        "provider_enabled": True,
        "live_calls_enabled": True,
        "credential_status": "ok",
        "dry_run": False,
        "records_received": 4,
        "records_valid": 4,
        "records_rejected": 0,
        "schema_version": "automation_scheduler.v1.sharp_sportsbook.v1",
        "records": [
            {
                "provider_id": "sharp_sportsbook",
                "event_id": "evt1",
                "event_name": "A vs B",
                "sport": "basketball",
                "league": "NBA",
                "book": "book_a",
                "market": "moneyline",
                "selection": "a",
                "odds": 120,
                "implied_probability": 0.454545,
                "timestamp": now_iso,
            },
            {
                "provider_id": "sharp_sportsbook",
                "event_id": "evt1",
                "event_name": "A vs B",
                "sport": "basketball",
                "league": "NBA",
                "book": "book_b",
                "market": "moneyline",
                "selection": "a",
                "odds": 110,
                "implied_probability": 0.47619,
                "timestamp": now_iso,
                "model_probability": 0.56,
                "no_vig_probability": 0.55,
            },
            {
                "provider_id": "sharp_sportsbook",
                "event_id": "evt1",
                "event_name": "A vs B",
                "sport": "basketball",
                "league": "NBA",
                "book": "book_a",
                "market": "moneyline",
                "selection": "b",
                "odds": 120,
                "implied_probability": 0.454545,
                "timestamp": now_iso,
            },
            {
                "provider_id": "sharp_sportsbook",
                "event_id": "evt1",
                "event_name": "A vs B",
                "sport": "basketball",
                "league": "NBA",
                "book": "book_b",
                "market": "moneyline",
                "selection": "b",
                "odds": 110,
                "implied_probability": 0.47619,
                "timestamp": now_iso,
            },
        ],
        "blockers": [],
        "timestamp": now_iso,
    }


class TestSharpSchedulerFlow(unittest.TestCase):
    def setUp(self):
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        os.environ["SHARP_API_KEY"] = "sharp_key_test_value"

    def tearDown(self):
        os.environ.pop("SHARP_PROVIDER_ENABLED", None)
        os.environ.pop("SHARP_LIVE_READS_ENABLED", None)
        os.environ.pop("SHARP_API_KEY", None)

    @patch("automation_scheduler.scheduler_runner.SharpSportsbookAdapter.fetch_snapshot")
    def test_sharp_records_flow_to_scheduler_read_only(self, mock_snapshot):
        mock_snapshot.return_value = _sharp_snapshot_two_books()
        with TemporaryDirectory() as tmp:
            result = run_scheduler_once(base_data_dir=tmp, dry_run=True)
            queue = get_scheduler_review_queue(base_data_dir=tmp)
            self.assertTrue(result["ok"])
            self.assertTrue(result["dry_run"])
            self.assertTrue(result["human_approval_required"])
            self.assertFalse(result["auto_execution_enabled"])
            self.assertFalse(result["auto_bet_enabled"])
            self.assertFalse(result["auto_trade_enabled"])
            self.assertEqual(result["records_received"], 4)
            self.assertEqual(result["records_valid"], 4)
            self.assertEqual(result["sharp_candidates_created"], 0)
            self.assertEqual(result["candidates_created"], 0)
            self.assertEqual(queue["count"], 0)
            self.assertEqual(queue["items"], [])


if __name__ == "__main__":
    unittest.main()
