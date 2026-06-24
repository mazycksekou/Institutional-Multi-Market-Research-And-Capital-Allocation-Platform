from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGP_ODDS_COMPATIBILITY_SHELL_DELETION.md",
    ROOT / "ODDS_COMPATIBILITY_SHELL_DELETION_PROOF_AFTER_10K8ZGP.md",
    ROOT / "POST_ODDS_SHELL_DELETION_IMPORT_SCAN_AFTER_10K8ZGP.md",
    ROOT / "ODDS_DELETION_COMPLETION_STATUS_AFTER_10K8ZGP.md",
]
DELETED_FILES = [
    ROOT / "sharp_client.py",
    ROOT / "providers" / "sharp_provider.py",
    ROOT / "betting_providers" / "sharp_api.py",
    ROOT / "betting_providers" / "the_odds_api.py",
    ROOT / "betting_providers" / "sportsgameodds.py",
    ROOT / "automation_scheduler" / "sharp_sportsbook_adapter.py",
    ROOT / "automation_scheduler" / "sportsbook_odds_provider.py",
]
DELETED_MODULES = [
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


def _assert_no_import_statements_reference_deleted_modules(
    historical_evidence_files: set[Path] | None = None,
) -> None:
    import_pattern = re.compile(
        r"^\s*(?:from|import)\s+{module}\b|importlib\.import_module\(\s*[\"']{module}[\"']\s*\)",
        re.MULTILINE,
    )

    for path in ROOT.rglob("*.py"):
        if path == Path(__file__):
            continue
        if historical_evidence_files and path in historical_evidence_files:
            continue
        text = path.read_text(encoding="utf-8")
        for module in DELETED_MODULES:
            pattern = import_pattern.pattern.format(module=re.escape(module))
            assert not re.search(pattern, text), f"active import found in {path}: {module}"


def test_docs_exist_and_contain_required_statement() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Big-Picture Architecture",
        "Proof Source From 10K8ZGO",
        "Import Scan Before Deletion",
        "Import Scan After Deletion",
        "Tests Run",
        "Behavior Preserved",
        "Remaining Legacy Odds / Runtime Files Not Touched",
        "Next Recommended Phase",
    ]:
        assert section in combined, section

    required_statement = (
        "Only the seven proof-backed legacy odds compatibility shells are deleted in this phase. "
        "Runtime modules, dashboard files, entrypoints, connector scaffolds, AI scaffolds, brokerage scaffolds, and prediction-market legacy modules are preserved."
    )
    assert required_statement in combined

    for phrase in [
        "canonical odds flow remains",
        "deleted files",
        "no active test imports deleted odds modules",
        "no tracked runtime file imports deleted odds modules",
        "behavior preserved",
        "no live odds api calls are enabled",
        "no import-time credential reads",
    ]:
        assert phrase in combined.lower()


def test_deleted_files_are_gone_and_canonical_flow_remains_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    for path in DELETED_FILES:
        assert not path.exists(), f"deleted file still exists: {path}"

    _run_import_safety_check(
        [
            "src.services.odds_runtime_bridge",
            "src.connectors.odds_data",
            "src.connectors.errors",
            "src.providers.sportsbooks",
            "src.providers.sportsbooks.adapters",
        ]
    )

    connector = importlib.import_module("src.connectors.odds_data")
    errors = importlib.import_module("src.connectors.errors")
    bridge = importlib.import_module("src.services.odds_runtime_bridge")
    sportsbook_adapters = importlib.import_module("src.providers.sportsbooks.adapters")

    readiness = connector.describe_odds_data_connector_readiness()
    assert readiness["status"] == "disabled"
    assert readiness["read_only"] is True

    configuration = connector.build_odds_data_connector_configuration()
    assert configuration.provider == "odds_data"
    assert configuration.credential_names == ("ODDS_DATA_API_KEY", "ODDS_DATA_API_SECRET")

    disabled_client = connector.build_odds_data_disabled_live_client()
    for action in [disabled_client.fetch_odds, disabled_client.fetch_snapshot]:
        with pytest.raises(RuntimeError) as exc_info:
            action()
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


def test_no_active_py_file_imports_deleted_odds_modules() -> None:
    historical_evidence_files = {
        ROOT / "tests" / "test_phase10k8zgz_post_provider_connector_cleanup_freeze.py",
    }

    _assert_no_import_statements_reference_deleted_modules(historical_evidence_files)
