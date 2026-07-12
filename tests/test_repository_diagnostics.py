from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import scripts.repo_diagnostics as diagnostics


ROOT = Path(__file__).resolve().parents[1]


def _clean_git_state() -> dict[str, object]:
    return {
        "available": True,
        "status": "available",
        "branch": "feature/nfl-backtesting",
        "head": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "upstream": "origin/feature/nfl-backtesting",
        "ahead": 0,
        "behind": 0,
        "staged_files": [],
        "modified_files": [],
        "untracked_files": [],
        "clean": True,
        "status_summary": "## feature/nfl-backtesting...origin/feature/nfl-backtesting",
    }


class TestRepositoryDiagnostics(unittest.TestCase):
    def test_git_state_handles_missing_git_gracefully(self) -> None:
        def _raise_file_not_found(*_args, **_kwargs):
            raise FileNotFoundError("git")

        with patch.object(diagnostics.subprocess, "run", side_effect=_raise_file_not_found):
            state = diagnostics._git_state()

        self.assertFalse(state["available"])
        self.assertEqual(state["status"], "unavailable")
        self.assertIsNone(state["branch"])
        self.assertIsNone(state["head"])
        self.assertIsNone(state["clean"])

    def test_collect_repository_diagnostics_reports_expected_sections(self) -> None:
        with patch.object(diagnostics, "_git_state", return_value=_clean_git_state()):
            report = diagnostics.collect_repository_diagnostics(ROOT)

        self.assertEqual(report["root"], str(ROOT))
        self.assertEqual(report["git"]["branch"], "feature/nfl-backtesting")
        self.assertTrue(report["git"]["available"])
        self.assertEqual(report["git"]["clean"], True)
        self.assertTrue(report["python"]["version"])
        self.assertIn("venv", report["python"])
        self.assertEqual(report["python"]["venv"]["path"], str(ROOT / ".venv"))
        self.assertTrue(report["repository_health"]["ok"], json.dumps(report["repository_health"], indent=2, sort_keys=True))
        self.assertIn("workflow_inventory", report)
        self.assertIn("script_inventory", report)
        self.assertIn("api_route_inventory", report)
        self.assertIn("test_inventory", report)
        self.assertIn("module_inventory", report)
        self.assertIn("provider_inventory", report)
        self.assertIn("quality_gates", report)
        self.assertEqual(report["quality_gates"]["canonical_local_command"], "./.venv/bin/python scripts/run_quality_gates.py --install")

        route_paths = {item["path"] for item in report["api_route_inventory"]["routes"]}
        self.assertIn("/health", route_paths)
        self.assertIn("/model/backtest", route_paths)

        layers = {layer["layer"] for layer in report["module_inventory"]["layers"]}
        self.assertIn("src.api", layers)
        self.assertIn("src.providers", layers)
        self.assertIn("tests", layers)
        self.assertIn("scripts", layers)

        provider_ids = {provider["provider_id"] for provider in report["provider_inventory"]["providers"]}
        self.assertIn("sportsbook_placeholder", provider_ids)
        self.assertIn("prediction_market_placeholder", provider_ids)

    def test_text_renderer_mentions_core_sections(self) -> None:
        with patch.object(diagnostics, "_git_state", return_value=_clean_git_state()):
            report = diagnostics.collect_repository_diagnostics(ROOT)

        text = diagnostics.render_repository_diagnostics_text(report)
        self.assertIn("repository diagnostics", text)
        self.assertIn("workflow inventory:", text)
        self.assertIn("script inventory:", text)
        self.assertIn("api route inventory:", text)
        self.assertIn("module inventory by layer:", text)
        self.assertIn("provider inventory:", text)
        self.assertIn("configured quality gates:", text)
        self.assertNotIn("VIRTUAL_ENV", text)

    def test_main_outputs_json(self) -> None:
        buffer = StringIO()
        with patch.object(diagnostics, "_git_state", return_value=_clean_git_state()), redirect_stdout(buffer):
            exit_code = diagnostics.main(["--output", "json"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(buffer.getvalue().strip())


if __name__ == "__main__":
    unittest.main()
