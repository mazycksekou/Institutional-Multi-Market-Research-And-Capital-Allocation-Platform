from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _roots_from_tree(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_phase10k8zg5_provider_router_independence():
    docs = [
        "PHASE10K8ZG5_CANONICAL_PROVIDER_ROUTER_INDEPENDENCE.md",
        "PROVIDER_ROUTER_INDEPENDENCE_MAP_AFTER_10K8ZG5.md",
        "LEGACY_PROVIDER_ROUTER_COMPATIBILITY_AFTER_10K8ZG5.md",
        "PROVIDER_ROUTER_DELETION_READINESS_AFTER_10K8ZG5.md",
    ]
    required_statement = (
        "src.providers.provider_router is the canonical provider router owner after this phase. "
        "Legacy provider routers remain only for compatibility and are not deleted in this phase."
    )
    for doc in docs:
        text = _read(doc)
        assert "No deletion occurs in this phase." in text
    assert required_statement in _read("PHASE10K8ZG5_CANONICAL_PROVIDER_ROUTER_INDEPENDENCE.md")

    bridge_text = _read("src/providers/provider_router.py")
    assert "betting_providers.provider_router" not in bridge_text
    assert "providers.odds_provider_router" not in bridge_text

    bridge_roots = _roots_from_tree(ROOT / "src/providers/provider_router.py")
    forbidden = {"requests", "httpx", "yfinance", "selenium", "playwright", "websocket", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"}
    assert "betting_providers" not in bridge_roots
    assert "providers" not in bridge_roots
    assert not (bridge_roots & forbidden)

    original_getenv = os.getenv
    try:
        def forbidden_getenv(*_args, **_kwargs):
            raise AssertionError("import-time credential access is forbidden")

        os.getenv = forbidden_getenv  # type: ignore[assignment]
        module = importlib.import_module("src.providers.provider_router")
        assert hasattr(module, "ProviderRouter")
        assert hasattr(module, "provider_category")
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]

    module = importlib.import_module("src.providers.provider_router")
    router = module.ProviderRouter()
    assert module.provider_category("kalshi") == "prediction_markets"
    assert module.provider_category("sharp_api") == "sportsbooks"
    assert router.available_provider_ids == ["the_odds_api", "sportsgameodds", "sharp_api", "kalshi"]
    assert router.default_betting_provider() == "the_odds_api"
    assert router.default_market_provider() == "kalshi"
    assert hasattr(router, "get_prediction_market_events")
    assert hasattr(router, "get_prediction_market_markets")
    assert hasattr(router, "get_prediction_market_orderbook")
    assert not hasattr(router, "get_kalshi_events")

    provider, error = router.get_provider("the_odds_api", "sportsbook_odds")
    assert error is None
    assert provider is not None
    assert provider.provider_type == "sportsbook_odds"

    legacy_router = importlib.import_module("betting_providers.provider_router")
    assert hasattr(legacy_router, "ProviderRouter")
    assert hasattr(legacy_router, "provider_category")
    legacy_instance = legacy_router.ProviderRouter()
    assert legacy_instance.available_provider_ids == router.available_provider_ids
    assert legacy_router.provider_category("kalshi") == "prediction_markets"
    assert legacy_router.provider_category("sharp_api") == "sportsbooks"
    assert hasattr(legacy_instance, "get_kalshi_events")
    assert hasattr(legacy_instance, "get_kalshi_markets")
    assert hasattr(legacy_instance, "get_kalshi_orderbook")

    odds_router = importlib.import_module("providers.odds_provider_router")
    assert hasattr(odds_router, "enrich_ticket")

    main_text = _read("main.py")
    model_card_text = _read("src/api/model_card_service.py")
    assert "from src.providers.provider_router import ProviderRouter" in main_text
    assert "from src.providers.provider_router import ProviderRouter" in model_card_text
    assert "from betting_providers.provider_router import ProviderRouter" not in main_text
    assert "from betting_providers.provider_router import ProviderRouter" not in model_card_text

    provider_router_tests = [
        "tests/test_phase10k8zg4_runtime_bridge_import_redirection.py",
        "tests/test_phase10k8zg3_wrapper_import_redirection.py",
        "tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py",
    ]
    for path in provider_router_tests:
        assert (ROOT / path).exists(), path
