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

    for module_name in CANONICAL_MODULES:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name

    bridge = importlib.import_module("src.services.prediction_market_runtime_bridge")

    assert hasattr(bridge, "enrich_with_kalshi")

    ticket = {
        "sport": "nba",
        "league": "nba",
        "event": "demo-event",
        "market": "moneyline",
        "selection": "home",
        "odds_american": -110,
    }
    provider_result = bridge.enrich_with_kalshi(ticket)
    assert provider_result["provider_status"] == "unavailable"
    assert provider_result["canonical_provider"] == "prediction_market"
    assert provider_result["connector_readiness"]["status"] == "disabled"

    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        assert "kalshi_client.py" in text or "Kalshi" in text
