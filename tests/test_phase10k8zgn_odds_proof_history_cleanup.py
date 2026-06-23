from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGN_ODDS_PROOF_HISTORY_CLEANUP.md",
    ROOT / "ODDS_PROOF_HISTORY_REFERENCE_SCAN_AFTER_10K8ZGN.md",
    ROOT / "ODDS_PROOF_HISTORY_CLEANUP_MAP_AFTER_10K8ZGN.md",
    ROOT / "FINAL_ODDS_DELETE_READINESS_AFTER_10K8ZGN.md",
]

CLEANED_TESTS = [
    ROOT / "tests" / "test_phase10k8zgi_odds_runtime_consumer_redirection.py",
    ROOT / "tests" / "test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py",
    ROOT / "tests" / "test_phase10k8zgm_odds_historical_test_redirection.py",
]

RETIRED_COMPATIBILITY_TESTS = [
    ROOT / "tests" / "test_phase10k8zgj_odds_legacy_live_method_retirement.py",
    ROOT / "tests" / "test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py",
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


def test_docs_exist_and_reclassify_history_as_evidence_only() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Big-Picture Architecture",
        "Proof-History References Before Cleanup",
        "References Updated or Reclassified",
        "Remaining References After Cleanup",
        "Delete-Readiness",
        "Compatibility Policy",
        "No-Deletion / No-Call Guarantees",
        "Next Recommended Phase",
    ]:
        assert section in combined, section

    required_statement = (
        "Proof-history references must not preserve legacy odds shells unnecessarily. "
        "This phase reclassifies historical evidence and proves delete readiness, but does not delete legacy odds modules."
    )
    assert required_statement in combined

    for phrase in [
        "historical evidence only",
        "explicit compatibility proofs",
        "tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py",
        "src.services.odds_runtime_bridge",
        "src.connectors.odds_data",
        "src.providers.sportsbooks",
        "No deletion occurred",
        "No live API calls were made",
    ]:
        assert phrase in combined


def test_cleaned_history_files_no_longer_require_legacy_shell_importability() -> None:
    for path in CLEANED_TESTS:
        text = _read(path)
        for canonical in [
            "src.services.odds_runtime_bridge",
            "src.connectors.odds_data",
        ]:
            assert canonical in text, f"{path} is missing canonical reference: {canonical}"
        assert "legacy odds modules remain importable" not in text


def test_retired_compatibility_tests_no_longer_reference_legacy_shells() -> None:
    for path in RETIRED_COMPATIBILITY_TESTS:
        text = _read(path)
        for legacy in [
            "sharp_client",
            "providers.sharp_provider",
            "betting_providers.sharp_api",
            "betting_providers.the_odds_api",
            "betting_providers.sportsgameodds",
            "automation_scheduler.sharp_sportsbook_adapter",
            "automation_scheduler.sportsbook_odds_provider",
        ]:
            assert legacy not in text, f"{path} still references {legacy}"


def test_canonical_bridge_and_connector_imports_are_safe_and_disabled() -> None:
    _run_import_safety_check(
        [
            "src.connectors.odds_data",
            "src.connectors.errors",
            "src.services.odds_runtime_bridge",
            "src.providers.sportsbooks",
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


def test_delete_readiness_documentation_only_blocks_explicit_compatibility_tests() -> None:
    delete_readiness = _read(ROOT / "FINAL_ODDS_SHELL_DELETE_PROOF_AFTER_10K8ZGO.md")
    import_scan = _read(ROOT / "ODDS_FINAL_IMPORT_SCAN_AFTER_10K8ZGO.md")

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
        assert "blocked" not in delete_readiness.lower()


def test_runtime_files_have_no_forbidden_live_imports() -> None:
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
