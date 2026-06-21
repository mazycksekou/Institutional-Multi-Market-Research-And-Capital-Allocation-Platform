import unittest
from datetime import datetime, timedelta, timezone

from src.providers.validation import validate_provider_payload


class TestProviderPayloadValidator(unittest.TestCase):
    def test_rejects_malformed_odds_and_missing_fields(self):
        payload = {
            "event_id": "",
            "market": "",
            "selection": "",
            "odds": "bad",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result = validate_provider_payload("sportsbook_odds", payload)
        self.assertFalse(result["ok"])
        self.assertIn("malformed_odds", result["errors"])
        self.assertIn("missing_event_id", result["errors"])

    def test_rejects_stale_timestamp(self):
        stale = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        payload = {"event_id": "e1", "market": "h2h", "selection": "A", "odds": -110, "timestamp": stale}
        result = validate_provider_payload("sportsbook_odds", payload)
        self.assertFalse(result["ok"])
        self.assertIn("stale_timestamp", result["errors"])

    def test_rejects_unknown_provider_type(self):
        result = validate_provider_payload("unknown_type", {"timestamp": datetime.now(timezone.utc).isoformat()})
        self.assertFalse(result["ok"])
        self.assertIn("unknown_provider_type", result["errors"])


if __name__ == "__main__":
    unittest.main()
