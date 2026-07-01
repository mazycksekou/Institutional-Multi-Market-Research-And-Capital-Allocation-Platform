from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGL_ODDS_RUNTIME_CONSUMER_REDIRECTION_BATCH_2.md",
    ROOT / "ODDS_RUNTIME_CONSUMER_REDIRECTION_MAP_AFTER_10K8ZGL.md",
    ROOT / "ODDS_RUNTIME_IMPORT_SCAN_AFTER_10K8ZGL.md",
    ROOT / "ODDS_RUNTIME_DELETE_READINESS_AFTER_10K8ZGL.md",
]

RUNTIME_FILES = [
    ROOT / "src" / "services" / "enrichment_service.py",
    ROOT / "src" / "services" / "scheduler_runner.py",
    ROOT / "src" / "services" / "automation_scheduler_facade.py",
    ROOT / "src" / "services" / "odds_runtime_bridge.py",
]

FORBIDDEN_IMPORTS = (
    "requests",
    "httpx",
    "websocket",
    "yfinance",
    "selenium",
    "playwright",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def _run_import_safety_check(module_names: list[str]) -> None:
    script = (
        "import importlib, os\n"
        "os.getenv = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('import-time credential access is forbidden'))\n"
        f"module_names = {module_names!r}\n"
        "for module_name in module_names:\n"
        "    importlib.import_module(module_name)\n"
        "print('ok')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == "ok"


def test_docs_exist_and_contain_required_redirection_language() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Big-Picture Architecture",
        "Runtime Consumer Redirection",
        "Canonical Disabled Surfaces",
        "Runtime Import Scan",
        "Remaining Compatibility References",
        "Delete-Readiness",
        "Compatibility Policy",
        "No-Deletion / No-Call Guarantees",
        "Next Recommended Phase",
    ]:
        assert section in combined, section

    required_statement = (
        "Odds runtime consumers are redirected away from legacy odds shells in this phase. "
        "This phase does not authorize live API calls, credential reads, bet execution, connector activation, or deletion."
    )
    assert required_statement in combined

    for phrase in [
        "src.services.odds_runtime_bridge",
        "src.connectors.odds_data",
        "No deletion occurred",
        "No live API calls were made",
        "No credentials were read at import time",
        "compatibility-preserving runtime bridge",
        "historical evidence only",
        "delete-proof only",
    ]:
        assert phrase in combined


def test_runtime_files_redirect_to_canonical_bridge() -> None:
    enrichment = _read(ROOT / "src" / "services" / "enrichment_service.py")
    scheduler_runner = _read(ROOT / "src" / "services" / "scheduler_runner.py")
    scheduler_init = _read(ROOT / "src" / "services" / "automation_scheduler_facade.py")
    bridge = _read(ROOT / "src" / "services" / "odds_runtime_bridge.py")

    assert "src.services.odds_runtime_bridge" in enrichment
    assert "providers.sharp_provider" not in enrichment

    for text in (scheduler_runner, scheduler_init):
        assert "src.services.odds_runtime_bridge" in text
        assert "sharp_sportsbook_adapter" not in text
        assert "sportsbook_odds_provider" not in text

    assert "src.connectors.odds_data" in bridge
    assert "ConnectorDisabledError" in bridge


def test_canonical_bridge_and_connector_imports_are_safe_and_disabled() -> None:
    _run_import_safety_check(
        [
            "src.connectors.odds_data",
            "src.connectors.errors",
            "src.services.odds_runtime_bridge",
        ]
    )

    connector = importlib.import_module("src.connectors.odds_data")
    errors = importlib.import_module("src.connectors.errors")
    bridge = importlib.import_module("src.services.odds_runtime_bridge")

    readiness = connector.describe_odds_data_connector_readiness()
    assert readiness["status"] == "disabled"
    assert readiness["read_only"] is True

    configuration = connector.build_odds_data_connector_configuration()
    assert configuration.provider == "odds_data"
    assert configuration.credential_names == ("ODDS_DATA_API_KEY", "ODDS_DATA_API_SECRET")

    disabled_client = connector.build_odds_data_disabled_live_client()
    with pytest.raises(RuntimeError) as exc_info:
        disabled_client.fetch_odds()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"

    adapter = bridge.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True})
    snapshot = bridge.get_sportsbook_snapshot(adapter)
    assert snapshot["status"] == "provider_disabled"
    assert snapshot["records"] == []
    assert snapshot["connector_configuration"]["provider"] == "odds_data"
    assert snapshot["connector_readiness"]["status"] == "disabled"

    for action in [
        adapter.fetch_events,
        adapter.fetch_odds,
        adapter.fetch_player_props,
        adapter.fetch_sports,
    ]:
        with pytest.raises(RuntimeError) as exc_info:
            action()
        assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"


def test_runtime_files_do_not_import_forbidden_live_network_libraries() -> None:
    for path in RUNTIME_FILES:
        text = _read(path).lower()
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in text, f"{path} still references {forbidden}"


def test_final_delete_readiness_is_documented() -> None:
    delete_readiness = _read(ROOT / "FINAL_ODDS_DELETE_READINESS_AFTER_10K8ZGN.md")
    import_scan = _read(ROOT / "ODDS_PROOF_HISTORY_REFERENCE_SCAN_AFTER_10K8ZGN.md")

    for blocker in [
        "tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py",
    ]:
        assert blocker in import_scan

    for phrase in [
        "Delete-Readiness Matrix",
        "Delete-Ready Outcome",
        "Next Recommended Phase",
        "explicit compatibility-proof tests",
    ]:
        assert phrase.lower() in delete_readiness.lower() or phrase.lower() in import_scan.lower()

