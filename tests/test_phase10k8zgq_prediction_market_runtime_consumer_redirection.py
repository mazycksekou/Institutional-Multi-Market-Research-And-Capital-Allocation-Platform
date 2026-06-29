from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    ROOT / "PHASE10K8ZGQ_PREDICTION_MARKET_RUNTIME_CONSUMER_REDIRECTION.md",
    ROOT / "PREDICTION_MARKET_RUNTIME_CONSUMER_REDIRECTION_MAP_AFTER_10K8ZGQ.md",
    ROOT / "PREDICTION_MARKET_RUNTIME_IMPORT_SCAN_AFTER_10K8ZGQ.md",
    ROOT / "PREDICTION_MARKET_RUNTIME_DELETE_READINESS_AFTER_10K8ZGQ.md",
]

CANONICAL_MODULES = [
    "src.connectors.prediction_market_data",
    "src.providers.prediction_markets",
    "src.services.prediction_market_runtime_bridge",
    "src.services.enrichment_service",
]

LEGACY_MODULES = [
    # Deleted in later phases; retained only as historical evidence in docs.
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


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _purge_modules(prefixes: list[str]) -> None:
    for name in list(sys.modules):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def test_prediction_market_runtime_consumer_redirection_is_canonical_and_disabled(monkeypatch):
    for path in DOCS:
        assert path.is_file(), path

    combined = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for required in [
        "10K8ZGQ",
        "Prediction-market runtime consumers are redirected away from legacy prediction-market shells in this phase. This phase does not authorize live API calls, credential reads, trade execution, connector activation, or deletion.",
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "No-Network Guarantee",
        "No-Credential Guarantee",
        "No-Execution Guarantee",
        "Next Recommended Phase",
        "Prediction-Market Legacy Live-Method Retirement Proof",
    ]:
        assert required in combined

    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("credential access at import time is forbidden")),
    )

    _purge_modules([
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "src.services.prediction_market_runtime_bridge",
        "src.services.enrichment_service",
    ])

    for module_name in CANONICAL_MODULES:
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

    service_path = ROOT / "src" / "services" / "enrichment_service.py"
    bridge_path = ROOT / "src" / "services" / "prediction_market_runtime_bridge.py"
    service_text = service_path.read_text(encoding="utf-8")
    bridge_text = bridge_path.read_text(encoding="utf-8")

    assert "from providers.kalshi_provider import enrich_with_kalshi" not in service_text
    assert "from src.services.prediction_market_runtime_bridge import enrich_with_kalshi" in service_text
    assert "providers.kalshi_provider" not in bridge_text
    assert "requests" not in bridge_text
    assert "httpx" not in bridge_text
    assert "os.getenv" not in bridge_text

    bridge_roots = _import_roots(bridge_path)
    assert not (bridge_roots & FORBIDDEN_DIRECT_IMPORTS)
    assert "providers" not in bridge_roots
    assert "betting_providers" not in bridge_roots
    assert "automation_scheduler" not in bridge_roots

    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: "")

    enrichment_service = importlib.import_module("src.services.enrichment_service")
    result = enrichment_service.EnrichmentService.enrich_ticket(
        {
            "sport": "nba",
            "league": "nba",
            "event": "demo-event",
            "market": "moneyline",
            "selection": "home",
            "odds_american": -110,
        }
    )

    assert "kalshi" in result
    kalshi = result["kalshi"]
    assert kalshi["provider"] == "kalshi"
    assert kalshi["canonical_provider"] == "prediction_market"
    assert kalshi["provider_status"] == "unavailable"
    assert kalshi["reason"] == "prediction_market_connector_boundary_disabled"
    assert kalshi["connector_readiness"]["status"] == "disabled"
    assert kalshi["provider_health"]["status"] == "scaffold_only"
    assert kalshi["provider_health"]["provider_id"] == "prediction_market_placeholder"
    assert kalshi["connector_configuration"]["provider"] == "prediction_market_data"
    assert kalshi["disabled_client"]["live_access_enabled"] is False

    canonical_scan_targets = [
        ROOT / "src" / "connectors" / "prediction_market_data",
        ROOT / "src" / "providers" / "prediction_markets",
        ROOT / "src" / "services",
    ]
    for target in canonical_scan_targets:
        for py_file in target.rglob("*.py"):
            roots = _import_roots(py_file)
            assert not (roots & FORBIDDEN_DIRECT_IMPORTS), f"forbidden import in {py_file}: {roots & FORBIDDEN_DIRECT_IMPORTS}"
            assert "providers.kalshi_provider" not in py_file.read_text(encoding="utf-8")


def test_deleted_prediction_market_legacy_modules_stay_deleted() -> None:
    deleted_modules = [
        "providers.kalshi_provider",
        "betting_providers.kalshi_api",
        'src.automation_scheduler_legacy.kalshi_readonly_adapter',
        'src.automation_scheduler_legacy.kalshi_market_provider',
        "kalshi_client",
    ]

    for module_name in deleted_modules:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)
