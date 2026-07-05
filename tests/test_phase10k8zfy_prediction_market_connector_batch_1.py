from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PHASE10K8ZFY_PREDICTION_MARKET_CONNECTOR_BATCH_1.md"
MIGRATION_MAP_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PREDICTION_MARKET_CONNECTOR_MIGRATION_MAP_AFTER_10K8ZFY.md"
LEGACY_COMPAT_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PHASE10K8ZFY_PREDICTION_MARKET_CONNECTOR_BATCH_1.md"
DISABLED_REPORT_PATH = ROOT / "docs" / "archive" / "historical_reports" / "CONNECTOR_DISABLED_BEHAVIOR_REPORT_AFTER_10K8ZFY.md"

CONNECTOR_MODULES = [
    "src.connectors.prediction_market_data",
    "src.connectors.prediction_market_data.client",
    "src.connectors.prediction_market_data.read_only",
    "src.connectors.prediction_market_data.adapter",
    "src.connectors.prediction_market_data.models",
    "src.connectors.prediction_market_data.payloads",
    "src.connectors.prediction_market_data.contracts",
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

def _module_path(module_name: str) -> Path:
    if module_name == "src.connectors.prediction_market_data":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "__init__.py"
    if module_name == "src.connectors.prediction_market_data.client":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "client.py"
    if module_name == "src.connectors.prediction_market_data.read_only":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "read_only.py"
    if module_name == "src.connectors.prediction_market_data.adapter":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "adapter.py"
    if module_name == "src.connectors.prediction_market_data.models":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "models.py"
    if module_name == "src.connectors.prediction_market_data.payloads":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "payloads.py"
    if module_name == "src.connectors.prediction_market_data.contracts":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "contracts.py"
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


def test_prediction_market_connector_wrapper_imports_are_safe_and_disabled(monkeypatch):
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("credential access at import time is forbidden")))

    for module_name in CONNECTOR_MODULES:
        path = _module_path(module_name)
        assert path.is_file()
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

        text = path.read_text(encoding="utf-8").lower()
        assert "kalshi" not in text
        assert "sharp" not in text
        assert "getenv" not in text
        assert "load_dotenv" not in text

        for name in _import_names(path):
            assert name not in FORBIDDEN_DIRECT_IMPORTS
            assert not name.startswith("automation_scheduler")
            assert not name.startswith("betting_providers")
            assert not name.startswith("providers.")
            assert not name.startswith("src.providers")

    connector_pkg = importlib.import_module("src.connectors.prediction_market_data")
    assert connector_pkg.PredictionMarketConnectorAdapter.__name__ == "PredictionMarketConnectorAdapter"
    assert connector_pkg.PredictionMarketReadOnlyClient.__name__ == "PredictionMarketReadOnlyClient"

    client = connector_pkg.PredictionMarketReadOnlyClient()
    adapter = connector_pkg.PredictionMarketConnectorAdapter(client=client)

    assert client.describe()["read_only"] is True
    assert adapter.describe()["live_access_enabled"] is False

    payload = {"provider": "prediction_market_data", "market_id": "m1", "event_id": "e1", "title": "Demo"}
    normalized = client.normalize_payload(payload)
    assert normalized["_connector_category"] == "prediction_market_data"
    assert normalized["_read_only"] is True

    snapshot = client.build_snapshot([payload])
    assert snapshot.status == "inert"
    assert len(snapshot.records) == 1
    assert snapshot.records[0].provider == "prediction_market_data"

    record = adapter.build_record(payload)
    assert record.market_id == "m1"
    assert adapter.validate_payload(payload)["ok"] is True

    with pytest.raises(ConnectorDisabledError) as excinfo:
        client.fetch_markets()

    with pytest.raises(ConnectorDisabledError):
        client.fetch_events()
    with pytest.raises(ConnectorDisabledError):
        client.fetch_snapshot()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_markets()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_events()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_snapshot()


def test_legacy_prediction_market_shell_names_remain_historical_evidence_only():
    legacy_evidence = [
        "providers/kalshi_provider.py",
        "betting_providers/kalshi_api.py",
        "automation_scheduler/kalshi_readonly_adapter.py",
        "automation_scheduler/kalshi_market_provider.py",
        "kalshi_client.py",
    ]
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [REPORT_PATH, MIGRATION_MAP_PATH, LEGACY_COMPAT_PATH, DISABLED_REPORT_PATH]
    )
    for relative in legacy_evidence:
        assert relative in combined
    assert "historical evidence only" in combined or "reclassified" in combined or "legacy modules remain in place" in combined


def test_phase_docs_cover_required_connector_language_and_vendor_neutrality():
    for path in (REPORT_PATH, MIGRATION_MAP_PATH, LEGACY_COMPAT_PATH, DISABLED_REPORT_PATH):
        assert path.is_file()

    report = REPORT_PATH.read_text(encoding="utf-8")
    migration_map = MIGRATION_MAP_PATH.read_text(encoding="utf-8")
    legacy_compat = LEGACY_COMPAT_PATH.read_text(encoding="utf-8")
    disabled_report = DISABLED_REPORT_PATH.read_text(encoding="utf-8")

    combined = "\n".join([report, migration_map, legacy_compat, disabled_report])
    for required in [
        "10K8ZFY",
        "Prediction-market connector migration has begun only as an inert read-only connector wrapper.",
        "connector wrapper means",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "Why Vendor-Neutral Naming Was Used",
        "Next Recommended Phase",
        "ConnectorDisabledError",
    ]:
        assert required in combined

    assert "kalshi" in combined.lower()  # legacy evidence remains documented
    assert "src/connectors/prediction_market_data" in combined
    assert "legacy evidence only" in legacy_compat.lower()
    assert "disabled" in disabled_report.lower()
    assert "fetch_markets() raises ConnectorDisabledError" in disabled_report

    assert not list((ROOT / "src" / "connectors" / "prediction_market_data").glob("kalshi*.py"))
    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
