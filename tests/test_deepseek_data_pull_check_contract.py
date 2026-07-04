import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.ai.deepseek_data_pull_check import build_deepseek_data_pull_check_report, provider_call_gate
from src.services.streamlit_dashboard_facade import build_candidate_report, evaluate_outcome_evidence, run_tiny_read_only_settlement_check
from tests.support.action_imports import app


ROOT = Path(__file__).resolve().parents[1]


class _FakeSettlementAdapter:
    def __init__(
        self,
        responses,
        *,
        ready=True,
        blockers=None,
        credential_status="ok",
        live_reads_enabled=True,
        provider_enabled=True,
    ):
        self.responses = list(responses)
        self.ready = ready
        self.blockers = list(blockers or ([] if ready else ["provider_disabled"]))
        self.credential_status = credential_status
        self.live_reads_enabled = live_reads_enabled
        self.provider_enabled = provider_enabled
        self.calls = []

    def validate_config(self):
        return {
            "ok": self.ready,
            "blockers": self.blockers,
            "credential_status": self.credential_status,
            "live_reads_enabled": self.live_reads_enabled,
            "provider_enabled": self.provider_enabled,
        }

    def fetch_markets(self, params=None):
        self.calls.append(dict(params or {}))
        if self.responses:
            return self.responses.pop(0)
        return {"ok": True, "status": "ok", "records": []}


class TestDeepSeekDataPullCheckContract(unittest.TestCase):
    def test_required_files_exist(self):
        for relative in (
            "scripts/deepseek_data_pull_check.ps1",
            "src/ai/prompts/deepseek_data_pull_check_prompt.md",
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
        self.assertIn("env_file_present", report)
        self.assertIn("env_loaded", report)
        self.assertIn("env_loader", report)
        self.assertIn("readiness_source", report)
        self.assertIn("readiness_checker_consistent_with_wrapper", report)
        self.assertIn("missing_env_names", report)
        self.assertIn("deepseek_data_checks/latest.json", report["latest_json_path"])
        self.assertIn("deepseek_data_checks/items/", report["item_json_path"])
        self.assertIn("deepseek_data_checks/daily/", report["daily_json_path"])
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("do-not-leak", rendered)

    def test_deepseek_wrapper_loads_project_env_and_matches_readiness_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "automation_scheduler").mkdir()
            (root / "scripts").mkdir()
            (root / ".env").write_text(
                "\n".join(
                    [
                        "KALSHI_PROVIDER_ENABLED=true",
                        "KALSHI_LIVE_READS_ENABLED=true",
                        "KALSHI_API_KEY=kalshi_key_do_not_print_12345",
                        "KALSHI_API_SECRET=kalshi_secret_do_not_print_12345",
                    ]
                ),
                encoding="utf-8",
            )
            env_names = (
                "KALSHI_PROVIDER_ENABLED",
                "KALSHI_LIVE_READS_ENABLED",
                "KALSHI_API_KEY",
                "KALSHI_API_SECRET",
            )
            previous_env = {name: os.environ.get(name) for name in env_names}
            try:
                for name in env_names:
                    os.environ.pop(name, None)
                report = build_deepseek_data_pull_check_report(
                    prediction_market_outcome_check=True,
                    allow_tiny_provider_calls=False,
                    max_provider_calls=3,
                    max_records=5,
                    base_data_dir=tmp,
                    project_root=root,
                )
            finally:
                for name, value in previous_env.items():
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value
        rendered = json.dumps(report, sort_keys=True)
        self.assertTrue(report["env_file_present"])
        self.assertTrue(report["env_loaded"])
        self.assertEqual(report["env_loader"], "python_dotenv")
        self.assertEqual(report["readiness_source"], "kalshi_readonly_readiness")
        self.assertEqual(report["missing_env_names"], [])
        self.assertEqual(report["readiness_checker_provider_readiness_status"], "provider_not_ready")
        self.assertEqual(report["provider_readiness_status"], "provider_not_ready")
        self.assertTrue(report["readiness_checker_consistent_with_wrapper"])
        self.assertIn("provider_not_ready", report["readiness_checker_provider_readiness_blockers"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["why_provider_calls_zero"], "tiny_provider_mode_not_requested")
        self.assertNotIn("kalshi_key_do_not_print_12345", rendered)
        self.assertNotIn("kalshi_secret_do_not_print_12345", rendered)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

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
        self.assertEqual(allowed["provider_call_execution_status"], "tiny_provider_mode_armed")

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

    def test_default_prediction_market_check_still_makes_zero_provider_calls(self):
        fake = _FakeSettlementAdapter([{"ok": True, "status": "ok", "records": [{"ticker": "KX1", "result": "yes"}]}])
        report = build_candidate_report(
            records=[
                {
                    "_source_record_type": "paper_decision",
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "ticker": "KX1",
                }
            ],
            allow_tiny_provider_calls=False,
            max_provider_calls=3,
            max_records=5,
            provider_adapter=fake,
        )
        self.assertEqual(fake.calls, [])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["explicit_outcomes_found"], 0)
        self.assertFalse(report["tiny_provider_mode_requested"])
        self.assertFalse(report["tiny_provider_mode_allowed"])
        self.assertEqual(report["why_provider_calls_zero"], "tiny_provider_mode_not_requested")
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])

    def test_zero_call_diagnostics_report_provider_not_ready_without_secrets(self):
        fake = _FakeSettlementAdapter(
            [{"ok": True, "status": "ok", "records": [{"ticker": "KX1", "result": "yes"}]}],
            ready=False,
            blockers=["provider_disabled", "live_reads_disabled", "blocked_missing_credentials"],
            credential_status="missing",
            live_reads_enabled=False,
            provider_enabled=False,
        )
        report = build_candidate_report(
            records=[
                {
                    "_source_record_type": "paper_decision",
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "ticker": "KX1",
                    "api_key": "do-not-leak",
                    "provider_payload": {"raw": "drop"},
                }
            ],
            allow_tiny_provider_calls=True,
            max_provider_calls=3,
            max_records=5,
            provider_adapter=fake,
        )
        rendered = json.dumps(report, sort_keys=True).lower()
        self.assertEqual(fake.calls, [])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertTrue(report["tiny_provider_mode_requested"])
        self.assertTrue(report["tiny_provider_mode_allowed"])
        self.assertEqual(report["provider_readiness_status"], "provider_not_ready")
        self.assertIn("provider_not_ready", report["provider_readiness_blockers"])
        self.assertIn("live_reads_disabled", report["provider_readiness_blockers"])
        self.assertIn("credentials_missing", report["provider_readiness_blockers"])
        self.assertFalse(report["provider_config_present"])
        self.assertFalse(report["live_read_enabled"])
        self.assertFalse(report["credentials_present"])
        self.assertEqual(report["why_provider_calls_zero"], "provider_not_ready")
        self.assertEqual(report["provider_selection_blocker"], "provider_not_ready")
        self.assertGreaterEqual(report["provider_eligible_records"], 1)
        self.assertNotIn("do-not-leak", rendered)
        self.assertNotIn("provider_payload", rendered)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_zero_call_diagnostics_report_missing_identifiers(self):
        fake = _FakeSettlementAdapter([], ready=True)
        result = run_tiny_read_only_settlement_check(
            [
                {
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "selection": "unknown",
                }
            ],
            allow_tiny_provider_calls=True,
            max_provider_calls=3,
            max_records=5,
            adapter=fake,
        )
        self.assertEqual(fake.calls, [])
        self.assertEqual(result["provider_calls_attempted"], 0)
        self.assertEqual(result["pending_records_seen"], 1)
        self.assertEqual(result["provider_eligible_records"], 0)
        self.assertEqual(result["provider_selected_count"], 0)
        self.assertEqual(result["missing_identifier_count"], 1)
        self.assertEqual(result["missing_ticker_count"], 1)
        self.assertEqual(result["missing_market_id_count"], 1)
        self.assertEqual(result["why_provider_calls_zero"], "missing_required_identifiers")
        self.assertEqual(result["provider_selection_blocker"], "missing_required_identifiers")

    def test_zero_call_diagnostics_report_no_provider_eligible_records(self):
        fake = _FakeSettlementAdapter([], ready=True)
        result = run_tiny_read_only_settlement_check(
            [
                {
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "ticker": "KXLOCAL",
                    "final_outcome": "yes",
                }
            ],
            allow_tiny_provider_calls=True,
            max_provider_calls=3,
            max_records=5,
            adapter=fake,
        )
        self.assertEqual(fake.calls, [])
        self.assertEqual(result["pending_records_seen"], 1)
        self.assertEqual(result["local_explicit_outcome_count"], 1)
        self.assertEqual(result["provider_eligible_records"], 0)
        self.assertEqual(result["provider_ineligible_reason_counts"]["local_explicit_outcome"], 1)
        self.assertEqual(result["why_provider_calls_zero"], "no_provider_eligible_records")

    def test_zero_call_diagnostics_report_call_budget_zero(self):
        fake = _FakeSettlementAdapter([{"ok": True, "status": "ok", "records": [{"ticker": "KX1", "result": "yes"}]}], ready=True)
        result = run_tiny_read_only_settlement_check(
            [{"provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KX1"}],
            allow_tiny_provider_calls=True,
            max_provider_calls=0,
            max_records=5,
            adapter=fake,
        )
        self.assertEqual(fake.calls, [])
        self.assertTrue(result["tiny_provider_mode_requested"])
        self.assertFalse(result["tiny_provider_mode_allowed"])
        self.assertEqual(result["provider_selection_limit"], 0)
        self.assertEqual(result["provider_selected_count"], 0)
        self.assertEqual(result["why_provider_calls_zero"], "call_budget_zero")
        self.assertEqual(result["provider_call_block_reason"], "call_budget_zero")

    def test_tiny_provider_settlement_check_accepts_explicit_yes_and_no(self):
        fake = _FakeSettlementAdapter(
            [
                {
                    "ok": True,
                    "status": "ok",
                    "records": [{"ticker": "KXYES", "result": "yes", "settlement_time": "2026-06-02T00:00:00Z"}],
                },
                {
                    "ok": True,
                    "status": "ok",
                    "records": [{"ticker": "KXNO", "result": "no", "settlement_time": "2026-06-02T00:00:00Z"}],
                },
            ]
        )
        report = build_candidate_report(
            records=[
                {"_source_record_type": "paper_decision", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXYES"},
                {"_source_record_type": "paper_decision", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXNO"},
            ],
            allow_tiny_provider_calls=True,
            max_provider_calls=99,
            max_records=99,
            provider_adapter=fake,
        )
        outcomes = sorted(row["explicit_outcome"] for row in report["candidates"])
        self.assertEqual(outcomes, ["no", "yes"])
        self.assertEqual(report["provider_calls_attempted"], 2)
        self.assertEqual(report["provider_calls_succeeded"], 2)
        self.assertEqual(report["provider_calls_failed"], 0)
        self.assertEqual(report["markets_checked_with_provider"], 2)
        self.assertEqual(report["explicit_outcomes_found"], 2)
        self.assertEqual(report["max_provider_calls_effective"], 3)
        self.assertEqual(report["max_records_effective"], 5)
        self.assertFalse(report["rate_limited"])
        self.assertFalse(report["persisted"])

    def test_tiny_provider_settlement_check_rejects_price_and_closed_without_result(self):
        fake = _FakeSettlementAdapter(
            [
                {"ok": True, "status": "ok", "records": [{"ticker": "KXPRICE", "yes_price": 0.99}]},
                {"ok": True, "status": "ok", "records": [{"ticker": "KXCLOSED", "status": "closed", "yes_price": 0.99}]},
            ]
        )
        report = build_candidate_report(
            records=[
                {"_source_record_type": "paper_decision", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXPRICE"},
                {"_source_record_type": "paper_decision", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXCLOSED"},
            ],
            allow_tiny_provider_calls=True,
            max_provider_calls=3,
            max_records=5,
            provider_adapter=fake,
        )
        self.assertEqual(report["explicit_outcomes_found"], 0)
        self.assertEqual(report["provider_calls_attempted"], 2)
        self.assertIn("missing_explicit_settlement_field", report["provider_rejection_reasons"])
        self.assertIn("closed_without_explicit_result", report["provider_rejection_reasons"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_tiny_provider_settlement_check_rate_limit_stops_safely(self):
        fake = _FakeSettlementAdapter(
            [
                {"ok": False, "status": "provider_error", "http_status": 429, "blocker": "http_429", "records": []},
                {"ok": True, "status": "ok", "records": [{"ticker": "KX2", "result": "yes"}]},
            ]
        )
        result = run_tiny_read_only_settlement_check(
            [
                {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KX1"},
                {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KX2"},
            ],
            allow_tiny_provider_calls=True,
            max_provider_calls=3,
            max_records=5,
            adapter=fake,
        )
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(result["provider_calls_attempted"], 1)
        self.assertEqual(result["provider_calls_succeeded"], 0)
        self.assertEqual(result["provider_calls_failed"], 1)
        self.assertTrue(result["rate_limited"])
        self.assertEqual(result["provider_settlement_check_status"], "provider_rate_limited")
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])

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
