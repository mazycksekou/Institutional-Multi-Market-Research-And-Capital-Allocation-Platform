import unittest
from model_governance.governance_health import get_governance_health


class TestGovernanceHealth(unittest.TestCase):
    def test_safe_json(self):
        r = get_governance_health()
        self.assertFalse(r["auto_execution_enabled"])
        self.assertIn("backtest_ready_count", r)
        self.assertIn("blocked_by_performance_count", r)
