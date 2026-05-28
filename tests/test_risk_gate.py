import unittest

from model_governance.risk_gate import evaluate_risk_gate


class TestRiskGate(unittest.TestCase):
    def test_risk_gate_blocks_unacceptable_risk(self):
        result = evaluate_risk_gate(
            drawdown_risk=0.5,
            tail_risk=0.6,
            liquidity_risk=0.5,
            settlement_risk=0.4,
            correlation_risk=0.5,
            market_regime_risk=0.5,
            execution_risk=0.5,
            risk_of_ruin=0.6,
        )
        self.assertFalse(result["passes_gate"])

