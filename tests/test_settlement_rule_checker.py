import unittest

from src.brokerage.settlement import compare_settlement_rules


class TestSettlementRuleChecker(unittest.TestCase):
    def test_settlement_rule_mismatch_detected(self):
        result = compare_settlement_rules(
            [
                {"includes_overtime": True, "void_on_push": False, "player_prop_settlement": "official"},
                {"includes_overtime": False, "void_on_push": False, "player_prop_settlement": "official"},
            ]
        )
        self.assertTrue(result["material_mismatch"])
        self.assertIn("overtime_rule_mismatch", result["mismatches"])
        self.assertFalse(result["overtime_rule_match"])
