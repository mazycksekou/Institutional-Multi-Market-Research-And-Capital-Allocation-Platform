import unittest

from src.data.odds_line_monitor import monitor_odds_lines
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestOddsLineMonitor(unittest.TestCase):
    def test_detects_odds_movement_candidates(self):
        config = get_default_scheduler_config()
        result = monitor_odds_lines(
            previous_snapshot=[{"event_id": "1", "market": "moneyline", "selection": "A", "odds_american": -110, "line": 0}],
            current_snapshot=[{"event_id": "1", "market": "moneyline", "selection": "A", "odds_american": -130, "line": 0, "books": [{"odds_american": -130}, {"odds_american": -110}]}],
            provider="sportsbooks",
            config=config,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertTrue(result["candidates"][0]["movement"]["steam"])
