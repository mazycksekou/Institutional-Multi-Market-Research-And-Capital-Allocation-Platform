import unittest

from src.services.streamlit_dashboard_facade import apply_arbitrage_risk_filters


class TestArbitrageRiskFilters(unittest.TestCase):
    def test_stale_price_and_settlement_mismatch_block(self):
        result = apply_arbitrage_risk_filters(
            timestamps=[0, 500],
            rule_sets=[{"includes_overtime": True}, {"includes_overtime": False}],
            liquidity_score_value=2,
        )
        self.assertTrue(result["blocked"])
        self.assertIn("stale_data", result["blockers"])
        self.assertIn("settlement_mismatch", result["blockers"])
