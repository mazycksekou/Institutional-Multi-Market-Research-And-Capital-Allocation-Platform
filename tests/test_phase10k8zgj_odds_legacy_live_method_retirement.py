from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGJ_ODDS_LEGACY_LIVE_METHOD_RETIREMENT.md",
    ROOT / "ODDS_LEGACY_LIVE_METHOD_RETIREMENT_MAP_AFTER_10K8ZGJ.md",
    ROOT / "ODDS_DISABLED_METHOD_BEHAVIOR_AFTER_10K8ZGJ.md",
    ROOT / "ODDS_LEGACY_DELETE_READINESS_AFTER_10K8ZGJ.md",
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


def test_docs_exist_and_contain_required_statement() -> None:
    combined = "\n".join(_read(path) for path in DOCS)
    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Compatibility Shell Behavior",
        "Delete Readiness",
        "Next Phase Recommendation",
    ]:
        assert section in combined, section
    assert (
        "Legacy odds modules are converted toward disabled compatibility shells in this phase. "
        "This phase does not authorize live API calls, credential reads, bet execution, route rewrites, connector activation, or deletion."
        in combined
    )
    for phrase in [
        "no files deleted",
        "no files moved",
        "no source-function migration",
        "no public functions removed",
        "behavior unchanged",
    ]:
        assert phrase in combined.lower()


def test_target_modules_import_without_import_time_env_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time env access is forbidden")),
    )

    for module_name in [
        "sharp_client",
        "providers.sharp_provider",
        "betting_providers.sharp_api",
        "betting_providers.the_odds_api",
        "betting_providers.sportsgameodds",
        "automation_scheduler.sharp_sportsbook_adapter",
        "automation_scheduler.sportsbook_odds_provider",
        "src.connectors.odds_data",
    ]:
        module = _fresh_import(module_name)
        assert module is not None


def test_disabled_legacy_odds_methods_raise_or_return_disabled_placeholders() -> None:
    sharp_client = importlib.import_module("sharp_client")
    sharp_provider = importlib.import_module("providers.sharp_provider")
    sharp_api = importlib.import_module("betting_providers.sharp_api")
    odds_api = importlib.import_module("betting_providers.the_odds_api")
    sports_game = importlib.import_module("betting_providers.sportsgameodds")
    sharp_scheduler = importlib.import_module("automation_scheduler.sharp_sportsbook_adapter")
    connector = importlib.import_module("src.connectors.odds_data")

    with pytest.raises(ConnectorDisabledError):
        sharp_client.get_sharp_active_events(api_key="x", sport="nba", league="nba")
    with pytest.raises(ConnectorDisabledError):
        sharp_client.get_sharp_event_odds(api_key="x", event_id="evt1")

    enrichment = sharp_provider.enrich_with_sharp({"sport": "nba", "league": "nba"})
    assert enrichment["provider_status"] == "disabled"
    assert enrichment["connector_configuration"]["provider"] == "odds_data"
    assert enrichment["connector_readiness"]["status"] == "disabled"

    async def _check_async_disabled() -> None:
        adapter = sharp_api.SharpApiAdapter()
        with pytest.raises(ConnectorDisabledError):
            await adapter.get_supported_sports()
        with pytest.raises(ConnectorDisabledError):
            await adapter.get_active_events("nba", "nba")
        with pytest.raises(ConnectorDisabledError):
            await adapter.get_event_odds("evt1", "nba", "nba")
        with pytest.raises(ConnectorDisabledError):
            await adapter.get_first_event_odds("nba", "nba")

        odds_adapter = odds_api.TheOddsApiAdapter()
        with pytest.raises(ConnectorDisabledError):
            await odds_adapter.get_supported_sports()
        with pytest.raises(ConnectorDisabledError):
            await odds_adapter.get_odds_events("basketball_nba", "nba")
        with pytest.raises(ConnectorDisabledError):
            await odds_adapter.get_active_events("basketball_nba", "nba")
        with pytest.raises(ConnectorDisabledError):
            await odds_adapter.get_event_odds("evt1", "basketball_nba", "nba")
        with pytest.raises(ConnectorDisabledError):
            await odds_adapter.get_first_event_odds("basketball_nba", "nba")

        sports_adapter = sports_game.SportsGameOddsAdapter()
        with pytest.raises(ConnectorDisabledError):
            await sports_adapter.get_active_events("basketball_nba", "nba")

    asyncio.run(_check_async_disabled())

    scheduler_adapter = sharp_scheduler.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True})
    snapshot = scheduler_adapter.fetch_snapshot()
    assert snapshot["status"] == "provider_disabled"
    assert snapshot["records"] == []
    assert snapshot["connector_configuration"]["provider"] == "odds_data"
    assert snapshot["connector_readiness"]["status"] == "disabled"
    with pytest.raises(ConnectorDisabledError):
        scheduler_adapter.fetch_events()
    with pytest.raises(ConnectorDisabledError):
        scheduler_adapter.fetch_odds()
    with pytest.raises(ConnectorDisabledError):
        scheduler_adapter.fetch_player_props()
    with pytest.raises(ConnectorDisabledError):
        scheduler_adapter.fetch_sports()

    disabled_client = connector.build_odds_data_disabled_live_client()
    with pytest.raises(ConnectorDisabledError):
        disabled_client.fetch_odds()


def test_target_sources_have_no_live_network_library_imports() -> None:
    for path in TARGET_FILES:
        text = _read(path).lower()
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in text, f"{path} still references {forbidden}"


def test_canonical_connector_boundary_remains_disabled_and_safe() -> None:
    connector = importlib.import_module("src.connectors.odds_data")
    readiness = connector.describe_odds_data_connector_readiness()
    assert readiness["status"] == "disabled"
    assert readiness["read_only"] is True
    client = connector.build_odds_data_disabled_live_client()
    with pytest.raises(ConnectorDisabledError):
        client.fetch_snapshot()
