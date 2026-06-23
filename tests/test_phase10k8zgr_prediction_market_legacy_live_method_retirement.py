from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGR_PREDICTION_MARKET_LEGACY_LIVE_METHOD_RETIREMENT.md",
    ROOT / "PREDICTION_MARKET_LEGACY_LIVE_METHOD_RETIREMENT_MAP_AFTER_10K8ZGR.md",
    ROOT / "PREDICTION_MARKET_DISABLED_METHOD_BEHAVIOR_AFTER_10K8ZGR.md",
    ROOT / "PREDICTION_MARKET_DELETE_READINESS_AFTER_10K8ZGR.md",
]

LEGACY_MODULES = [
    "kalshi_client",
    "providers.kalshi_provider",
    "betting_providers.kalshi_api",
    "automation_scheduler.kalshi_readonly_adapter",
    "automation_scheduler.kalshi_market_provider",
]

CANONICAL_MODULES = [
    "src.connectors.prediction_market_data",
    "src.providers.prediction_markets",
    "src.services.prediction_market_runtime_bridge",
]


def _roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_prediction_market_legacy_live_method_retirement(monkeypatch: pytest.MonkeyPatch) -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for required in [
        "10K8ZGR",
        "Prediction-market live-method migration is connector-owned but disabled in this phase.",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "No-Execution Guarantee",
        "ConnectorDisabledError",
        "Next Recommended Phase",
    ]:
        assert required in combined

    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    for module_name in CANONICAL_MODULES + LEGACY_MODULES:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name

    client = importlib.import_module("kalshi_client")
    provider = importlib.import_module("providers.kalshi_provider")
    adapter_module = importlib.import_module("betting_providers.kalshi_api")
    readonly_adapter_module = importlib.import_module("automation_scheduler.kalshi_readonly_adapter")
    market_provider = importlib.import_module("automation_scheduler.kalshi_market_provider")
    bridge = importlib.import_module("src.services.prediction_market_runtime_bridge")

    assert hasattr(client, "describe_kalshi_client")
    assert hasattr(provider, "normalize_kalshi_probability_market")
    assert hasattr(provider, "enrich_with_kalshi")
    assert hasattr(adapter_module, "KalshiApiAdapter")
    assert hasattr(readonly_adapter_module, "KalshiReadonlyAdapter")
    assert hasattr(market_provider, "get_kalshi_snapshot")
    assert hasattr(bridge, "enrich_with_kalshi")

    with pytest.raises(ConnectorDisabledError):
        client.get_kalshi_market("KX1")
    with pytest.raises(ConnectorDisabledError):
        client.get_kalshi_orderbook("KX1")
    with pytest.raises(ConnectorDisabledError):
        client.get_kalshi_market_snapshot("KX1")

    api_adapter = adapter_module.KalshiApiAdapter()
    assert api_adapter.capability()["supports_prediction_markets"] is True
    with pytest.raises(ConnectorDisabledError):
        import asyncio
        asyncio.run(api_adapter.get_markets())

    readonly_adapter = readonly_adapter_module.KalshiReadonlyAdapter({})
    assert readonly_adapter.get_capabilities()["supports_prediction_markets"] is True
    with pytest.raises(ConnectorDisabledError):
        readonly_adapter.fetch_snapshot()

    disabled_snapshot = market_provider.get_kalshi_snapshot(readonly_adapter)
    assert disabled_snapshot["status"] == "provider_disabled"
    assert disabled_snapshot["connector_readiness"]["status"] == "disabled"
    assert disabled_snapshot["provider_name"] == "Kalshi Prediction Market"

    ticket = {
        "sport": "nba",
        "league": "nba",
        "event": "demo-event",
        "market": "moneyline",
        "selection": "home",
        "odds_american": -110,
    }
    provider_result = provider.enrich_with_kalshi(ticket)
    assert provider_result["provider_status"] == "unavailable"
    assert provider_result["canonical_provider"] == "prediction_market"
    assert provider_result["connector_readiness"]["status"] == "disabled"

    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        assert "kalshi_client.py" in text or "Kalshi" in text

    for py_file in [
        ROOT / "kalshi_client.py",
        ROOT / "providers" / "kalshi_provider.py",
        ROOT / "betting_providers" / "kalshi_api.py",
        ROOT / "automation_scheduler" / "kalshi_readonly_adapter.py",
        ROOT / "automation_scheduler" / "kalshi_market_provider.py",
    ]:
        roots = _roots(py_file)
        assert "requests" not in roots
        assert "httpx" not in roots
        assert "websocket" not in roots
        assert "yfinance" not in roots
        assert "selenium" not in roots
        assert "playwright" not in roots
