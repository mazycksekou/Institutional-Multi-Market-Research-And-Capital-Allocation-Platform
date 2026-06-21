from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _legacy_target_hits(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in {"betting_providers.provider_router", "providers.odds_provider_router"}:
            hits.add(f"importfrom:{node.module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"betting_providers.provider_router", "providers.odds_provider_router"}:
                    hits.add(f"import:{alias.name}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "patch" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and arg.value in {
                    "betting_providers.provider_router",
                    "providers.odds_provider_router",
                }:
                    hits.add(f"patch:{arg.value}")
            if isinstance(func, ast.Attribute) and func.attr == "import_module" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and arg.value in {
                    "betting_providers.provider_router",
                    "providers.odds_provider_router",
                }:
                    hits.add(f"import_module:{arg.value}")
    return hits


def test_phase10k8zg6_legacy_provider_router_delete_proof(monkeypatch):
    docs = [
        "PHASE10K8ZG6_LEGACY_PROVIDER_ROUTER_DELETE_PROOF.md",
        "LEGACY_PROVIDER_ROUTER_IMPORT_SCAN_AFTER_10K8ZG6.md",
        "PROVIDER_ROUTER_COMPATIBILITY_HOOK_STATUS_AFTER_10K8ZG6.md",
        "PROVIDER_ROUTER_DELETE_READINESS_AFTER_10K8ZG6.md",
    ]
    required_statement = "Legacy provider router deletion is allowed only after import proof, compatibility proof, and full test proof. This phase prioritizes proof over deletion."
    for doc in docs:
        text = _read(doc)
        assert "No deletion occurs in this phase." in text
    assert required_statement in _read("PHASE10K8ZG6_LEGACY_PROVIDER_ROUTER_DELETE_PROOF.md")

    canonical_router_text = _read("src/providers/provider_router.py")
    assert "betting_providers.provider_router" not in canonical_router_text
    assert "providers.odds_provider_router" not in canonical_router_text

    main_text = _read("main.py")
    model_card_text = _read("src/api/model_card_service.py")
    market_routes_text = _read("src/api/market_metadata_routes.py")
    screenshot_text = _read("screenshot_intake.py")
    for text in (main_text, model_card_text, market_routes_text, screenshot_text):
        assert "from betting_providers.provider_router import ProviderRouter" not in text
        assert "from providers.odds_provider_router import enrich_ticket" not in text

    assert (ROOT / "betting_providers" / "provider_router.py").is_file()
    assert (ROOT / "providers" / "odds_provider_router.py").is_file()

    original_getenv = os.getenv
    try:
        def forbidden_getenv(*_args, **_kwargs):
            raise AssertionError("import-time credential access is forbidden")

        os.getenv = forbidden_getenv  # type: ignore[assignment]
        module = importlib.import_module("src.providers.provider_router")
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]

    assert hasattr(module, "ProviderRouter")
    assert hasattr(module, "provider_category")
    original_getenv = os.getenv
    try:
        os.getenv = lambda *_args, **_kwargs: ""  # type: ignore[assignment]
        router = module.ProviderRouter()
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]
    assert hasattr(router, "get_prediction_market_events")
    assert hasattr(router, "get_prediction_market_markets")
    assert hasattr(router, "get_prediction_market_orderbook")
    assert not hasattr(router, "get_kalshi_events")

    target_hits = set()
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if path.name == "test_phase10k8zg6_legacy_provider_router_delete_proof.py":
            continue
        target_hits |= _legacy_target_hits(path)
    assert not target_hits, target_hits

    blockers = _read("PROVIDER_ROUTER_DELETE_READINESS_AFTER_10K8ZG6.md")
    assert "betting_providers.provider_router" in blockers
    assert "providers.odds_provider_router" in blockers
    assert "delete-ready" in blockers.lower()
