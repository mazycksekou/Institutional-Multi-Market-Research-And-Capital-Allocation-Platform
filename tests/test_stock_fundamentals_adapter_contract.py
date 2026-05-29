import unittest

from automation_scheduler.stock_fundamentals_adapter_contract import SAMPLE_DRY_RUN_PAYLOAD, normalize_payload, validate_payload


class TestStockFundamentalsAdapterContract(unittest.TestCase):
    def test_normalizes(self):
        result = validate_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertTrue(result["ok"])
        normalized = normalize_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertIn("market_cap", normalized)
        self.assertIn("report_date", normalized)


if __name__ == "__main__":
    unittest.main()

