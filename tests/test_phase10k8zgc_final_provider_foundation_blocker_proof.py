from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

REPORT_PATH = ROOT / "PHASE10K8ZGC_FINAL_PROVIDER_FOUNDATION_BLOCKER_PROOF.md"
IMPORT_SCAN_PATH = ROOT / "FINAL_PROVIDER_FOUNDATION_IMPORT_SCAN_AFTER_10K8ZGC.md"
TEST_REDIRECTION_PATH = ROOT / "FINAL_PROVIDER_FOUNDATION_TEST_REDIRECTION_AFTER_10K8ZGC.md"
DELETE_READINESS_PATH = ROOT / "FINAL_PROVIDER_FOUNDATION_DELETE_READINESS_AFTER_10K8ZGC.md"

TARGET_MODULES = {
    'src.automation_scheduler_legacy.provider_registry',
    'src.automation_scheduler_legacy.provider_write_firewall',
}

ALLOWED_TEST_TEXT_REFERENCES = {
    "tests/test_phase10k8zga_provider_registry_runtime_blocker.py",
    "tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py",
    "tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py",
    "tests/test_phase10k8zg8_provider_foundation_deletion_proof.py",
    "tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py",
}

ALL_PY_PATHS = [
    path
    for path in ROOT.rglob("*.py")
    if "__pycache__" not in path.parts
]


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


def _uses_target_module(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in TARGET_MODULES:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in TARGET_MODULES:
                    return True
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "import_module" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and first.value in TARGET_MODULES:
                    return True
    return False


def test_phase10k8zgc_docs_exist_and_cover_required_strings():
    for path in (REPORT_PATH, IMPORT_SCAN_PATH, TEST_REDIRECTION_PATH, DELETE_READINESS_PATH):
        assert path.is_file(), path

    report = _read(REPORT_PATH)
    import_scan = _read(IMPORT_SCAN_PATH)
    test_redirection = _read(TEST_REDIRECTION_PATH)
    delete_readiness = _read(DELETE_READINESS_PATH)

    for text in (report, import_scan, test_redirection, delete_readiness):
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    required_phrases = [
        "PHASE10K8ZGC",
        "Final Provider Foundation Blocker Proof",
        "src.providers.registry",
        "src.providers.policy.write_firewall",
        "delete-ready",
        "compatibility shims",
        "runtime imports",
        "test imports",
        "compatibility proof",
        "full local gate proof",
        "Final provider foundation blocker deletion is authorized only after runtime imports, test imports, compatibility proof, and full local gate proof are clean.",
    ]
    for phrase in required_phrases:
        assert phrase in report or phrase in delete_readiness or phrase in import_scan or phrase in test_redirection

    required_sections = [
        "Executive Summary",
        "Big Picture Architecture",
        "Imports / References Before Redirection",
        "Tests Redirected",
        "Remaining References After Redirection",
        "Delete-Readiness Decision",
        "Why Deletion Did or Did Not Occur",
        "Next Recommended Deletion Phase",
        "Runtime Import Scan",
        "Compatibility Evidence",
        "Scan Result",
        "Tests Still Documenting the Shims",
        "Remaining Test References",
        "Decision by File",
        "Why This Is Still a Proof Phase",
        "Acceptance Summary",
        "Required Statement",
    ]
    for section in required_sections:
        assert (
            section in report
            or section in import_scan
            or section in test_redirection
            or section in delete_readiness
        ), section

    assert "runtime import redirection is complete" in import_scan.lower()
    assert "no other tracked test file requires the final two legacy shim modules as a direct import dependency" in test_redirection.lower()
    assert "delete-ready" in delete_readiness.lower()


def test_phase10k8zgc_runtime_and_test_redirect(monkeypatch, tmp_path):
    original_getenv = os.getenv

    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    canonical_registry = importlib.import_module("src.providers.registry")
    canonical_firewall = importlib.import_module("src.providers.policy.write_firewall")
    scheduler_pkg = importlib.import_module('src.automation_scheduler_legacy')
    execution_authorization = importlib.import_module("src.brokerage.readiness")

    monkeypatch.setattr(os, "getenv", original_getenv)
    monkeypatch.setattr(canonical_registry.os, "getenv", lambda *_args, **_kwargs: None)

    assert not (ROOT / "automation_scheduler" / "provider_registry.py").exists()
    assert not (ROOT / "automation_scheduler" / "provider_write_firewall.py").exists()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('src.automation_scheduler_legacy.provider_registry')
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('src.automation_scheduler_legacy.provider_write_firewall')

    canonical_registry_snapshot = canonical_registry.get_provider_registry(include_legacy_aliases=True)
    scheduler_snapshot = scheduler_pkg.get_provider_registry_snapshot(base_data_dir=str(tmp_path))
    assert scheduler_snapshot["provider_count"] == len(canonical_registry_snapshot)
    scheduler_provider_ids = {item["provider_id"] for item in scheduler_snapshot["providers"]}
    for provider_id in ("sharp_sportsbook", "kalshi_prediction_market"):
        assert provider_id in scheduler_provider_ids

    payload = {
        "provider": "paper",
        "action": "review_only",
        "asset_type": "stock",
        "market_type": "equity",
    }
    canonical_result = canonical_firewall.check_provider_write_attempt(
        provider="paper",
        action="review_only",
        request_payload=payload,
        persist_audit=False,
    )
    scheduler_result = scheduler_pkg.check_provider_write_firewall(
        provider="paper",
        action="review_only",
        request_payload=payload,
        base_data_dir=str(tmp_path),
        persist_audit=False,
    )
    assert scheduler_result == canonical_result

    execution_result = execution_authorization.evaluate_execution_authorization(
        payload,
        base_data_dir=str(tmp_path),
        persist_audit=False,
    )
    assert execution_result["provider_write_firewall_status"] == canonical_result["status"]
    assert execution_result["status"] == "execution_attempt_blocked"
    assert execution_result["ok"] is False

    scan_hits = {"runtime": set(), "tests": set()}
    for path in ALL_PY_PATHS:
        text = _read(path)
        relative = path.relative_to(ROOT).as_posix()
        if _uses_target_module(path):
            if relative.startswith("tests/"):
                scan_hits["tests"].add(relative)
            else:
                scan_hits["runtime"].add(relative)
        if relative.startswith("tests/"):
            if "automation_scheduler.provider_registry" in text or "automation_scheduler.provider_write_firewall" in text:
                assert relative in ALLOWED_TEST_TEXT_REFERENCES, relative
        else:
            assert "automation_scheduler.provider_registry" not in text
            assert "automation_scheduler.provider_write_firewall" not in text

    assert not scan_hits["runtime"], scan_hits["runtime"]
    assert scan_hits["tests"] <= ALLOWED_TEST_TEXT_REFERENCES
