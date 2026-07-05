from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest


pytestmark = pytest.mark.smoke

ROOT = Path(__file__).resolve().parents[1]
DELETED_MODULES = {
    "src.automation_scheduler_legacy.provider_allowlist",
    "src.automation_scheduler_legacy.security_event_types",
    "src.automation_scheduler_legacy.owner_approval_gate",
    "src.automation_scheduler_legacy.risk_limit_guard",
}
DELETED_FILES = {
    ROOT / "src" / "automation_scheduler_legacy" / "provider_allowlist.py",
    ROOT / "src" / "automation_scheduler_legacy" / "security_event_types.py",
    ROOT / "src" / "automation_scheduler_legacy" / "owner_approval_gate.py",
    ROOT / "src" / "automation_scheduler_legacy" / "risk_limit_guard.py",
}


def _import_targets(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "import_module":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    targets.add(str(node.args[0].value))
            elif isinstance(func, ast.Name) and func.id == "import_module":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    targets.add(str(node.args[0].value))
    return targets


def _module_path(module_name: str) -> Path:
    return ROOT / Path(*module_name.split(".")).with_suffix(".py")


def test_canonical_provider_security_modules_import_without_env_access(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    from src.providers.policy import allowlist as canonical_allowlist
    from src.security import owner_approval_gate as canonical_owner
    from src.security import risk_limit_guard as canonical_risk

    assert canonical_allowlist.classify_provider("kalshi_prediction_market") == "kalshi_order"
    assert canonical_allowlist.classify_provider("sharp_sportsbook") == "sportsbook"
    allowlist_response = canonical_allowlist.provider_allowlist_response("internal_math")
    assert allowlist_response["ok"] is True
    assert allowlist_response["provider_class"] == "internal_deterministic"

    owner_result = canonical_owner.evaluate_owner_approval(None, persist_audit=False)
    assert owner_result["ok"] is False
    assert owner_result["status"] == "owner_approval_blocked"

    risk_result = canonical_risk.evaluate_risk_limits({}, persist_audit=False)
    assert risk_result["ok"] is False
    assert risk_result["status"] == "risk_limit_blocked"


def test_legacy_provider_security_wrappers_are_deleted_and_unreferenced():
    assert not (ROOT / "automation_scheduler").exists()
    for path in DELETED_FILES:
        assert not path.exists(), path

    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if path == Path(__file__):
            continue
        targets = _import_targets(path)
        for module_name in DELETED_MODULES:
            assert not any(
                target == module_name or target.startswith(f"{module_name}.")
                for target in targets
            ), f"{path} still imports {module_name}"


def test_canonical_provider_security_modules_do_not_import_network_packages():
    for module_name in ("src/providers/policy/allowlist.py", "src/security/owner_approval_gate.py", "src/security/risk_limit_guard.py"):
        targets = _import_targets(ROOT / module_name)
        assert "requests" not in targets
        assert "httpx" not in targets
        assert "openai" not in targets
        assert "anthropic" not in targets
        assert "playwright" not in targets
        assert "selenium" not in targets
        assert "alpaca" not in targets
        assert "robinhood" not in targets
        assert "ib_insync" not in targets
        assert "ccxt" not in targets

