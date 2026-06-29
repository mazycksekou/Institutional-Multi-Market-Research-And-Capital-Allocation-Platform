import unittest

from src.services.streamlit_dashboard_facade import SAMPLE_DRY_RUN_PAYLOAD, normalize_payload, validate_payload


class TestPlayerPropsAdapterContract(unittest.TestCase):
    def test_normalizes(self):
        result = validate_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertTrue(result["ok"])
        normalized = normalize_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertEqual(normalized["player_name"], SAMPLE_DRY_RUN_PAYLOAD["player_name"])
        self.assertIn("line", normalized)


if __name__ == "__main__":
    unittest.main()

