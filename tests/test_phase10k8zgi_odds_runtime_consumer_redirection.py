from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGI_ODDS_RUNTIME_CONSUMER_REDIRECTION.md",
    ROOT / "ODDS_RUNTIME_CONSUMER_REDIRECTION_MAP_AFTER_10K8ZGI.md",
    ROOT / "ODDS_LEGACY_IMPORT_SCAN_AFTER_10K8ZGI.md",
    ROOT / "ODDS_LEGACY_DELETE_READINESS_AFTER_10K8ZGI.md",
]

CANONICAL_MODULES = [
    "src.services.odds_runtime_bridge",
    "src.connectors.odds_data",
    "src.providers.sportsbooks",
    "src.providers.registry",
]

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Current HEAD",
    "Purpose",
    "Scope",
    "Non-Goals",
    "Big-Picture Architecture",
    "Runtime Consumer Redirection",
    "Canonical Disabled Surfaces",
    "Delete-Readiness",
    "Remaining Blockers",
    "Compatibility Policy",
    "No-Deletion / No-Call Guarantees",
    "Next Recommended Phase",
]

REQUIRED_STATEMENT = (
    "Odds runtime consumers are redirected toward connector-owned disabled surfaces in this phase. "
    "This phase does not authorize live API calls, credential reads, bet execution, route rewrites, or deletion of legacy odds modules."
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def _fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_docs_and_redirection_files_exist_and_contain_required_language() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in REQUIRED_SECTIONS:
        assert section in combined, f"missing section: {section}"

    assert REQUIRED_STATEMENT in combined

    for needle in [
        "No deletion occurred",
        "No live calls were made",
        "No credentials were read at import time",
        "src.connectors.odds_data",
        "ODDS_DATA_CONNECTOR_CONFIGURATION",
        "ODDS_DATA_CONNECTOR_READINESS",
        "compatibility-preserving runtime consumers",
    ]:
        assert needle in combined


def test_odds_runtime_consumer_modules_import_canonical_connector_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("credential access at import time is forbidden")),
    )

    for module_name in CANONICAL_MODULES:
        module = _fresh_import(module_name)
        assert module is not None
        if hasattr(module, "ODDS_DATA_CONNECTOR_CONFIGURATION"):
            assert hasattr(module, "ODDS_DATA_CONNECTOR_READINESS")
            readiness = getattr(module, "ODDS_DATA_CONNECTOR_READINESS")
            assert readiness["status"] == "disabled"
            configuration = getattr(module, "ODDS_DATA_CONNECTOR_CONFIGURATION")
            assert configuration.describe()["provider"] == "odds_data"
        else:
            assert module.__name__ in {
                "src.services.odds_runtime_bridge",
                "src.connectors.odds_data",
                "src.providers.sportsbooks",
                "src.providers.registry",
            }


def test_connector_boundary_and_disabled_client_remain_safe() -> None:
    connector = importlib.import_module("src.connectors.odds_data")
    errors = importlib.import_module("src.connectors.errors")

    assert connector.describe_odds_data_connector_readiness()["status"] == "disabled"
    assert connector.build_odds_data_connector_configuration().provider == "odds_data"

    disabled_client = connector.build_odds_data_disabled_live_client()
    with pytest.raises(errors.ConnectorDisabledError):
        disabled_client.fetch_odds()


def test_updated_runtime_files_reference_the_canonical_connector_boundary() -> None:
    for path in [
        ROOT / "src" / "services" / "odds_runtime_bridge.py",
        ROOT / "src" / "services" / "enrichment_service.py",
        ROOT / "automation_scheduler" / "scheduler_runner.py",
        ROOT / "automation_scheduler" / "__init__.py",
    ]:
        text = path.read_text(encoding="utf-8")
        if path.name == "odds_runtime_bridge.py":
            assert "src.connectors.odds_data" in text
            assert "ODDS_DATA_CONNECTOR_CONFIGURATION" in text
            assert "ODDS_DATA_CONNECTOR_READINESS" in text
        else:
            assert "src.services.odds_runtime_bridge" in text
