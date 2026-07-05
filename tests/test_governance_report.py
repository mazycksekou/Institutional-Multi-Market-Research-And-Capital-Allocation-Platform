import unittest
from src.analytics.reports import generate_governance_report

class TestGovernanceReport(unittest.TestCase):
    def test_summary(self):
        r = generate_governance_report(
            [{"model_id": "m1", "activation_tier": "research_only"}],
            {"model_inventory_count": 1, "research_only_count": 1},
        )
        self.assertIn('inventory_summary', r)
