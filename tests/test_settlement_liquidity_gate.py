import unittest
from src.analytics.model_governance.settlement_liquidity_gate import evaluate_settlement_liquidity_gate

class TestSettlementLiquidityGate(unittest.TestCase):
    def test_blocks(self):
        r = evaluate_settlement_liquidity_gate(settlement_rule_match=False, liquidity_score=40)
        self.assertEqual(r['gate_result'], 'blocked_by_governance')

    def test_low_liquidity_blocks_prediction_market(self):
        r = evaluate_settlement_liquidity_gate(
            prediction_market_resolution_match=True,
            liquidity_score=35,
        )
        self.assertEqual(r["gate_result"], "blocked_by_governance")

    def test_prediction_market_with_liquidity_and_settlement_rule_is_approved(self):
        r = evaluate_settlement_liquidity_gate(
            prediction_market_resolution_match=True,
            liquidity_score=80,
        )
        self.assertEqual(r["gate_result"], "approved")
