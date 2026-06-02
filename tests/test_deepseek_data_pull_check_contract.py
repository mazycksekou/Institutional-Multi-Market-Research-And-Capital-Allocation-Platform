import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from automation_scheduler.deepseek_data_pull_check import (
    build_deepseek_data_pull_check_report,
    provider_call_gate,
)
from automation_scheduler.prediction_market_outcome_candidates import (
    build_candidate_report,
    evaluate_outcome_evidence,
)
from main import app


ROOT = Path(__file__).resolve().parents[1]


class TestDeepSeekDataPullCheckContract(unittest.TestCase):
    def test_required_files_exist(self):
        for relative in (
            "scripts/deepseek_data_pull_check.ps1",
            "prompts/deepseek_data_pull_check_prompt.md",
            "docs/DEEPSEEK_DATA_PULL_CHECK.md",
        ):
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_script_runs_only_safe_checks_and_no_forbidden_actions(self):
        script = (ROOT / "scripts/deepseek_data_pull_check.ps1").read_text(encoding="utf-8")
        for expected in (
            "[switch]$DryRun",
            "[switch]$PredictionMarketOutcomeCheck",
            "[switch]$AllowTinyProviderCalls",
            "[int]$MaxProviderCalls = 0",
            "[int]$MaxRecords = 0",
            "[string]$Module = \"\"",
            "[string]$SourceId = \"\"",
            "[switch]$NoDeepSeek",
            ".\\scripts\\check_local.ps1",
            ".\\scripts\\check_render.ps1",
            ".\\scripts\\check_data_availability_tiers.ps1",
            "betting-stock-api-code-integration.onrender.com",
            "Capping MaxProviderCalls at 3",
            "Capping MaxRecords at 5",
        ):
            self.assertIn(expected, script)
        forbidden = (
            "import-local-settlements",
            "persist_import_kalshi_outcomes",
            "calibration-collector/run",
            "scheduled-run",
            "render deploy",
            "git push",
            "enable-source",
            "submit_live_order",
        )
        lowered = script.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lowered)

    def test_default_report_makes_zero_provider_calls_and_writes_compact_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                report = build_deepseek_data_pull_check_report(base_data_dir=tmp, persist=True)
                rendered = json.dumps(report, sort_keys=True).lower()
                latest = Path(tmp, report["latest_json_path"])
                daily = Path(tmp, report["daily_markdown_path"])
                self.assertTrue(latest.exists())
                self.assertTrue(daily.exists())

        self.assertTrue(report["dry_run"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertFalse(report["allow_tiny_provider_calls"])
        self.assertEqual(report["max_provider_calls_effective"], 0)
        self.assertEqual(report["max_records_effective"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertTrue(report["paid_budget_gated_sources_blocked"])
        self.assertTrue(report["source_remains_enabled_false"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertIn("deepseek_data_checks/latest.json", report["latest_json_path"])
        self.assertIn("deepseek_data_checks/items/", report["item_json_path"])
        self.assertIn("deepseek_data_checks/daily/", report["daily_json_path"])
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("api_key", rendered)

    def test_provider_calls_require_tiny_mode_and_caps_are_hard(self):
        blocked = provider_call_gate(
            dry_run=True,
            allow_tiny_provider_calls=False,
            max_provider_calls=99,
            max_records=99,
        )
        allowed = provider_call_gate(
            dry_run=True,
            allow_tiny_provider_calls=True,
            max_provider_calls=99,
            max_records=99,
        )
        self.assertFalse(blocked["provider_calls_allowed"])
        self.assertEqual(blocked["max_provider_calls_effective"], 0)
        self.assertEqual(blocked["max_records_effective"], 0)
        self.assertEqual(blocked["provider_calls_attempted"], 0)
        self.assertTrue(allowed["provider_calls_allowed"])
        self.assertEqual(allowed["max_provider_calls_effective"], 3)
        self.assertEqual(allowed["max_records_effective"], 5)
        self.assertEqual(allowed["provider_calls_attempted"], 0)
        self.assertEqual(allowed["provider_call_execution_status"], "not_executed_by_safe_wrapper_step_1")

    def test_outcome_evidence_accepts_only_explicit_yes_no(self):
        accepted_yes = evaluate_outcome_evidence(
            {"market_type": "prediction_market", "ticker": "KX-YES", "result": "yes"},
            source_record_type="test",
        )
        accepted_no = evaluate_outcome_evidence(
            {"market_type": "prediction_market", "ticker": "KX-NO", "settled_no": True},
            source_record_type="test",
        )
        price_only = evaluate_outcome_evidence(
            {"market_type": "prediction_market", "ticker": "KX-PRICE", "yes_price": 0.99},
            source_record_type="test",
        )
        closed = evaluate_outcome_evidence(
            {"market_type": "prediction_market", "ticker": "KX-CLOSED", "status": "closed"},
            source_record_type="test",
        )
        ambiguous = evaluate_outcome_evidence(
            {"market_type": "prediction_market", "ticker": "KX-BAD", "result": "maybe"},
            source_record_type="test",
        )

        self.assertTrue(accepted_yes["candidate_accepted"])
        self.assertEqual(accepted_yes["explicit_outcome"], "yes")
        self.assertTrue(accepted_no["candidate_accepted"])
        self.assertEqual(accepted_no["explicit_outcome"], "no")
        self.assertFalse(price_only["candidate_accepted"])
        self.assertEqual(price_only["rejection_reason"], "price_only_inference_rejected")
        self.assertFalse(closed["candidate_accepted"])
        self.assertEqual(closed["rejection_reason"], "closed_without_explicit_result")
        self.assertFalse(ambiguous["candidate_accepted"])
        self.assertEqual(ambiguous["rejection_reason"], "ambiguous_result")

    def test_candidate_report_schema_and_safety_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_candidate_report(
                records=[
                    {"_source_record_type": "paper_decision", "market_type": "prediction_market", "ticker": "KX1", "final_outcome": "yes"},
                    {"_source_record_type": "review_queue", "market_type": "prediction_market", "ticker": "KX2", "yes_bid": 0.98},
                ],
                base_data_dir=tmp,
                persist=True,
            )
            latest = Path(tmp, report["candidate_latest_json_path"])
            payload = json.loads(latest.read_text(encoding="utf-8"))

        self.assertEqual(report["candidates_count"], 1)
        self.assertEqual(report["rejected_count"], 1)
        self.assertFalse(report["would_persist_outcomes"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertIn("prediction_market_outcome_candidates/latest.json", report["candidate_latest_json_path"])
        self.assertIn("prediction_market_outcome_candidates/latest.md", report["candidate_latest_markdown_path"])
        self.assertIn("prediction_market_outcome_candidates/items/", report["candidate_item_json_path"])
        self.assertIn("prediction_market_outcome_candidates/daily/", report["candidate_daily_json_path"])
        self.assertEqual(payload["candidates"][0]["explicit_outcome"], "yes")
        self.assertFalse(payload["would_persist_outcomes"])

    def test_data_availability_and_calibration_endpoints_still_work(self):
        client = TestClient(app)
        data_availability = client.get("/api/automation/data-sources/data-availability/tiers?limit=10")
        calibration = client.get("/api/automation/calibration?limit=10")
        self.assertEqual(data_availability.status_code, 200)
        self.assertEqual(calibration.status_code, 200)
        data_payload = data_availability.json()
        calibration_payload = calibration.json()
        self.assertEqual(data_payload["enabled_source_count"], 0)
        self.assertFalse(data_payload["provider_write"])
        self.assertFalse(data_payload["execution_allowed"])
        self.assertIn("matched_outcomes_count", calibration_payload)
        self.assertGreaterEqual(calibration_payload["matched_outcomes_count"], 0)
        self.assertFalse(calibration_payload["raw_payload_included"])


if __name__ == "__main__":
    unittest.main()
