from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest

from src.providers.errors import ProviderUnavailableError

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZG1_ZERO_DTE_STOCKS_PROVIDER_BATCH.md"
MIGRATION_MAP_PATH = ROOT / "ZERO_DTE_STOCKS_PROVIDER_MIGRATION_MAP_AFTER_10K8ZG1.md"
BOUNDARY_PATH = ROOT / "ZERO_DTE_STOCKS_PROVIDER_CONNECTOR_BOUNDARY_AFTER_10K8ZG1.md"
DISABLED_PATH = ROOT / "ZERO_DTE_STOCKS_DISABLED_BEHAVIOR_REPORT_AFTER_10K8ZG1.md"

PROVIDER_MODULES = [
    "src.providers.zero_dte_stocks",
    "src.providers.zero_dte_stocks.provider",
    "src.providers.zero_dte_stocks.normalization",
    "src.providers.zero_dte_stocks.models",
    "src.providers.zero_dte_stocks.adapters",
    "src.providers.zero_dte_stocks.contracts",
]

FORBIDDEN_DIRECT_IMPORTS = {
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
}


def _module_path(module_name: str) -> Path:
    if module_name == "src.providers.zero_dte_stocks":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "__init__.py"
    if module_name == "src.providers.zero_dte_stocks.provider":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "provider.py"
    if module_name == "src.providers.zero_dte_stocks.normalization":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "normalization.py"
    if module_name == "src.providers.zero_dte_stocks.models":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "models.py"
    if module_name == "src.providers.zero_dte_stocks.adapters":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "adapters.py"
    if module_name == "src.providers.zero_dte_stocks.contracts":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "contracts.py"
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


def test_zero_dte_stocks_provider_wrapper_imports_are_safe_and_read_only(monkeypatch):
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("credential access at import time is forbidden")))

    for module_name in PROVIDER_MODULES:
        path = _module_path(module_name)
        assert path.is_file()
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

        text = path.read_text(encoding="utf-8").lower()
        assert "requests" not in text
        assert "httpx" not in text
        assert "yfinance" not in text
        assert "websocket" not in text
        assert "getenv" not in text

        for name in _import_names(path):
            assert name not in FORBIDDEN_DIRECT_IMPORTS
            assert not name.startswith("requests")
            assert not name.startswith("httpx")
            assert not name.startswith("yfinance")

    provider_pkg = importlib.import_module("src.providers.zero_dte_stocks")
    provider = provider_pkg.ZeroDteStockProvider()

    assert provider.describe()["read_only"] is True
    assert provider.describe()["live_access_enabled"] is False

    raw_payload = {"symbol": "AAPL", "price": 190.0, "bid": 189.8, "ask": 190.2, "volume": 100, "timestamp": "2026-06-20T00:00:00+00:00"}
    normalized = provider.normalize_payload(raw_payload)
    assert normalized["provider_type"] == "stock_price"
    assert normalized["symbol"] == "AAPL"

    market_data = importlib.import_module("src.connectors.market_data")
    market_quote = market_data.MarketDataQuote(provider="market_data", symbol="AAPL", asset_class="equity", exchange="NASDAQ", payload=raw_payload)
    market_snapshot = market_data.MarketDataSnapshot(provider="market_data", records=(market_quote,))

    normalized_quote = provider.normalize_market_data_quote(market_quote)
    normalized_snapshot = provider.normalize_market_data_snapshot(market_snapshot)
    assert normalized_quote.symbol == "AAPL"
    assert normalized_quote.provider_type == "stock_price"
    assert normalized_snapshot.quotes[0].symbol == "AAPL"
    assert normalized_snapshot.quotes[0].provider_type == "stock_price"

    built_quote = provider.build_quote(raw_payload)
    built_snapshot = provider.build_snapshot([raw_payload])
    assert built_quote.symbol == "AAPL"
    assert built_snapshot.quotes[0].symbol == "AAPL"

    assert provider.validate_payload(raw_payload)["ok"] is True

    with pytest.raises(Exception) as excinfo:
        provider.fetch_snapshot()
    assert excinfo.type.__name__ == "ProviderUnavailableError"
    assert "read-only" in str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        provider.fetch_quotes()
    assert excinfo.type.__name__ == "ProviderUnavailableError"
    assert "read-only" in str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        provider.fetch_market_data()
    assert excinfo.type.__name__ == "ProviderUnavailableError"
    assert "read-only" in str(excinfo.value)


def test_market_data_connector_and_existing_provider_batches_still_resolve():
    market_data = importlib.import_module("src.connectors.market_data")
    prediction_connector = importlib.import_module("src.connectors.prediction_market_data")
    odds_connector = importlib.import_module("src.connectors.odds_data")
    zero_dte = importlib.import_module("src.providers.zero_dte_stocks")

    assert market_data.MarketDataReadOnlyClient.__name__ == "MarketDataReadOnlyClient"
    assert prediction_connector.PredictionMarketReadOnlyClient.__name__ == "PredictionMarketReadOnlyClient"
    assert odds_connector.OddsDataReadOnlyClient.__name__ == "OddsDataReadOnlyClient"
    assert zero_dte.ZeroDteStockProviderAdapter.__name__ == "ZeroDteStockProviderAdapter"


def test_phase_docs_cover_required_language_and_boundary_guarantees():
    for path in (REPORT_PATH, MIGRATION_MAP_PATH, BOUNDARY_PATH, DISABLED_PATH):
        assert path.is_file()

    report = REPORT_PATH.read_text(encoding="utf-8")
    migration_map = MIGRATION_MAP_PATH.read_text(encoding="utf-8")
    boundary = BOUNDARY_PATH.read_text(encoding="utf-8")
    disabled = DISABLED_PATH.read_text(encoding="utf-8")

    combined = "\n".join([report, migration_map, boundary, disabled])
    for required in [
        "10K8ZG1",
        "Zero DTE stocks provider migration has begun only as a read-only normalization layer over already-supplied market-data payloads.",
        "Why zero_dte_stocks is a provider category, not a connector.",
        "MarketDataQuote",
        "MarketDataSnapshot",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "No-Execution Guarantee",
        "Next Recommended Phase",
        "ProviderUnavailableError",
    ]:
        assert required in combined

    assert "read-only" in combined.lower()
    assert "provider category" in combined.lower()
    assert "market-data" in combined.lower()
    assert "fetch_snapshot()" in disabled
    assert "ProviderUnavailableError" in disabled
    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
