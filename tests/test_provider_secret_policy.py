import os
import unittest

from src.providers.policy.secret_policy import (
    assert_no_secret_leak,
    credential_status_from_env,
    list_required_secret_names,
    redact_mapping,
    redact_secret,
)


class TestProviderSecretPolicy(unittest.TestCase):
    def test_redact_secret_and_mapping(self):
        self.assertEqual(redact_secret("abc"), "[redacted]")
        payload = {
            "api_key": "secret_value",
            "nested": {"Authorization": "Bearer abc"},
            "normal": "ok",
            "token_hint": "sk_1234567890123456",
        }
        redacted = redact_mapping(payload)
        self.assertEqual(redacted["api_key"], "[redacted]")
        self.assertEqual(redacted["nested"]["Authorization"], "[redacted]")
        self.assertEqual(redacted["token_hint"], "[redacted]")
        self.assertEqual(redacted["normal"], "ok")

    def test_assert_no_secret_leak(self):
        safe = {"api_key": "[redacted]", "nested": {"token": "[redacted]"}}
        assert_no_secret_leak(safe)
        with self.assertRaises(ValueError):
            assert_no_secret_leak({"api_key": "live_value"})

    def test_credential_status_from_env(self):
        self.assertEqual(list_required_secret_names("sharp_sportsbook"), ["SHARP_API_KEY"])
        self.assertEqual(list_required_secret_names("kalshi_prediction_market"), ["KALSHI_API_KEY", "KALSHI_API_SECRET"])
        os.environ.pop("SHARP_API_KEY", None)
        os.environ.pop("KALSHI_API_KEY", None)
        os.environ.pop("KALSHI_API_SECRET", None)
        missing = credential_status_from_env("sharp_sportsbook")
        self.assertEqual(missing["status"], "missing_credentials")
        missing_kalshi = credential_status_from_env("kalshi_prediction_market")
        self.assertEqual(missing_kalshi["status"], "missing_credentials")
        os.environ["SHARP_API_KEY"] = "test_key_1234567890"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = "kalshi_secret_1234567890"
        ok = credential_status_from_env("sharp_sportsbook")
        self.assertEqual(ok["status"], "ok")
        ok_kalshi = credential_status_from_env("kalshi_prediction_market")
        self.assertEqual(ok_kalshi["status"], "ok")
        os.environ.pop("SHARP_API_KEY", None)
        os.environ.pop("KALSHI_API_KEY", None)
        os.environ.pop("KALSHI_API_SECRET", None)


if __name__ == "__main__":
    unittest.main()
