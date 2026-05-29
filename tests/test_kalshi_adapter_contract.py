import unittest

from automation_scheduler.kalshi_adapter_contract import SAMPLE_DRY_RUN_PAYLOAD, normalize_payload, validate_payload


class TestKalshiAdapterContract(unittest.TestCase):
    def test_normalizes(self):
        result = validate_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertTrue(result["ok"])
        normalized = normalize_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertIn("market_id", normalized)
        self.assertIn("implied_probability", normalized)


if __name__ == "__main__":
    unittest.main()

