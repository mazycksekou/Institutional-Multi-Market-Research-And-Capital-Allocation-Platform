import unittest

from automation_scheduler.news_events_adapter_contract import SAMPLE_DRY_RUN_PAYLOAD, normalize_payload, validate_payload


class TestNewsEventsAdapterContract(unittest.TestCase):
    def test_normalizes(self):
        result = validate_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertTrue(result["ok"])
        normalized = normalize_payload(SAMPLE_DRY_RUN_PAYLOAD)
        self.assertIn("source", normalized)
        self.assertIn("published_at", normalized)


if __name__ == "__main__":
    unittest.main()

