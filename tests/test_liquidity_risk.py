import unittest

from src.services.streamlit_dashboard_facade import block_low_liquidity_arbitrage, estimate_execution_feasibility, estimate_limit_risk, liquidity_score


class TestLiquidityRisk(unittest.TestCase):
    def test_liquidity_risk_score_and_blocking(self):
        score = liquidity_score(limit_estimate=1000, spread_percent=0.5, book_count=4)
        self.assertGreater(score, 5)
        self.assertGreaterEqual(estimate_execution_feasibility(liquidity_score_value=score, stale_odds_risk=0.1), 0)
        self.assertGreater(estimate_limit_risk(50, 100), 0)
        blocked = block_low_liquidity_arbitrage(liquidity_score_value=2)
        self.assertTrue(blocked["blocked"])
