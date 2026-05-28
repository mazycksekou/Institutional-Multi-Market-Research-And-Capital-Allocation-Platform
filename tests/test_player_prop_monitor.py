import unittest

from automation_scheduler.player_prop_monitor import monitor_player_props
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestPlayerPropMonitor(unittest.TestCase):
    def test_detects_prop_line_movement(self):
        config = get_default_scheduler_config()
        result = monitor_player_props(
            previous_snapshot=[{"player": "Player A", "market": "points", "selection": "over", "line": 24.5, "odds_american": -110}],
            current_snapshot=[{"player": "Player A", "market": "points", "selection": "over", "line": 26.5, "odds_american": -120, "sample_size": 20}],
            provider="odds_api",
            config=config,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertGreater(result["candidates"][0]["movement_strength"], 0)
