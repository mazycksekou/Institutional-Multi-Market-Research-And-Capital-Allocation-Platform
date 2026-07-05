from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from scripts.check_openapi_contract import collect_openapi_report


ROOT = Path(__file__).resolve().parents[1]
BANNED_TERMS = ("OpenAI", "Custom GPT", "GPT Actions", "ChatGPT")


class OpenApiContractValidationTests(unittest.TestCase):
    def test_checked_in_contract_is_valid_and_vendor_neutral(self) -> None:
        report = collect_openapi_report(ROOT)
        self.assertTrue(report["ok"], json.dumps(report, indent=2, sort_keys=True))
        self.assertEqual(report["location"], "root")
        self.assertEqual(report["openapi_version"], "3.1.0")
        self.assertEqual(report["info_version"], "2.2.0")
        self.assertEqual(report["title"], "Betting Stock API")
        self.assertEqual(report["path_count"], 2)
        self.assertEqual(report["operation_count"], 2)
        self.assertEqual(report["schema_count"], 3)
        self.assertFalse(report["duplicate_operation_ids"])
        self.assertFalse(report["unresolved_refs"])
        text = Path(ROOT / "openapi.yaml").read_text(encoding="utf-8")
        for term in BANNED_TERMS:
            self.assertNotIn(term, text)

    def test_runtime_openapi_is_vendor_neutral(self) -> None:
        spec = importlib.util.spec_from_file_location("openapi_contract_main", ROOT / "main.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = module.app

        schema = app.openapi()
        payload = json.dumps(schema, sort_keys=True)
        for term in BANNED_TERMS:
            self.assertNotIn(term, payload)
        self.assertEqual(schema["info"]["title"], "Betting Stock API")
        self.assertEqual(schema["info"]["description"], "Public API contract for the Betting Stock market intelligence platform.")


if __name__ == "__main__":
    unittest.main()
