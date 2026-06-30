from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PACKAGE = "src.automation_scheduler_legacy"
DELETED_MODULE_NAMES = ("ai_provider_security", "hard_gate_policy", "security_readiness_report")
DELETED_MODULES = {f"{LEGACY_PACKAGE}.{name}" for name in DELETED_MODULE_NAMES}

pytestmark = pytest.mark.smoke


def _fresh_import(module_name: str):
    for name in (
        module_name,
        "src.security",
        "src.security.policy",
        "src.security.secret_safety",
        "src.security.ai_provider_security",
        "src.security.hard_gate_policy",
        "src.security.owner_approval_gate",
        "src.security.risk_limit_guard",
        "src.services.security_readiness",
    ):
        sys.modules.pop(name, None)
    return importlib.import_module(module_name)


def _legacy_import_refs() -> list[str]:
    refs: set[str] = set()
    excluded = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "node_modules", "build", "dist"}
    for path in ROOT.rglob("*.py"):
        if path == Path(__file__) or excluded.intersection(path.parts):
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
                if node.module in DELETED_MODULES:
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


def test_security_cluster_imports_are_canonical_and_import_safe() -> None:
    assert not (ROOT / "automation_scheduler").exists()
    for module_name in DELETED_MODULE_NAMES:
        assert not (ROOT / "src" / "automation_scheduler_legacy" / f"{module_name}.py").exists()

    before_modules = set(sys.modules)
    with patch("os.getenv", side_effect=AssertionError("import-time env access is not allowed")):
        ai_provider = _fresh_import("src.security.ai_provider_security")
        hard_gate = _fresh_import("src.security.hard_gate_policy")
        readiness = _fresh_import("src.services.security_readiness")

    with patch.dict(
        os.environ,
        {
            "DEEPSEEK_ENABLED": "true",
            "OPENAI_ANALYST_ENABLED": "false",
            "ALLOW_OPENAI_ANALYST": "false",
            "GLOBAL_EXECUTION_KILL_SWITCH": "true",
        },
        clear=True,
    ):
        ai_result = ai_provider.evaluate_ai_provider("deepseek", persist_audit=False)
        hard_result = hard_gate.evaluate_hard_gates({"provider": "internal_deterministic", "action": "strategy_readiness"}, persist_audit=False)
        readiness_result = readiness.build_security_readiness_report()

    assert ai_result["ok"] is True
    assert ai_result["status"] == "ai_provider_allowed"
    assert hard_result["ok"] is False
    assert hard_result["status"] == "execution_blocked_by_hard_gates"
    assert readiness_result["ok"] is True
    assert readiness_result["status"] == "security_readiness"

    imported_modules = set(sys.modules) - before_modules
    assert not any(
        name.startswith(("requests", "httpx", "urllib", "urllib3", "socket", "openai", "alpaca", "ib_insync"))
        for name in imported_modules
    )

    assert _legacy_import_refs() == []


def test_canonical_security_cluster_modules_load_without_network_or_credential_reads() -> None:
    with patch("os.getenv", side_effect=AssertionError("import-time env access is not allowed")):
        policy = _fresh_import("src.security.policy")
        secret_safety = _fresh_import("src.security.secret_safety")
        owner = _fresh_import("src.security.owner_approval_gate")
        risk = _fresh_import("src.security.risk_limit_guard")

    assert policy.locked_safety_flags()["dry_run"] is True
    assert secret_safety.redact_sensitive({"api_key": "sk-test12345678901234567890"})["api_key"] == "[redacted]"
    assert owner.OWNER_APPROVAL_MISSING == "owner_approval_missing"
    assert risk.RISK_LIMIT_BLOCKED == "risk_limit_blocked"
