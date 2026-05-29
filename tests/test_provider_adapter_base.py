import unittest

from automation_scheduler.provider_adapter_base import ProviderAdapterBase
from automation_scheduler.provider_contracts import get_default_provider_contracts


class TestProviderAdapterBase(unittest.TestCase):
    def test_default_disabled_dry_run_and_placeholder_fetch(self):
        contract = get_default_provider_contracts()["sportsbook_placeholder"]
        adapter = ProviderAdapterBase(contract)
        caps = adapter.get_capabilities()
        self.assertFalse(caps["enabled"])
        self.assertTrue(caps["dry_run"])
        self.assertFalse(caps["live_calls_enabled"])
        fetched = adapter.fetch_snapshot()
        self.assertEqual(fetched["status"], "dry_run_placeholder")
        self.assertEqual(fetched["records"], [])

    def test_validate_config_missing_creds_no_crash(self):
        contract = get_default_provider_contracts()["sportsbook_placeholder"]
        contract["required_credentials"] = ["token"]
        adapter = ProviderAdapterBase(contract)
        result = adapter.validate_config()
        self.assertFalse(result["ok"])
        self.assertIn("missing_credentials", result["blockers"])


if __name__ == "__main__":
    unittest.main()

