import unittest
from model_governance.governance_config import default_governance_config

class TestGovernanceConfig(unittest.TestCase):
    def test_safe_defaults(self):
        cfg = default_governance_config()
        self.assertTrue(cfg['human_approval_required'])
        self.assertFalse(cfg['auto_bet_enabled'])
        self.assertFalse(cfg['auto_trade_enabled'])
        self.assertFalse(cfg['auto_execution_enabled'])
        self.assertTrue(cfg['paper_execution_only'])
