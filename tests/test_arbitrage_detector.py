import unittest

from automation_scheduler.arbitrage_detector import detect_arbitrage


class TestArbitrageDetector(unittest.TestCase):
    def test_two_way_arbitrage_math_works(self):
        result = detect_arbitrage(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 110, "timestamp": 100},
                {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "match winner", "selection": "Celtics", "odds": 110, "timestamp": 110},
            ],
            total_stake=100,
            market_identity_confidence=95,
        )
        self.assertTrue(result["candidate_found"])
        self.assertEqual(result["candidate_type"], "arbitrage_candidate")
        self.assertLess(result["arbitrage_implied_sum"], 1.0)
        self.assertGreater(result["min_profit"], 0)

    def test_no_false_arbitrage_when_vig_exists(self):
        result = detect_arbitrage(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": -110},
                {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "match winner", "selection": "Celtics", "odds": -110},
            ],
            market_identity_confidence=95,
        )
        self.assertFalse(result["candidate_found"])
        self.assertEqual(result["reason"], "no_arbitrage_after_vig")

    def test_stale_or_low_confidence_blocks_candidate(self):
        stale = detect_arbitrage(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 110, "timestamp": 0},
                {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "match winner", "selection": "Celtics", "odds": 110, "timestamp": 1000},
            ],
            market_identity_confidence=95,
        )
        low_conf = detect_arbitrage(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 110},
                {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "match winner", "selection": "Celtics", "odds": 110},
            ],
            market_identity_confidence=80,
        )
        self.assertFalse(stale["candidate_found"])
        self.assertEqual(stale["reason"], "stale_data")
        self.assertFalse(low_conf["candidate_found"])
        self.assertEqual(low_conf["reason"], "low_market_identity_confidence")

    def test_three_way_arbitrage_math_works(self):
        result = detect_arbitrage(
            [
                {"bookmaker": "DraftKings", "event": "TeamA vs TeamB", "market": "1x2", "selection": "TeamA", "odds": 260, "timestamp": 100},
                {"bookmaker": "FanDuel", "event": "TeamA vs TeamB", "market": "1x2", "selection": "Draw", "odds": 360, "timestamp": 102},
                {"bookmaker": "BetMGM", "event": "TeamA vs TeamB", "market": "1x2", "selection": "TeamB", "odds": 320, "timestamp": 101},
            ],
            market_identity_confidence=95,
        )
        self.assertTrue(result["candidate_found"])
        self.assertLess(result["arbitrage_implied_sum"], 1.0)
