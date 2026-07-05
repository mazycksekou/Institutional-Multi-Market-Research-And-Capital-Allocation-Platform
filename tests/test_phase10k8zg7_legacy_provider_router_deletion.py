from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELETED_FILES = [
    ROOT / "betting_providers" / "provider_router.py",
    ROOT / "providers" / "odds_provider_router.py",
]
DELETE_TARGETS = {
    "betting_providers.provider_router",
    "providers.odds_provider_router",
}
FORBIDDEN_IMPORT_ROOTS = {
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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _legacy_target_hits(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in DELETE_TARGETS:
            hits.add(f"importfrom:{node.module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in DELETE_TARGETS:
                    hits.add(f"import:{alias.name}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "patch" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and arg.value in DELETE_TARGETS:
                    hits.add(f"patch:{arg.value}")
            if isinstance(func, ast.Attribute) and func.attr == "import_module" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and arg.value in DELETE_TARGETS:
                    hits.add(f"import_module:{arg.value}")
    return hits


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


def test_phase10k8zg7_legacy_provider_router_deletion():
    docs = [
        "PHASE10K8ZG7_LEGACY_PROVIDER_ROUTER_DELETION.md",
        "LEGACY_PROVIDER_ROUTER_DELETION_PROOF_AFTER_10K8ZG7.md",
        "POST_DELETION_IMPORT_SCAN_AFTER_10K8ZG7.md",
    ]
    required_statement = (
        "Only proof-backed legacy provider router compatibility hooks are deleted in this phase. "
        "No runtime provider owners, live clients, dashboard files, entrypoints, AI modules, "
        "brokerage modules, or connector scaffolds are deleted."
    )
    for doc in docs:
        text = _read(doc)
        lower_text = text.lower()
        assert "files deleted" in lower_text or "import scan summary" in lower_text
    assert required_statement in _read("PHASE10K8ZG7_LEGACY_PROVIDER_ROUTER_DELETION.md")

    for deleted_path in DELETED_FILES:
        assert not deleted_path.exists(), deleted_path

    main_text = _read("main.py")
    model_card_text = _read("src/api/model_card_service.py")
    assert "from src.providers.provider_router import ProviderRouter" in main_text
    assert "from src.providers.provider_router import ProviderRouter" in model_card_text
    assert "from betting_providers.provider_router import ProviderRouter" not in main_text
    assert "from betting_providers.provider_router import ProviderRouter" not in model_card_text

    canonical_router_text = _read("src/providers/provider_router.py")
    assert "betting_providers.provider_router" not in canonical_router_text
    assert "providers.odds_provider_router" not in canonical_router_text

    original_getenv = os.getenv
    try:
        os.getenv = lambda *_args, **_kwargs: ""  # type: ignore[assignment]
        module = importlib.import_module("src.providers.provider_router")
        router = module.ProviderRouter()
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]

    assert hasattr(module, "ProviderRouter")
    assert hasattr(module, "provider_category")
    assert hasattr(router, "get_prediction_market_events")
    assert hasattr(router, "get_prediction_market_markets")
    assert hasattr(router, "get_prediction_market_orderbook")
    assert not hasattr(router, "get_kalshi_events")

    target_hits = set()
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if path.name == "test_phase10k8zg7_legacy_provider_router_deletion.py":
            continue
        target_hits |= _legacy_target_hits(path)
    assert not target_hits, target_hits

    bridge_roots = _roots_from_tree(ROOT / "src/providers/provider_router.py")
    assert "betting_providers" not in bridge_roots
    assert "providers" not in bridge_roots
    assert not (bridge_roots & FORBIDDEN_IMPORT_ROOTS)
