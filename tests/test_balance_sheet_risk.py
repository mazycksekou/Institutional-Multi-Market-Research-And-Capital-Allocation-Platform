import unittest

from src.services.streamlit_dashboard_facade import evaluate_balance_sheet


class TestBalanceSheetRisk(unittest.TestCase):
    def test_balance_sheet_ratios(self):
        result = evaluate_balance_sheet(
            {
                "cash_and_cash_equivalents": 10_000_000,
                "marketable_securities": 2_000_000,
                "accounts_receivable": 3_000_000,
                "inventory": 1_000_000,
                "current_assets": 20_000_000,
                "fixed_assets": 5_000_000,
                "current_liabilities": 10_000_000,
                "short_term_debt": 1_000_000,
                "long_term_debt": 4_000_000,
                "other_liabilities": 1_000_000,
                "shareholder_equity": 10_000_000,
            }
        )
        self.assertFalse(result["data_insufficient"])
        self.assertEqual(result["current_ratio"], 2.0)
        self.assertEqual(result["quick_ratio"], 1.5)
        self.assertEqual(result["cash_to_debt"], 2.0)

    def test_balance_sheet_risk_blockers(self):
        result = evaluate_balance_sheet(
            {
                "cash_and_cash_equivalents": 100_000,
                "current_assets": 400_000,
                "current_liabilities": 2_000_000,
                "short_term_debt": 1_000_000,
                "long_term_debt": 5_000_000,
                "preferred_stock": 3_000_000,
                "shareholder_equity": -2_000_000,
                "dilution_risk_score": 90,
                "offering_risk_score": 92,
            }
        )
        self.assertIn("negative_or_zero_shareholder_equity", result["risk_blockers"])
        self.assertIn("extreme_offering_risk", result["risk_blockers"])
        self.assertEqual(result["force_status"], "NO_REVIEW")

    def test_missing_balance_sheet_is_data_insufficient(self):
        result = evaluate_balance_sheet({})
        self.assertTrue(result["data_insufficient"])
        self.assertIn("balance_sheet_data_insufficient", result["risk_blockers"])


if __name__ == "__main__":
    unittest.main()
