from __future__ import annotations

import asyncio
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


def test_docs_exist_and_contain_required_statement() -> None:
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
        "Remaining References",
        "Next Recommended Phase",
    ]:
        assert section in combined, section
    assert (
        "Explicit compatibility-proof tests must not preserve legacy odds shells unnecessarily. "
        "This phase proves final delete readiness only and does not delete legacy odds modules."
        in combined
    )
    for phrase in [
        "no files deleted",
        "no files moved",
        "no source-function migration",
        "no public functions removed",
        "behavior unchanged",
        "historical evidence only",
    ]:
        assert phrase in combined.lower()


def test_canonical_modules_import_without_import_time_env_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time env access is forbidden")),
    )

    for module_name in [
        "src.connectors.odds_data",
        "src.connectors.errors",
        "src.services.odds_runtime_bridge",
        "src.providers.sportsbooks",
        "src.providers.registry",
    ]:
        module = _fresh_import(module_name)
        assert module is not None


def test_canonical_odds_methods_remain_disabled_and_safe() -> None:
    errors = importlib.import_module("src.connectors.errors")
    connector = importlib.import_module("src.connectors.odds_data")
    bridge = importlib.import_module("src.services.odds_runtime_bridge")
    sportsbooks = importlib.import_module("src.providers.sportsbooks")
    sportsbook_adapters = importlib.import_module("src.providers.sportsbooks.adapters")

    assert connector.describe_odds_data_connector_readiness()["status"] == "disabled"
    assert connector.build_odds_data_connector_configuration().provider == "odds_data"

    adapter = bridge.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True})
    snapshot = adapter.fetch_snapshot()
    assert snapshot["status"] == "provider_disabled"
    assert snapshot["records"] == []
    assert snapshot["connector_configuration"]["provider"] == "odds_data"
    assert snapshot["connector_readiness"]["status"] == "disabled"

    enriched = bridge.enrich_with_sharp({"sport": "nba", "league": "nba"})
    assert enriched["provider_status"] == "disabled"
    assert enriched["connector_configuration"]["provider"] == "odds_data"
    assert enriched["connector_readiness"]["status"] == "disabled"

    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_events()
    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_odds()
    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_player_props()
    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_sports()

    disabled_client = connector.build_odds_data_disabled_live_client()
    try:
        disabled_client.fetch_odds()
    except Exception as exc:  # pragma: no cover - explicit disabled path proof
        assert exc.__class__.__name__ == "ConnectorDisabledError"
        assert exc.__class__.__module__ == "src.connectors.errors"
    else:  # pragma: no cover - explicit disabled path proof
        raise AssertionError("disabled odds client unexpectedly fetched odds")

    normalized = sportsbook_adapters.normalize_sportsbook_odds(
        "sportsbook",
        "evt-1",
        "nba",
        "moneyline",
        "fanduel",
        "home",
        -110,
        None,
        "2024-01-01T00:00:00Z",
        {"status": "disabled"},
    )
    assert normalized["provider"] == "sportsbook"
    assert normalized["provider_event_id"] == "evt-1"
    assert normalized["selection"] == "home"


def test_target_sources_have_no_live_network_library_imports() -> None:
    for path in TARGET_FILES:
        text = _read(path).lower()
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in text, f"{path} still references {forbidden}"


def test_canonical_connector_boundary_remains_disabled_and_safe() -> None:
    errors = importlib.import_module("src.connectors.errors")
    connector = importlib.import_module("src.connectors.odds_data")
    readiness = connector.describe_odds_data_connector_readiness()
    assert readiness["status"] == "disabled"
    assert readiness["read_only"] is True
    client = connector.build_odds_data_disabled_live_client()
    try:
        client.fetch_snapshot()
    except Exception as exc:  # pragma: no cover - explicit disabled path proof
        assert exc.__class__.__name__ == "ConnectorDisabledError"
        assert exc.__class__.__module__ == "src.connectors.errors"
    else:  # pragma: no cover - explicit disabled path proof
        raise AssertionError("disabled odds client unexpectedly fetched snapshot")
