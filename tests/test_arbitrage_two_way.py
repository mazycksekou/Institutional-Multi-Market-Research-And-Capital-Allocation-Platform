import unittest

from automation_scheduler.arbitrage.two_way_arbitrage import (
    detect_cross_book_moneyline_arbitrage,
    detect_cross_book_spread_arbitrage,
    detect_cross_book_total_arbitrage,
    detect_two_way_arbitrage,
)


class TestArbitrageTwoWay(unittest.TestCase):
    def test_two_way_and_cross_book_arbitrage(self):
        offers = [
            {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 110},
            {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "moneyline", "selection": "Celtics", "odds": 110},
        ]
        self.assertTrue(detect_two_way_arbitrage(offers, market_identity_confidence=90)["candidate_found"])
        self.assertTrue(detect_cross_book_moneyline_arbitrage(offers, market_identity_confidence=90)["candidate_found"])
        self.assertTrue(detect_cross_book_spread_arbitrage(offers, market_identity_confidence=90)["candidate_found"])
        self.assertTrue(detect_cross_book_total_arbitrage(offers, market_identity_confidence=90)["candidate_found"])

    def test_low_confidence_blocks_candidate(self):
        result = detect_two_way_arbitrage(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 110},
                {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "moneyline", "selection": "Celtics", "odds": 110},
            ],
            market_identity_confidence=80,
        )
        self.assertFalse(result["candidate_found"])
