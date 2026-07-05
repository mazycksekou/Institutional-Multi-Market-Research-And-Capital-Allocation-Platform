from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZG0_MARKET_DATA_CONNECTOR_BATCH_3.md"
MIGRATION_MAP_PATH = ROOT / "MARKET_DATA_CONNECTOR_MIGRATION_MAP_AFTER_10K8ZG0.md"
LEGACY_COMPAT_PATH = ROOT / "MARKET_DATA_LEGACY_COMPATIBILITY_AFTER_10K8ZG0.md"
DISABLED_REPORT_PATH = ROOT / "MARKET_DATA_DISABLED_BEHAVIOR_REPORT_AFTER_10K8ZG0.md"

CONNECTOR_MODULES = [
    "src.connectors.market_data",
    "src.connectors.market_data.client",
    "src.connectors.market_data.read_only",
    "src.connectors.market_data.adapter",
    "src.connectors.market_data.models",
    "src.connectors.market_data.payloads",
    "src.connectors.market_data.contracts",
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

FORBIDDEN_VENDOR_NAMES = {
    "alpaca",
    "robinhood",
    "polygon",
    "tradier",
    "iex",
    "yfinance",
    "schwab",
    "nasdaq",
}


def _module_path(module_name: str) -> Path:
    if module_name == "src.connectors.market_data":
        return ROOT / "src" / "connectors" / "market_data" / "__init__.py"
    if module_name == "src.connectors.market_data.client":
        return ROOT / "src" / "connectors" / "market_data" / "client.py"
    if module_name == "src.connectors.market_data.read_only":
        return ROOT / "src" / "connectors" / "market_data" / "read_only.py"
    if module_name == "src.connectors.market_data.adapter":
        return ROOT / "src" / "connectors" / "market_data" / "adapter.py"
    if module_name == "src.connectors.market_data.models":
        return ROOT / "src" / "connectors" / "market_data" / "models.py"
    if module_name == "src.connectors.market_data.payloads":
        return ROOT / "src" / "connectors" / "market_data" / "payloads.py"
    if module_name == "src.connectors.market_data.contracts":
        return ROOT / "src" / "connectors" / "market_data" / "contracts.py"
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


def test_market_data_connector_wrapper_imports_are_safe_and_disabled(monkeypatch):
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("credential access at import time is forbidden")))

    for module_name in CONNECTOR_MODULES:
        path = _module_path(module_name)
        assert path.is_file()
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

        text = path.read_text(encoding="utf-8").lower()
        for vendor_name in FORBIDDEN_VENDOR_NAMES:
            assert vendor_name not in text
        assert "getenv" not in text
        assert "load_dotenv" not in text

        for name in _import_names(path):
            assert name not in FORBIDDEN_DIRECT_IMPORTS
            assert not name.startswith("automation_scheduler")
            assert not name.startswith("betting_providers")
            assert not name.startswith("providers.")
            assert not name.startswith("src.providers")

    connector_pkg = importlib.import_module("src.connectors.market_data")
    assert connector_pkg.MarketDataConnectorAdapter.__name__ == "MarketDataConnectorAdapter"
    assert connector_pkg.MarketDataReadOnlyClient.__name__ == "MarketDataReadOnlyClient"

    client = connector_pkg.MarketDataReadOnlyClient()
    adapter = connector_pkg.MarketDataConnectorAdapter(client=client)

    assert client.describe()["read_only"] is True
    assert adapter.describe()["live_access_enabled"] is False

    payload = {"provider": "market_data", "symbol": "AAPL", "asset_class": "equity", "exchange": "NASDAQ"}
    normalized = client.normalize_payload(payload)
    assert normalized["_connector_category"] == "market_data"
    assert normalized["_read_only"] is True

    snapshot = client.build_snapshot([payload])
    assert snapshot.status == "inert"
    assert len(snapshot.records) == 1
    assert snapshot.records[0].provider == "market_data"

    quote = adapter.build_quote(payload)
    assert quote.symbol == "AAPL"
    assert adapter.validate_payload(payload)["ok"] is True

    with pytest.raises(ConnectorDisabledError):
        client.fetch_market_data()
    with pytest.raises(ConnectorDisabledError):
        client.fetch_quotes()
    with pytest.raises(ConnectorDisabledError):
        client.fetch_snapshot()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_market_data()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_quotes()
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_snapshot()


def test_connector_related_wrapper_imports_still_resolve():
    prediction_market = importlib.import_module("src.connectors.prediction_market_data")
    odds_data = importlib.import_module("src.connectors.odds_data")

    assert prediction_market.PredictionMarketConnectorAdapter.__name__ == "PredictionMarketConnectorAdapter"
    assert odds_data.OddsDataConnectorAdapter.__name__ == "OddsDataConnectorAdapter"


def test_phase_docs_cover_required_connector_language_and_vendor_neutrality():
    for path in (REPORT_PATH, MIGRATION_MAP_PATH, LEGACY_COMPAT_PATH, DISABLED_REPORT_PATH):
        assert path.is_file()

    report = REPORT_PATH.read_text(encoding="utf-8")
    migration_map = MIGRATION_MAP_PATH.read_text(encoding="utf-8")
    legacy_compat = LEGACY_COMPAT_PATH.read_text(encoding="utf-8")
    disabled_report = DISABLED_REPORT_PATH.read_text(encoding="utf-8")

    combined = "\n".join([report, migration_map, legacy_compat, disabled_report])
    for required in [
        "10K8ZG0",
        "Market-data connector migration has begun only as an inert read-only connector wrapper.",
        "why market_data exists separately from providers",
        "zero_dte_stocks",
        "Vendor-Neutral Ownership Policy",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "No-Execution Guarantee",
        "Next Recommended Phase",
        "ConnectorDisabledError",
    ]:
        assert required in combined

    assert "market_data" in combined
    assert "legacy" in legacy_compat.lower()
    assert "disabled" in disabled_report.lower()
    assert "fetch_market_data()" in disabled_report
    assert "ConnectorDisabledError" in disabled_report
    assert not list((ROOT / "src" / "connectors" / "market_data").glob("alpaca*.py"))
    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
