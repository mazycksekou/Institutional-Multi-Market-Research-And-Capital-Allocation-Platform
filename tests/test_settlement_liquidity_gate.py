import unittest
from model_governance.settlement_liquidity_gate import evaluate_settlement_liquidity_gate

class TestSettlementLiquidityGate(unittest.TestCase):
    def test_blocks(self):
        r = evaluate_settlement_liquidity_gate(settlement_rule_match=False, liquidity_score=40)
        self.assertEqual(r['gate_result'], 'blocked_by_governance')
