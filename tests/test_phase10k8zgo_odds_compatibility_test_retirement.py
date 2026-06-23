from __future__ import annotations

import asyncio
import importlib
import os
import subprocess
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

RETIRED_TESTS = [
    ROOT / "tests" / "test_phase10k8zgj_odds_legacy_live_method_retirement.py",
    ROOT / "tests" / "test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py",
]

LEGACY_SHELL_MODULES = [
    "sharp_client",
    "providers.sharp_provider",
    "betting_providers.sharp_api",
    "betting_providers.the_odds_api",
    "betting_providers.sportsgameodds",
    "automation_scheduler.sharp_sportsbook_adapter",
    "automation_scheduler.sportsbook_odds_provider",
]


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


def test_docs_exist_and_contain_required_retirement_language() -> None:
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
        "historical evidence only",
        "no active test requires legacy odds shell imports",
        "delete-ready now",
        "no files deleted",
        "no files moved",
        "no source-function migration",
        "behavior unchanged",
    ]:
        assert phrase in combined.lower()


def test_retired_compatibility_tests_no_longer_reference_legacy_shell_imports() -> None:
    for path in RETIRED_TESTS:
        text = _read(path)
        for legacy in LEGACY_SHELL_MODULES + ["legacy odds modules remain importable"]:
            assert legacy not in text, f"{path} still references {legacy}"
        for canonical in [
            "src.services.odds_runtime_bridge",
            "src.connectors.odds_data",
            "src.providers.sportsbooks",
        ]:
            assert canonical in text, f"{path} is missing canonical reference: {canonical}"


def test_canonical_bridge_provider_and_connector_imports_are_safe_and_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    _run_import_safety_check(
        [
            "src.connectors.odds_data",
            "src.connectors.errors",
            "src.services.odds_runtime_bridge",
            "src.providers.sportsbooks",
            "src.providers.registry",
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
    with pytest.raises(errors.ConnectorDisabledError):
        disabled_client.fetch_odds()

    adapter = bridge.SharpSportsbookAdapter({"enabled": False, "live_calls_enabled": False, "dry_run": True})
    snapshot = bridge.get_sportsbook_snapshot(adapter)
    assert snapshot["status"] == "provider_disabled"
    assert snapshot["records"] == []
    assert snapshot["connector_configuration"]["provider"] == "odds_data"
    assert snapshot["connector_readiness"]["status"] == "disabled"

    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_events()
    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_odds()
    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_player_props()
    with pytest.raises(errors.ConnectorDisabledError):
        adapter.fetch_sports()

    sportsbook_module = importlib.import_module("src.providers.sportsbooks")
    assert sportsbook_module is not None


def test_legacy_shell_importability_is_proved_only_as_historical_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
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

    async def _check_async_disabled() -> None:
        adapter = sharp_api.SharpApiAdapter()
        with pytest.raises(errors.ConnectorDisabledError):
            await adapter.get_supported_sports()
        with pytest.raises(errors.ConnectorDisabledError):
            await adapter.get_active_events("nba", "nba")
        with pytest.raises(errors.ConnectorDisabledError):
            await adapter.get_event_odds("evt1", "nba", "nba")
        with pytest.raises(errors.ConnectorDisabledError):
            await adapter.get_first_event_odds("nba", "nba")

        odds_adapter = odds_api.TheOddsApiAdapter()
        with pytest.raises(errors.ConnectorDisabledError):
            await odds_adapter.get_supported_sports()
        with pytest.raises(errors.ConnectorDisabledError):
            await odds_adapter.get_odds_events("basketball_nba", "nba")
        with pytest.raises(errors.ConnectorDisabledError):
            await odds_adapter.get_active_events("basketball_nba", "nba")
        with pytest.raises(errors.ConnectorDisabledError):
            await odds_adapter.get_event_odds("evt1", "basketball_nba", "nba")
        with pytest.raises(errors.ConnectorDisabledError):
            await odds_adapter.get_first_event_odds("basketball_nba", "nba")

        sports_adapter = sports_game.SportsGameOddsAdapter()
        with pytest.raises(errors.ConnectorDisabledError):
            await sports_adapter.get_active_events("basketball_nba", "nba")

    asyncio.run(_check_async_disabled())

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


def test_runtime_files_have_no_forbidden_live_network_imports() -> None:
    for path in [
        ROOT / "src" / "services" / "odds_runtime_bridge.py",
        ROOT / "src" / "connectors" / "odds_data" / "__init__.py",
        ROOT / "src" / "providers" / "sportsbooks" / "contracts.py",
        ROOT / "src" / "providers" / "sportsbooks" / "adapters.py",
    ]:
        text = _read(path).lower()
        for forbidden in [
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
        ]:
            assert forbidden not in text, f"{path} still references {forbidden}"


def test_delete_readiness_documentation_states_no_remaining_blockers() -> None:
    import_scan = _read(ROOT / "ODDS_FINAL_IMPORT_SCAN_AFTER_10K8ZGO.md")
    delete_readiness = _read(ROOT / "FINAL_ODDS_SHELL_DELETE_PROOF_AFTER_10K8ZGO.md")

    for blocker in [
        "tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py",
    ]:
        assert blocker in import_scan
        assert "historical evidence only" in import_scan.lower()

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
        assert "delete-ready now" in delete_readiness.lower()
        assert "no remaining file-level barriers" in delete_readiness.lower()
