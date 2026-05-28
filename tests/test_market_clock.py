import unittest
from datetime import datetime, timedelta, timezone

from automation_scheduler.market_clock import apply_score_decay, is_market_closed, is_stale


class TestMarketClock(unittest.TestCase):
    def test_market_close_detection(self):
        now = datetime.now(timezone.utc)
        self.assertTrue(is_market_closed({"close_at": (now - timedelta(seconds=1)).isoformat()}, now))
        self.assertFalse(is_market_closed({"close_at": (now + timedelta(minutes=5)).isoformat()}, now))

    def test_stale_detection_and_score_decay(self):
        now = datetime.now(timezone.utc)
        stale_item = {
            "updated_at": (now - timedelta(minutes=20)).isoformat(),
            "stale_after_seconds": 300,
        }
        self.assertTrue(is_stale(stale_item, now))
        self.assertEqual(apply_score_decay(90, 1800), 84.0)
