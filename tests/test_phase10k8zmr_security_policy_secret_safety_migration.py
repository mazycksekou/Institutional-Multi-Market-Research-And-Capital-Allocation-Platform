from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT / "src" / "automation_scheduler_legacy"
LEGACY_PACKAGE = "src.automation_scheduler_legacy"
DELETED_MODULE_NAMES = {"security_policy", "secret_safety"}
DELETED_MODULES = {f"{LEGACY_PACKAGE}.{name}" for name in DELETED_MODULE_NAMES}

pytestmark = pytest.mark.smoke


def _fresh_import(module_name: str):
    for name in (module_name, "src.security", "src.security.policy", "src.security.secret_safety"):
        sys.modules.pop(name, None)
    return importlib.import_module(module_name)


def _legacy_import_refs() -> list[str]:
    refs: set[str] = set()
    excluded = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "node_modules", "build", "dist"}
    for path in ROOT.rglob("*.py"):
        if path == Path(__file__):
            continue
        if excluded.intersection(path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except SyntaxError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in DELETED_MODULES:
                        refs.add(rel)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in DELETED_MODULES:
                    refs.add(rel)
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "import_module":
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in DELETED_MODULES:
                        refs.add(rel)
                elif isinstance(func, ast.Name) and func.id == "import_module":
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in DELETED_MODULES:
                        refs.add(rel)
    return sorted(refs)


def test_security_policy_and_secret_safety_are_canonical_and_deleted() -> None:
    assert not (ROOT / "automation_scheduler").exists()
    assert not (LEGACY_ROOT / "security_policy.py").exists()
    assert not (LEGACY_ROOT / "secret_safety.py").exists()

    before_modules = set(sys.modules)
    with patch("os.getenv", side_effect=AssertionError("import-time env access is not allowed")):
        policy = _fresh_import("src.security.policy")
        secret_safety = _fresh_import("src.security.secret_safety")
        security_pkg = _fresh_import("src.security")

    assert policy.locked_safety_flags()["dry_run"] is True
    assert policy.detect_execution_authority_violations({"live_execution_enabled": True})
    assert not policy.detect_execution_authority_violations({"recommended_action": "hold"})
    assert secret_safety.redact_sensitive({"api_key": "sk-test12345678901234567890"})["api_key"] == "[redacted]"
    assert secret_safety.secret_safety_fields(source_payload={"api_key": "sk-test12345678901234567890"})["redaction_applied"] is True
    assert hasattr(security_pkg, "locked_safety_flags")
    assert hasattr(security_pkg, "redact_sensitive")

    imported_modules = set(sys.modules) - before_modules
    assert not any(
        name.startswith(("requests", "httpx", "urllib", "socket", "openai", "alpaca", "ib_insync"))
        for name in imported_modules
    )

    assert _legacy_import_refs() == []

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(f"{LEGACY_PACKAGE}.security_policy")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(f"{LEGACY_PACKAGE}.secret_safety")
