from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REPORT_PATH = ROOT / "PHASE10K8ZGB_PROVIDER_WRITE_FIREWALL_RUNTIME_BLOCKER_PROOF.md"
IMPORT_SCAN_PATH = ROOT / "PROVIDER_WRITE_FIREWALL_IMPORT_SCAN_AFTER_10K8ZGB.md"
MIGRATION_MAP_PATH = ROOT / "PROVIDER_WRITE_FIREWALL_MIGRATION_MAP_AFTER_10K8ZGB.md"
DELETE_READINESS_PATH = ROOT / "PROVIDER_WRITE_FIREWALL_DELETE_READINESS_AFTER_10K8ZGB.md"

RUNTIME_FILES = [
    ROOT / "automation_scheduler" / "__init__.py",
    ROOT / "automation_scheduler" / "execution_authorization.py",
]

FORBIDDEN_NETWORK_ROOTS = {
    "requests",
    "httpx",
    "yfinance",
    "openai",
    "anthropic",
    "playwright",
    "selenium",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
    "websocket",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def _uses_legacy_firewall_import(text: str) -> bool:
    return (
        "from .provider_write_firewall import" in text
        or "from automation_scheduler.provider_write_firewall import" in text
        or "import automation_scheduler.provider_write_firewall" in text
    )


def test_phase10k8zgb_docs_exist_and_cover_required_strings():
    for path in (REPORT_PATH, IMPORT_SCAN_PATH, MIGRATION_MAP_PATH, DELETE_READINESS_PATH):
        assert path.is_file(), path

    report = _read(REPORT_PATH)
    import_scan = _read(IMPORT_SCAN_PATH)
    migration_map = _read(MIGRATION_MAP_PATH)
    delete_readiness = _read(DELETE_READINESS_PATH)

    for text in (report, import_scan, migration_map, delete_readiness):
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    required_report_strings = [
        "PHASE10K8ZGB",
        "provider_write_firewall",
        "src.providers.policy.write_firewall",
        "runtime blocker",
        "compatibility-only",
        "delete-ready",
        "No deletion occurs in this phase.",
        "automation_scheduler/provider_write_firewall.py",
    ]
    for required in required_report_strings:
        assert required in report

    assert "automation_scheduler.__init__" in import_scan
    assert "automation_scheduler.execution_authorization" in import_scan
    assert "legacy file remains only as a compatibility wrapper" in import_scan.lower()
    assert "compatibility-only" in migration_map.lower()
    assert "not yet delete-ready" in migration_map
    assert "compatibility-only" in delete_readiness
    assert "deferred" in delete_readiness.lower()


def test_phase10k8zgb_runtime_redirect_and_wrapper_compatibility(monkeypatch, tmp_path):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    canonical = importlib.import_module("src.providers.policy.write_firewall")
    scheduler_pkg = importlib.import_module("automation_scheduler")
    execution_authorization = importlib.import_module("automation_scheduler.execution_authorization")

    for path in RUNTIME_FILES:
        text = _read(path)
        assert not _uses_legacy_firewall_import(text), path
        assert "src.providers.policy.write_firewall" in text, path
        assert not any(token in text for token in ("requests", "httpx", "yfinance", "openai", "anthropic", "playwright", "selenium", "alpaca", "robinhood", "ib_insync", "ccxt"))

    for path in RUNTIME_FILES:
        roots = _import_roots(path)
        assert roots.isdisjoint(FORBIDDEN_NETWORK_ROOTS), (path, roots & FORBIDDEN_NETWORK_ROOTS)

    wrapper_text = _read(ROOT / "automation_scheduler" / "provider_write_firewall.py")
    assert "from src.providers.policy.write_firewall import" in wrapper_text
    assert "check_provider_write_attempt" in wrapper_text
    assert "append_security_event" not in wrapper_text
    assert "evaluate_owner_approval" not in wrapper_text
    assert "locked_safety_flags" not in wrapper_text

    sample = {
        "provider": "paper",
        "action": "review_only",
        "asset_type": "stock",
        "market_type": "equity",
    }
    canonical_result = canonical.check_provider_write_attempt(
        provider="paper",
        action="review_only",
        request_payload=sample,
        persist_audit=False,
    )
    wrapper_text = _read(ROOT / "automation_scheduler" / "provider_write_firewall.py")
    assert "from src.providers.policy.write_firewall import" in wrapper_text
    assert "check_provider_write_attempt" in wrapper_text
    assert "append_security_event" not in wrapper_text
    assert "evaluate_owner_approval" not in wrapper_text
    assert "locked_safety_flags" not in wrapper_text

    scheduler_result = scheduler_pkg.check_provider_write_firewall(
        provider="paper",
        action="review_only",
        request_payload=sample,
        base_data_dir=str(tmp_path),
        persist_audit=False,
    )
    assert scheduler_result == canonical_result

    monkeypatch.setattr(
        execution_authorization,
        "kill_switch_state",
        lambda: {"kill_switches_active": True, "switches": {"GLOBAL_EXECUTION_KILL_SWITCH": True}},
    )
    execution_result = execution_authorization.evaluate_execution_authorization(
        sample,
        base_data_dir=str(tmp_path),
        persist_audit=False,
    )
    assert execution_result["provider_write_firewall_status"] == canonical_result["status"]
    assert execution_result["status"] == "execution_attempt_blocked"
    assert execution_result["ok"] is False
