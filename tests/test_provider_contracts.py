import unittest

from automation_scheduler.provider_contracts import PROVIDER_TYPES, get_default_provider_contracts


class TestProviderContracts(unittest.TestCase):
    def test_contract_fields_and_types(self):
        contracts = get_default_provider_contracts()
        self.assertGreaterEqual(len(contracts), 7)
        required = {
            "provider_id",
            "provider_name",
            "provider_type",
            "enabled",
            "dry_run",
            "supports_streaming",
            "supports_polling",
            "min_poll_seconds",
            "rate_limit_note",
            "credential_status",
            "required_credentials",
            "supported_markets",
            "output_schema_version",
            "last_health_status",
            "live_calls_enabled",
        }
        for contract in contracts.values():
            self.assertTrue(required.issubset(contract.keys()))
            self.assertIn(contract["provider_type"], PROVIDER_TYPES)
            self.assertFalse(contract["enabled"])
            self.assertTrue(contract["dry_run"])
            self.assertFalse(contract["live_calls_enabled"])


if __name__ == "__main__":
    unittest.main()

