import unittest
from model_governance.governance_report import generate_governance_report

class TestGovernanceReport(unittest.TestCase):
    def test_summary(self):
        r = generate_governance_report()
        self.assertIn('inventory_summary', r)
