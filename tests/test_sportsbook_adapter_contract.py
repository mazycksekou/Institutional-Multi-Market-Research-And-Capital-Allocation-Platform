import unittest

from automation_scheduler.sportsbook_adapter_contract import SAMPLE_DRY_RUN_PAYLOAD, normalize_payload, validate_payload


class TestSportsbookAdapterContract(unittest.TestCase):
    def test_normalizes(self):
        result = validate_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertTrue(result["ok"])
        normalized = normalize_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertEqual(normalized["event_id"], SAMPLE_DRY_RUN_PAYLOAD["event_id"])
        self.assertIn("odds", normalized)


if __name__ == "__main__":
    unittest.main()

