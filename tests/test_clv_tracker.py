import json
import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.clv_tracker import calculate_clv, write_clv_record


class TestClvTracker(unittest.TestCase):
    def test_clv_tracker_writes_clv_ready_record(self):
        with TemporaryDirectory() as tmp:
            result = write_clv_record(
                {
                    "event": "Lakers vs Celtics",
                    "market": "moneyline",
                    "selection": "Lakers",
                    "opening_odds": 100,
                    "current_odds": 110,
                    "closing_odds": 120,
                },
                base_dir=tmp,
            )
            with open(result["path"], "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("clv", payload)
            self.assertEqual(calculate_clv(100, 110, 120)["opening_to_closing"], 20)
