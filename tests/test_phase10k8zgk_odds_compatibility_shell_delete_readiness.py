from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGK_ODDS_COMPATIBILITY_SHELL_DELETE_READINESS.md",
    ROOT / "ODDS_COMPATIBILITY_IMPORT_SCAN_AFTER_10K8ZGK.md",
    ROOT / "ODDS_COMPATIBILITY_TEST_REDIRECTION_AFTER_10K8ZGK.md",
    ROOT / "ODDS_COMPATIBILITY_DELETE_READINESS_AFTER_10K8ZGK.md",
]
TARGET_FILES = [
    ROOT / "sharp_client.py",
    ROOT / "providers" / "sharp_provider.py",
    ROOT / "betting_providers" / "sharp_api.py",
    ROOT / "betting_providers" / "the_odds_api.py",
    ROOT / "betting_providers" / "sportsgameodds.py",
    ROOT / "automation_scheduler" / "sharp_sportsbook_adapter.py",
    ROOT / "automation_scheduler" / "sportsbook_odds_provider.py",
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
        "Import Scan Summary",
        "Test Redirection Summary",
        "Delete Readiness Matrix",
        "Compatibility Import State",
        "Delete-Ready Files",
        "Blocked Files",
        "Next Recommended Deletion Phase",
    ]:
        assert section in combined, section

    required_statement = (
        "Odds compatibility shell deletion is authorized only after runtime imports, test imports, "
        "compatibility proof, and full local gate proof are clean. This phase proves readiness only "
        "and does not delete legacy odds modules."
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
        "none yet",
        "blocked",
        "legacy odds modules remain importable",
    ]:
        assert phrase in combined.lower()

    for filename in [
        "sharp_client.py",
        "providers/sharp_provider.py",
        "betting_providers/sharp_api.py",
        "betting_providers/the_odds_api.py",
        "betting_providers/sportsgameodds.py",
        "automation_scheduler/sharp_sportsbook_adapter.py",
        "automation_scheduler/sportsbook_odds_provider.py",
    ]:
        assert filename in combined


def test_canonical_connector_boundary_remains_safe_and_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
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
    ]:
        module = _fresh_import(module_name)
        assert module is not None

    connector = importlib.import_module("src.connectors.odds_data")
    readiness = connector.describe_odds_data_connector_readiness()
    assert readiness["status"] == "disabled"
    assert readiness["read_only"] is True

    configuration = connector.build_odds_data_connector_configuration()
    assert configuration.provider == "odds_data"
    assert configuration.credential_names == ("ODDS_DATA_API_KEY", "ODDS_DATA_API_SECRET")

    disabled_client = connector.build_odds_data_disabled_live_client()
    with pytest.raises(ConnectorDisabledError):
        disabled_client.fetch_snapshot()


def test_legacy_odds_shells_remain_importable_but_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda _name, default=None: default if default is not None else "")

    sharp_client = importlib.import_module("sharp_client")
    sharp_provider = importlib.import_module("providers.sharp_provider")
    sharp_api = importlib.import_module("betting_providers.sharp_api")
    odds_api = importlib.import_module("betting_providers.the_odds_api")
    sports_game = importlib.import_module("betting_providers.sportsgameodds")
    sharp_scheduler = importlib.import_module("automation_scheduler.sharp_sportsbook_adapter")
    sportsbook_provider = importlib.import_module("automation_scheduler.sportsbook_odds_provider")
    errors = importlib.import_module("src.connectors.errors")

    with pytest.raises(errors.ConnectorDisabledError):
        sharp_client.get_sharp_active_events(api_key="x", sport="nba", league="nba")
    with pytest.raises(errors.ConnectorDisabledError):
        sharp_client.get_sharp_event_odds(api_key="x", event_id="evt1")

    enrichment = sharp_provider.enrich_with_sharp({"sport": "nba", "league": "nba"})
    assert enrichment["provider_status"] == "disabled"
    assert enrichment["connector_configuration"]["provider"] == "odds_data"
    assert enrichment["connector_readiness"]["status"] == "disabled"

    import asyncio

    adapter = sharp_api.SharpApiAdapter()
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(adapter.get_supported_sports())
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(adapter.get_active_events("nba", "nba"))
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(adapter.get_event_odds("evt1", "nba", "nba"))
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(adapter.get_first_event_odds("nba", "nba"))

    odds_adapter = odds_api.TheOddsApiAdapter()
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(odds_adapter.get_supported_sports())
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(odds_adapter.get_odds_events("basketball_nba", "nba"))
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(odds_adapter.get_active_events("basketball_nba", "nba"))
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(odds_adapter.get_event_odds("evt1", "basketball_nba", "nba"))
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(odds_adapter.get_first_event_odds("basketball_nba", "nba"))

    sports_adapter = sports_game.SportsGameOddsAdapter()
    with pytest.raises(errors.ConnectorDisabledError):
        asyncio.run(sports_adapter.get_active_events("basketball_nba", "nba"))

    scheduler_adapter = sharp_scheduler.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True})
    snapshot = scheduler_adapter.fetch_snapshot()
    assert snapshot["status"] == "provider_disabled"
    assert snapshot["records"] == []
    assert snapshot["connector_configuration"]["provider"] == "odds_data"
    assert snapshot["connector_readiness"]["status"] == "disabled"
    with pytest.raises(errors.ConnectorDisabledError):
        scheduler_adapter.fetch_events()
    with pytest.raises(errors.ConnectorDisabledError):
        scheduler_adapter.fetch_odds()
    with pytest.raises(errors.ConnectorDisabledError):
        scheduler_adapter.fetch_player_props()
    with pytest.raises(errors.ConnectorDisabledError):
        scheduler_adapter.fetch_sports()

    sportsbook_snapshot = sportsbook_provider.get_sportsbook_snapshot(
        sharp_scheduler.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True})
    )
    assert sportsbook_snapshot["status"] in {"provider_disabled", "disabled"}


def test_target_sources_have_no_live_network_library_imports() -> None:
    for path in TARGET_FILES:
        text = _read(path).lower()
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in text, f"{path} still references {forbidden}"


def test_runtime_and_test_blockers_remain_documented() -> None:
    import_scan = _read(ROOT / "ODDS_COMPATIBILITY_IMPORT_SCAN_AFTER_10K8ZGK.md")
    delete_readiness = _read(ROOT / "ODDS_COMPATIBILITY_DELETE_READINESS_AFTER_10K8ZGK.md")

    for blocker in [
        "src/services/enrichment_service.py",
        "automation_scheduler/scheduler_runner.py",
        "automation_scheduler/__init__.py",
        "tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py",
        "tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py",
        "tests/test_phase10k8zfz_odds_data_connector_batch_2.py",
    ]:
        assert blocker in import_scan

    for target in [
        "sharp_client.py",
        "providers/sharp_provider.py",
        "betting_providers/sharp_api.py",
        "betting_providers/the_odds_api.py",
        "betting_providers/sportsgameodds.py",
        "automation_scheduler/sharp_sportsbook_adapter.py",
        "automation_scheduler/sportsbook_odds_provider.py",
    ]:
        assert target in delete_readiness
        assert "blocked" in delete_readiness.lower()
        assert "none yet" in delete_readiness.lower()
