from __future__ import annotations

import ast
import importlib
import os
import re
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PHASE10K8ZFZ_ODDS_DATA_CONNECTOR_BATCH_2.md"
MIGRATION_MAP_PATH = ROOT / "docs" / "archive" / "historical_reports" / "ODDS_DATA_CONNECTOR_MIGRATION_MAP_AFTER_10K8ZFZ.md"
LEGACY_COMPAT_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PHASE10K8ZFZ_ODDS_DATA_CONNECTOR_BATCH_2.md"
DISABLED_REPORT_PATH = ROOT / "docs" / "archive" / "historical_reports" / "ODDS_DATA_DISABLED_BEHAVIOR_REPORT_AFTER_10K8ZFZ.md"

CONNECTOR_MODULES = [
    "src.connectors.odds_data",
    "src.connectors.odds_data.client",
    "src.connectors.odds_data.read_only",
    "src.connectors.odds_data.adapter",
    "src.connectors.odds_data.models",
    "src.connectors.odds_data.payloads",
    "src.connectors.odds_data.contracts",
]

FORBIDDEN_DIRECT_IMPORTS = {
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}

LEGACY_IMPORTS = [
    "providers.sharp_provider",
    "betting_providers.sharp_api",
    "betting_providers.the_odds_api",
    "betting_providers.sportsgameodds",
    'src.automation_scheduler_legacy.sharp_sportsbook_adapter',
    'src.automation_scheduler_legacy.sportsbook_odds_provider',
    "sharp_client",
]


def _module_path(module_name: str) -> Path:
    if module_name == "src.connectors.odds_data":
        return ROOT / "src" / "connectors" / "odds_data" / "__init__.py"
    if module_name == "src.connectors.odds_data.client":
        return ROOT / "src" / "connectors" / "odds_data" / "client.py"
    if module_name == "src.connectors.odds_data.read_only":
        return ROOT / "src" / "connectors" / "odds_data" / "read_only.py"
    if module_name == "src.connectors.odds_data.adapter":
        return ROOT / "src" / "connectors" / "odds_data" / "adapter.py"
    if module_name == "src.connectors.odds_data.models":
        return ROOT / "src" / "connectors" / "odds_data" / "models.py"
    if module_name == "src.connectors.odds_data.payloads":
        return ROOT / "src" / "connectors" / "odds_data" / "payloads.py"
    if module_name == "src.connectors.odds_data.contracts":
        return ROOT / "src" / "connectors" / "odds_data" / "contracts.py"
    raise ValueError(module_name)


def _import_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _has_deleted_module_import_statements(path: Path, deleted_modules: list[str]) -> bool:
    text = path.read_text(encoding="utf-8")
    for module in deleted_modules:
        pattern = re.compile(
            rf"^\s*(?:from|import)\s+{re.escape(module)}\b|importlib\.import_module\(\s*[\"']{re.escape(module)}[\"']\s*\)",
            re.MULTILINE,
        )
        if re.search(pattern, text):
            return True
    return False


def test_odds_data_connector_wrapper_imports_are_safe_and_disabled(monkeypatch):
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("credential access at import time is forbidden")))

    for module_name in CONNECTOR_MODULES:
        path = _module_path(module_name)
        assert path.is_file()
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

        text = path.read_text(encoding="utf-8").lower()
        assert "sharp" not in text
        assert "the_odds_api" not in text
        assert "sportsgameodds" not in text
        assert "getenv" not in text
        assert "load_dotenv" not in text

        for name in _import_names(path):
            assert name not in FORBIDDEN_DIRECT_IMPORTS
            assert not name.startswith("automation_scheduler")
            assert not name.startswith("betting_providers")
            assert not name.startswith("providers.")
            assert not name.startswith("src.providers")

    connector_pkg = importlib.import_module("src.connectors.odds_data")
    assert connector_pkg.OddsDataConnectorAdapter.__name__ == "OddsDataConnectorAdapter"
    assert connector_pkg.OddsDataReadOnlyClient.__name__ == "OddsDataReadOnlyClient"

    client = connector_pkg.OddsDataReadOnlyClient()
    adapter = connector_pkg.OddsDataConnectorAdapter(client=client)

    assert client.describe()["read_only"] is True
    assert adapter.describe()["live_access_enabled"] is False

    payload = {"provider": "odds_data", "event_id": "e1", "market": "moneyline", "selection": "home"}
    normalized = client.normalize_payload(payload)
    assert normalized["_connector_category"] == "odds_data"
    assert normalized["_read_only"] is True

    snapshot = client.build_snapshot([payload])
    assert snapshot.status == "inert"
    assert len(snapshot.records) == 1
    assert snapshot.records[0].provider == "odds_data"

    record = adapter.build_record(payload)
    assert record.event_id == "e1"
    assert adapter.validate_payload(payload)["ok"] is True

    with pytest.raises(ConnectorDisabledError):
        client.fetch_odds()
    with pytest.raises(ConnectorDisabledError):
        client.fetch_events()
    with pytest.raises(ConnectorDisabledError):
        client.fetch_snapshot()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_odds()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_events()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_snapshot()


def test_legacy_odds_imports_are_no_longer_active_dependencies():
    deleted_modules = [
        "sharp_client",
        "providers.sharp_provider",
        "betting_providers.sharp_api",
        "betting_providers.the_odds_api",
        "betting_providers.sportsgameodds",
        'src.automation_scheduler_legacy.sharp_sportsbook_adapter',
        'src.automation_scheduler_legacy.sportsbook_odds_provider',
    ]
    historical_evidence_files = {
        ROOT / "tests" / "test_phase10k8zgz_post_provider_connector_cleanup_freeze.py",
    }

    for path in ROOT.rglob("*.py"):
        if path == Path(__file__):
            continue
        if path in historical_evidence_files:
            continue
        assert not _has_deleted_module_import_statements(path, deleted_modules), path

    service = importlib.import_module("src.services.enrichment_service")
    assert hasattr(service.EnrichmentService, "enrich_ticket")


def test_phase_docs_cover_required_connector_language_and_vendor_neutrality():
    for path in (REPORT_PATH, MIGRATION_MAP_PATH, LEGACY_COMPAT_PATH, DISABLED_REPORT_PATH):
        assert path.is_file()

    report = REPORT_PATH.read_text(encoding="utf-8")
    migration_map = MIGRATION_MAP_PATH.read_text(encoding="utf-8")
    legacy_compat = LEGACY_COMPAT_PATH.read_text(encoding="utf-8")
    disabled_report = DISABLED_REPORT_PATH.read_text(encoding="utf-8")

    combined = "\n".join([report, migration_map, legacy_compat, disabled_report])
    for required in [
        "10K8ZFZ",
        "Odds-data connector migration has begun only as an inert read-only connector wrapper.",
        "odds-data connector wrapper means",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "No-Execution Guarantee",
        "Why Vendor-Neutral Naming Was Used",
        "Next Recommended Phase",
        "ConnectorDisabledError",
    ]:
        assert required in combined

    assert "sharp" in combined.lower()  # legacy evidence remains documented
    assert "src/connectors/odds_data" in combined
    assert "legacy evidence only" in legacy_compat.lower()
    assert "disabled" in disabled_report.lower()
    assert "fetch_odds() raises ConnectorDisabledError" in disabled_report

    for path in (ROOT / "src" / "connectors" / "odds_data").glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "sharp" not in text
        assert "the_odds_api" not in text
        assert "sportsgameodds" not in text

    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
