from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGO_ODDS_COMPATIBILITY_TEST_RETIREMENT.md",
    ROOT / "ODDS_COMPATIBILITY_TEST_RETIREMENT_MAP_AFTER_10K8ZGO.md",
    ROOT / "ODDS_FINAL_IMPORT_SCAN_AFTER_10K8ZGO.md",
    ROOT / "FINAL_ODDS_SHELL_DELETE_PROOF_AFTER_10K8ZGO.md",
]
TARGET_FILES = [
    ROOT / "src" / "services" / "odds_runtime_bridge.py",
    ROOT / "src" / "connectors" / "odds_data" / "__init__.py",
    ROOT / "src" / "providers" / "sportsbooks" / "contracts.py",
    ROOT / "src" / "providers" / "sportsbooks" / "adapters.py",
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


def _fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_docs_exist_and_state_that_no_shell_is_delete_ready() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Big-Picture Architecture",
        "Compatibility Test Retirement",
        "Delete Readiness",
        "Historical Evidence Policy",
        "No-Deletion / No-Call Guarantees",
        "Next Recommended Phase",
    ]:
        assert section in combined, section

    required_statement = (
        "Explicit compatibility-proof tests must not preserve legacy odds shells unnecessarily. "
        "This phase proves final delete readiness only and does not delete legacy odds modules."
    )
    assert required_statement in combined

    for phrase in [
        "no files deleted",
        "no files moved",
        "no source-function migration",
        "no behavior expansion",
        "no public functions removed",
        "behavior unchanged",
        "no live api calls",
        "no credential reads at import time",
        "historical evidence only",
        "delete-ready now",
    ]:
        assert phrase in combined.lower()


def test_canonical_connector_boundary_remains_safe_and_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    errors = importlib.import_module("src.connectors.errors")
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    for module_name in [
        "src.connectors.odds_data",
        "src.connectors.odds_data.configuration",
        "src.connectors.odds_data.readiness",
        "src.connectors.odds_data.disabled_client",
        "src.services.odds_runtime_bridge",
        "src.providers.sportsbooks",
    ]:
        module = _fresh_import(module_name)
        assert module is not None

    connector = importlib.import_module("src.connectors.odds_data")
    bridge = importlib.import_module("src.services.odds_runtime_bridge")
    readiness = connector.describe_odds_data_connector_readiness()
    assert readiness["status"] == "disabled"
    assert readiness["read_only"] is True

    configuration = connector.build_odds_data_connector_configuration()
    assert configuration.provider == "odds_data"
    assert configuration.credential_names == ("ODDS_DATA_API_KEY", "ODDS_DATA_API_SECRET")

    disabled_client = connector.build_odds_data_disabled_live_client()
    try:
        disabled_client.fetch_snapshot()
    except Exception as exc:  # pragma: no cover - explicit disabled path proof
        assert exc.__class__.__name__ == "ConnectorDisabledError"
        assert exc.__class__.__module__ == "src.connectors.errors"
    else:  # pragma: no cover - explicit disabled path proof
        raise AssertionError("disabled odds connector snapshot unexpectedly succeeded")

    snapshot = bridge.get_sportsbook_snapshot(bridge.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True}))
    assert snapshot["status"] == "provider_disabled"
    assert snapshot["connector_readiness"]["status"] == "disabled"


def test_target_sources_have_no_live_network_library_imports() -> None:
    for path in TARGET_FILES:
        text = _read(path).lower()
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in text, f"{path} still references {forbidden}"


def test_runtime_and_test_blockers_are_reclassified_as_historical_evidence() -> None:
    import_scan = _read(ROOT / "ODDS_FINAL_IMPORT_SCAN_AFTER_10K8ZGO.md")
    delete_readiness = _read(ROOT / "FINAL_ODDS_SHELL_DELETE_PROOF_AFTER_10K8ZGO.md")

    for blocker in [
        "tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgo_odds_compatibility_test_retirement.py",
    ]:
        assert blocker in import_scan
        assert "historical evidence only" in import_scan.lower()

    for target in [
        "src.services.odds_runtime_bridge",
        "src.connectors.odds_data",
        "src.providers.sportsbooks",
    ]:
        assert target in delete_readiness
        assert "delete-ready now" in delete_readiness.lower()
        assert "no remaining file-level barriers" in delete_readiness.lower()
        assert "blocked" not in delete_readiness.lower()
