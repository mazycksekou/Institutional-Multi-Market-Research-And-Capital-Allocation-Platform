import unittest

from src.providers.normalization import get_normalized_schema, normalize_provider_payload
from src.providers.sportsbooks import SAMPLE_DRY_RUN_PAYLOAD as SPORTSBOOK_SAMPLE


class TestProviderNormalizationContract(unittest.TestCase):
    def test_dispatch_and_schema(self):
        normalized = normalize_provider_payload("sportsbook_odds", SPORTSBOOK_SAMPLE)
        schema = get_normalized_schema("sportsbook_odds")
        for key in schema:
            self.assertIn(key, normalized)


if __name__ == "__main__":
    unittest.main()
