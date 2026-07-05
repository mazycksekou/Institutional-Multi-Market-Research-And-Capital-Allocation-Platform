from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BROKERAGE_ROOT = ROOT / "src" / "brokerage"
FORBIDDEN_IMPORTS = {
    "requests",
    "httpx",
    "websocket",
    "selenium",
    "playwright",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}


def _clear_brokerage_modules() -> None:
    for name in list(sys.modules):
        if name == "src.brokerage" or name.startswith("src.brokerage."):
            sys.modules.pop(name, None)


def _fresh_import(module_name: str, monkeypatch: pytest.MonkeyPatch):
    _clear_brokerage_modules()
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("os.getenv must not be called at import time")),
    )
    return importlib.import_module(module_name)


def _module_name_from_path(path: Path) -> str:
    relative = path.relative_to(ROOT / "src")
    if path.name == "__init__.py":
        parts = ("src", *relative.parent.parts)
    else:
        parts = ("src", *relative.with_suffix("").parts)
    return ".".join(parts)


def test_credential_sdk_network_freeze(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _fresh_import("src.brokerage", monkeypatch)
    credential_readiness = importlib.import_module("src.brokerage.credential_readiness")

    scanned_modules: set[str] = set()
    for path in sorted(BROKERAGE_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert imports.isdisjoint(FORBIDDEN_IMPORTS), (path, imports & FORBIDDEN_IMPORTS)

        module_name = _module_name_from_path(path)
        if module_name not in scanned_modules:
            importlib.import_module(module_name)
            scanned_modules.add(module_name)

    assert root.build_disabled_credential_readiness(broker_name="sandbox-broker").ready is False
    assert credential_readiness.build_disabled_credential_readiness(broker_name="sandbox-broker").ready is False

    with pytest.raises(root.DisabledCredentialLoadError):
        root.load_credentials_disabled(
            root.ApprovalState(approval_id="approval_blocked", approved=False),
            root.build_default_kill_switch_state(),
            broker_name="sandbox-broker",
            required_credentials=("api_key", "api_secret"),
        )
