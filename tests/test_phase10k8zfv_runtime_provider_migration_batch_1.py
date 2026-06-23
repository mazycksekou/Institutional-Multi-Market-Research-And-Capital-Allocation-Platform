from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZFV_RUNTIME_PROVIDER_MIGRATION_BATCH_1.md"
MIGRATION_MAP_PATH = ROOT / "PROVIDER_RUNTIME_MIGRATION_MAP_AFTER_10K8ZFV.md"
REDIRECTS_PATH = ROOT / "PROVIDER_LEGACY_IMPORT_REDIRECTS_AFTER_10K8ZFV.md"

CANONICAL_MODULES = [
    "src.providers",
    "src.providers.prediction_markets",
    "src.providers.prediction_markets.adapters",
    "src.providers.prediction_markets.models",
    "src.providers.sportsbooks",
    "src.providers.sportsbooks.adapters",
    "src.providers.sportsbooks.models",
    "src.providers.zero_dte_stocks",
    "src.providers.zero_dte_stocks.adapters",
    "src.providers.zero_dte_stocks.models",
]

FORBIDDEN_IMPORT_PREFIXES = ("automation_scheduler", "betting_providers", "providers")
FORBIDDEN_DIRECT_IMPORTS = {"requests", "httpx", "yfinance", "openai", "anthropic", "playwright", "selenium", "alpaca", "robinhood", "ib_insync", "ccxt"}


def _import_fresh(module_name: str):
    for key in list(sys.modules):
        if key == module_name or key.startswith(f"{module_name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(module_name)


def _module_path(module_name: str) -> Path:
    if module_name == "src.providers":
        return ROOT / "src" / "providers" / "__init__.py"
    parts = module_name.split(".")
    if module_name.startswith("src.providers."):
        relative = Path(*parts[2:-1]) if len(parts) > 3 else Path()
        if len(parts) == 3:
            return ROOT / "src" / "providers" / parts[-1] / "__init__.py"
        return ROOT / "src" / "providers" / relative / f"{parts[-1]}.py"
    if module_name.startswith("providers."):
        return ROOT / "providers" / f"{parts[-1]}.py"
    if module_name.startswith("betting_providers."):
        return ROOT / "betting_providers" / f"{parts[-1]}.py"
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


def test_runtime_category_adapters_import_and_preserve_compatibility(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {module_name: _import_fresh(module_name) for module_name in CANONICAL_MODULES}

    # Canonical adapter/model imports.
    pm_adapters = imported["src.providers.prediction_markets.adapters"]
    sb_adapters = imported["src.providers.sportsbooks.adapters"]
    stock_adapters = imported["src.providers.zero_dte_stocks.adapters"]
    assert hasattr(pm_adapters, "PredictionMarketProviderAdapter")
    assert hasattr(pm_adapters, "PredictionMarketQuote")
    assert hasattr(sb_adapters, "SportsbookProviderAdapter")
    assert hasattr(sb_adapters, "SportsbookQuote")
    assert hasattr(stock_adapters, "ZeroDteStockProviderAdapter")
    assert hasattr(stock_adapters, "ZeroDteStockQuote")

    canonical_pm = pm_adapters.normalize_prediction_market_quote(
        {
            "ticker": "KXTEST",
            "yes_bid": 48,
            "yes_ask": 52,
            "no_bid": 47,
            "no_ask": 53,
            "liquidity": 1000,
            "volume": 250,
        },
        provider="prediction_market",
        market_type="prediction_market",
    )
    provider_namespace = imported["src.providers.prediction_markets"]
    namespace_pm = provider_namespace.normalize_prediction_market_quote(
        {
            "ticker": "KXTEST",
            "yes_bid": 48,
            "yes_ask": 52,
            "no_bid": 47,
            "no_ask": 53,
            "liquidity": 1000,
            "volume": 250,
        }
    )
    assert namespace_pm == canonical_pm

    canonical_kalshi_snapshot = pm_adapters.normalize_prediction_market_snapshot(
        {
            "ticker": "KXTEST",
            "market_ticker": "KXTEST",
            "yes_bid": 48,
            "yes_ask": 52,
            "no_bid": 47,
            "no_ask": 53,
            "last_price": 51,
            "volume": 250,
            "liquidity": 1000,
            "close_time": "2026-06-20T00:00:00+00:00",
            "subtitle": "demo",
            "status": "open",
        },
        provider="kalshi",
        market_type="kalshi_prediction_market",
    )
    assert canonical_kalshi_snapshot["provider_type"] == "prediction_market"

    sportsbook_event = {
        "id": "evt-1",
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "commence_time": "2026-06-20T00:00:00+00:00",
        "home_team": "A",
        "away_team": "B",
    }
    sportsbook_odds = {
        "event_id": "evt-1",
        "market": "h2h",
        "sportsbook": "demo",
        "selection": "A",
        "price_american": -110,
        "point": None,
        "last_update": "2026-06-20T00:00:00+00:00",
        "raw": {"event_id": "evt-1"},
    }
    assert sb_adapters.normalize_sportsbook_event("demo", sportsbook_event, league="NBA") == sb_adapters.normalize_sportsbook_event("demo", sportsbook_event, league="NBA")
    assert sb_adapters.normalize_sportsbook_odds(
        "demo",
        "evt-1",
        "basketball_nba",
        "h2h",
        "demo",
        "A",
        -110,
        None,
        "2026-06-20T00:00:00+00:00",
        {"event_id": "evt-1"},
    ) == sb_adapters.normalize_sportsbook_odds(
        "demo",
        "evt-1",
        "basketball_nba",
        "h2h",
        "demo",
        "A",
        -110,
        None,
        "2026-06-20T00:00:00+00:00",
        {"event_id": "evt-1"},
    )

    stock_adapter = stock_adapters.ZeroDteStockProviderAdapter()
    stock_payload = {"symbol": "AAPL", "price": 190.0, "bid": 189.9, "ask": 190.1, "volume": 100000, "timestamp": "2026-06-20T00:00:00+00:00"}
    assert stock_adapter.normalize_payload(stock_payload)["symbol"] == "AAPL"
    assert stock_adapter.normalize_payload(stock_payload)["provider_type"] == "stock_price"

    for path in (REPORT_PATH, MIGRATION_MAP_PATH, REDIRECTS_PATH):
        assert path.is_file()


def test_canonical_provider_modules_are_import_safe_and_vendor_neutral():
    canonical_paths = [_module_path(module_name) for module_name in CANONICAL_MODULES]
    for path in canonical_paths:
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        assert "kalshi" not in lower
        assert "sharp" not in lower
        for forbidden in FORBIDDEN_DIRECT_IMPORTS:
            assert forbidden not in text
        names = _import_names(path)
        for name in names:
            assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES)
            assert name not in FORBIDDEN_DIRECT_IMPORTS


def test_phase_docs_and_no_frontend_pages():
    report = REPORT_PATH.read_text(encoding="utf-8")
    migration_map = MIGRATION_MAP_PATH.read_text(encoding="utf-8")
    redirects = REDIRECTS_PATH.read_text(encoding="utf-8")

    for text in (report, migration_map, redirects):
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    for required in [
        "PHASE10K8ZFV",
        "Runtime provider migration has begun at the read-only adapter layer only.",
        "What Read-Only Means",
        "What Adapter-Level Means",
        "Compatibility Wrappers Preserved",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "No-Execution Guarantee",
        "Next Recommended Phase",
    ]:
        assert required in report

    for required in [
        "providers/kalshi_provider.py",
        "betting_providers/normalization.py",
        "src/providers/prediction_markets/adapters.py",
        "src/providers/sportsbooks/adapters.py",
        "src/providers/zero_dte_stocks/adapters.py",
    ]:
        assert required in migration_map or required in redirects

    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
