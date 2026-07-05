import json
import re
import unittest
from tempfile import TemporaryDirectory

from src.services.streamlit_dashboard_facade import generate_backtest_report, run_backtest


class TestBacktestingEngine(unittest.TestCase):
    def test_generates_compact_and_full_report(self):
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
                "ev_percent": 3.2,
                "recommended_stake_percent": 1.2,
            }
        ]
        with TemporaryDirectory() as tmp:
            result = generate_backtest_report(model_id="m1", rows=rows, base_data_dir=tmp)
            compact = result["compact_report"]
            self.assertTrue(compact["ok"])
            self.assertNotIn("full_report", compact)
            with open(result["report_path"], "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["model_id"], "m1")

    def test_banned_language_not_present(self):
        result = run_backtest(
            model_id="m2",
            rows=[
                {
                    "event_id": "e2",
                    "market_type": "spread",
                    "event_name": "C vs D",
                    "market_name": "spread",
                    "selection_name": "C",
                    "odds": -110,
                    "model_probability": 0.54,
                    "closing_odds": -115,
                    "result_status": "loss",
                }
            ],
        )
        text = json.dumps(result).lower()
        self.assertIsNone(re.search(r"\block\b", text))
        for banned in ["guaranteed", "risk-free", "sure thing", "can't lose"]:
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
