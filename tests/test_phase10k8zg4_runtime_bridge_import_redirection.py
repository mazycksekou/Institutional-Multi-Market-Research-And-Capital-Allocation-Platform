from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase10k8zg4_runtime_bridge_import_redirection():
    docs = [
        "PHASE10K8ZG4_RUNTIME_BRIDGE_IMPORT_REDIRECTION.md",
        "RUNTIME_BRIDGE_REDIRECTION_MAP_AFTER_10K8ZG4.md",
        "WRAPPER_DELETION_PROOF_AFTER_10K8ZG4.md",
        "REMAINING_DELETION_BLOCKERS_AFTER_10K8ZG4.md",
    ]
    required_statement = "Runtime bridge imports are redirected in this phase, but legacy modules are not deleted. This phase produces deletion proof only."
    for doc in docs:
        text = _read(doc)
        assert required_statement in text
        assert "no deletion occurred" in text.lower() or "not deleted" in text.lower()

    main_text = _read("main.py")
    model_card_text = _read("src/api/model_card_service.py")
    bridge_text = _read("src/providers/provider_router.py")

    assert "from src.providers.provider_router import ProviderRouter" in main_text
    assert "from betting_providers.provider_router import ProviderRouter" not in main_text
    assert "from src.providers.provider_router import ProviderRouter" in model_card_text
    assert "from betting_providers.provider_router import ProviderRouter" not in model_card_text
    assert "betting_providers.provider_router" not in bridge_text

    bridge_path = ROOT / "src/providers/provider_router.py"
    tree = ast.parse(bridge_path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert "automation_scheduler" not in roots
    assert "betting_providers" not in roots
    assert "providers" not in roots
    forbidden = {"requests", "httpx", "yfinance", "selenium", "playwright", "websocket", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"}
    assert not (roots & forbidden)

    original_getenv = os.getenv
    try:
        def forbidden_getenv(*_args, **_kwargs):
            raise AssertionError("import-time credential access is forbidden")

        os.getenv = forbidden_getenv  # type: ignore[assignment]
        bridge = importlib.import_module("src.providers.provider_router")
        assert hasattr(bridge, "ProviderRouter")
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]

    assert (ROOT / "main.py").exists()
    assert (ROOT / "src/api/model_card_service.py").exists()

    blockers = _read("REMAINING_DELETION_BLOCKERS_AFTER_10K8ZG4.md")
    assert "src.providers.provider_router" in blockers
    assert "no deletion occurred" in blockers.lower() or "not deleted" in blockers.lower()
