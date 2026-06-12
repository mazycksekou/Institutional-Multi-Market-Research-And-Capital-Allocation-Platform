import json
import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.backtesting_engine import (
    load_historical_rows,
    replay_rows,
    summarize_replay_result,
    write_replay_result,
)


class TestHistoricalReplay(unittest.TestCase):
    def test_local_rows_only(self):
        with self.assertRaises(ValueError):
            load_historical_rows("https://example.com/rows.json")

    def test_replay_and_write(self):
        rows = [
            {
                "event_id": "e1",
                "market_type": "moneyline",
                "event_name": "A vs B",
                "market_name": "moneyline",
                "selection_name": "A",
                "odds": 120,
                "model_probability": 0.57,
                "closing_odds": 100,
                "result_status": "win",
                "timestamp": "2026-05-01T00:00:00Z",
            }
        ]
        replay = replay_rows(rows, model_id="m1")
        summary = summarize_replay_result(replay)
        self.assertEqual(summary["status"], "backtest_complete")
        with TemporaryDirectory() as tmp:
            path = write_replay_result(replay, base_dir=tmp)
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["sample_size"], 1)


if __name__ == "__main__":
    unittest.main()

