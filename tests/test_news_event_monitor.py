import unittest

from src.market_intelligence.news_event_monitor import monitor_news_events
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestNewsEventMonitor(unittest.TestCase):
    def test_assigns_event_severity(self):
        config = get_default_scheduler_config()
        result = monitor_news_events(
            events=[{"symbol": "AAPL", "headline": "Earnings guidance cut", "event_severity": "high"}],
            provider="news_provider",
            config=config,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["event_severity"], "high")
