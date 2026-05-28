import unittest

from automation_scheduler.market_identity_resolver import resolve_market_identity


class TestMarketIdentityResolver(unittest.TestCase):
    def test_matches_same_market_across_books(self):
        left = {"event": "Lakers vs Celtics", "market": "spread", "selection": "Lakers", "participant": "Lakers", "line": 3.5}
        right = {"event": "Celtics @ Lakers", "market": "point spread", "selection": "Lakers", "participant": "Lakers", "line": 3.5}
        result = resolve_market_identity(left, right)
        self.assertTrue(result["same_market_identity"])
        self.assertGreaterEqual(result["confidence"], 85)

    def test_rejects_false_matches(self):
        left = {"event": "Lakers vs Celtics", "market": "spread", "selection": "Lakers", "participant": "Lakers", "line": 3.5}
        right = {"event": "Yankees vs Red Sox", "market": "moneyline", "selection": "Yankees", "participant": "Yankees"}
        result = resolve_market_identity(left, right)
        self.assertFalse(result["same_market_identity"])
        self.assertLess(result["confidence"], 85)
