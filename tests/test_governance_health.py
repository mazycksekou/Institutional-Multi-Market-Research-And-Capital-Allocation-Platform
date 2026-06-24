import unittest
from src.analytics.governance import build_governance_health


class TestGovernanceHealth(unittest.TestCase):
    def test_safe_json(self):
        r = build_governance_health(
            {"model_inventory_count": 1, "active_scoring_ready_count": 1, "production_candidate_count": 0},
            {"blocked_model_count": 0},
        )
        self.assertFalse(r["auto_execution_enabled"])
        self.assertIn("backtest_ready_count", r)
        self.assertIn("blocked_by_performance_count", r)
