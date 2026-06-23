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
    ROOT / "PHASE10K8ZGM_ODDS_HISTORICAL_TEST_REDIRECTION.md",
    ROOT / "ODDS_HISTORICAL_TEST_REDIRECTION_MAP_AFTER_10K8ZGM.md",
    ROOT / "ODDS_SHELL_IMPORT_SCAN_AFTER_10K8ZGM.md",
    ROOT / "ODDS_SHELL_DELETE_READINESS_AFTER_10K8ZGM.md",
]

REDIRECTED_TESTS = [
    ROOT / "tests" / "test_sharp_sportsbook_adapter.py",
    ROOT / "tests" / "test_sportsbook_odds_provider.py",
]

LEGACY_MODULES = [
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


def test_docs_exist_and_contain_required_redirection_language() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Big-Picture Architecture",
        "Historical Test Redirection",
        "Canonical Disabled Surfaces",
        "Import Scan Summary",
        "Test Redirection Summary",
        "Delete-Readiness",
        "Compatibility Policy",
        "No-Deletion / No-Call Guarantees",
        "Next Recommended Phase",
    ]:
        assert section in combined, section

    required_statement = (
        "Odds shell deletion is authorized only after runtime imports, historical test imports, compatibility proof, and full local gate proof are clean. "
        "This phase proves readiness only and does not delete legacy odds modules."
    )
    assert required_statement in combined

    for phrase in [
        "tests/test_sharp_sportsbook_adapter.py",
        "tests/test_sportsbook_odds_provider.py",
        "src.services.odds_runtime_bridge",
        "src.connectors.odds_data",
        "src.providers.sportsbooks",
        "No deletion occurred",
        "No live API calls were made",
        "legacy odds modules remain importable",
    ]:
        assert phrase in combined


def test_redirected_historical_tests_reference_canonical_bridge_and_connector() -> None:
    sharp_adapter_test = _read(REDIRECTED_TESTS[0])
    sportsbook_provider_test = _read(REDIRECTED_TESTS[1])

    for text in (sharp_adapter_test, sportsbook_provider_test):
        assert "src.services.odds_runtime_bridge" in text
        assert "src.connectors.odds_data" in text
        assert "automation_scheduler.sharp_sportsbook_adapter" not in text
        assert "automation_scheduler.sportsbook_odds_provider" not in text
        assert "providers.sharp_provider" not in text
        assert "sharp_client" not in text
        assert "the_odds_api" not in text
        assert "sportsgameodds" not in text


def test_canonical_bridge_and_connector_imports_are_safe_and_disabled() -> None:
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

    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_events()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_odds()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_player_props()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_sports()


def test_legacy_odds_shells_remain_importable_and_not_deleted() -> None:
    for module_name in LEGACY_MODULES:
        module = importlib.import_module(module_name)
        assert module is not None

    for path in [
        ROOT / "sharp_client.py",
        ROOT / "providers" / "sharp_provider.py",
        ROOT / "betting_providers" / "sharp_api.py",
        ROOT / "betting_providers" / "the_odds_api.py",
        ROOT / "betting_providers" / "sportsgameodds.py",
        ROOT / "automation_scheduler" / "sharp_sportsbook_adapter.py",
        ROOT / "automation_scheduler" / "sportsbook_odds_provider.py",
    ]:
        assert path.exists(), path


def test_delete_readiness_documentation_matches_remaining_blockers() -> None:
    import_scan = _read(ROOT / "ODDS_SHELL_IMPORT_SCAN_AFTER_10K8ZGM.md")
    delete_readiness = _read(ROOT / "ODDS_SHELL_DELETE_READINESS_AFTER_10K8ZGM.md")

    for blocker in [
        "tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py",
        "tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py",
        "tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py",
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


def test_runtime_and_historical_files_have_no_forbidden_live_imports() -> None:
    for path in REDIRECTED_TESTS + [
        ROOT / "src" / "services" / "odds_runtime_bridge.py",
        ROOT / "src" / "connectors" / "odds_data" / "__init__.py",
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
