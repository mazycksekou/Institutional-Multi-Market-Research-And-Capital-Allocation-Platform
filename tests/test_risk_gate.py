import unittest
from model_governance.risk_gate import evaluate_risk_gate

class TestRiskGate(unittest.TestCase):
    def test_blocks(self):
        r = evaluate_risk_gate(drawdown_risk=0.9, tail_risk=0.9, liquidity_risk=0.9, settlement_risk=0.9, correlation_risk=0.9, market_regime_risk=0.9, execution_risk=0.9, risk_of_ruin=0.9, max_loss=0.9, exposure_concentration=0.9)
        self.assertFalse(r['passes_gate'])
