from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DELETED_PATHS = [
    ROOT / "src" / "automation_scheduler_legacy" / "provider_registry.py",
    ROOT / "src" / "automation_scheduler_legacy" / "provider_write_firewall.py",
]
TARGET_MODULES = {
    'src.automation_scheduler_legacy.provider_registry',
    'src.automation_scheduler_legacy.provider_write_firewall',
}
ALLOWED_TEST_REFERENCES = {
    "tests/test_phase10k8zga_provider_registry_runtime_blocker.py",
    "tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py",
    "tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py",
    "tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def test_phase10k8zgd_final_provider_foundation_blocker_deletion(monkeypatch, tmp_path):
    original_getenv = os.getenv

    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    canonical_registry = importlib.import_module("src.providers.registry")
    canonical_firewall = importlib.import_module("src.providers.policy.write_firewall")
    scheduler_pkg = importlib.import_module('src.services.streamlit_dashboard_facade')

    monkeypatch.setattr(os, "getenv", original_getenv)
    monkeypatch.setattr(canonical_registry.os, "getenv", lambda *_args, **_kwargs: None)

    for deleted_path in DELETED_PATHS:
        assert not deleted_path.exists(), deleted_path

    assert not (ROOT / "src" / "automation_scheduler_legacy" / "provider_registry.py").exists()
    assert not (ROOT / "src" / "automation_scheduler_legacy" / "provider_write_firewall.py").exists()

    canonical_snapshot = canonical_registry.get_provider_registry(include_legacy_aliases=True)
    scheduler_snapshot = scheduler_pkg.get_provider_registry_snapshot(base_data_dir=str(tmp_path))
    assert scheduler_snapshot["provider_count"] == len(canonical_snapshot)
    assert canonical_firewall.check_provider_write_attempt(
        provider="paper",
        action="review_only",
        request_payload={"provider": "paper", "action": "review_only", "asset_type": "stock", "market_type": "equity"},
        persist_audit=False,
    )["status"] == "provider_write_blocked"

    runtime_hits = set()
    test_hits = set()
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if _uses_target_module(path):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("tests/"):
                if relative in ALLOWED_TEST_REFERENCES:
                    test_hits.add(relative)
                else:
                    raise AssertionError(f"unexpected test reference to deleted shim: {relative}")
            else:
                runtime_hits.add(relative)
    assert not runtime_hits, runtime_hits
    assert test_hits <= ALLOWED_TEST_REFERENCES

    for doc_name in (
        "PHASE10K8ZGD_FINAL_PROVIDER_FOUNDATION_BLOCKER_DELETION.md",
        "FINAL_PROVIDER_FOUNDATION_BLOCKER_DELETION_PROOF_AFTER_10K8ZGD.md",
        "POST_FINAL_PROVIDER_FOUNDATION_DELETION_IMPORT_SCAN_AFTER_10K8ZGD.md",
        "PROVIDER_FOUNDATION_DELETION_COMPLETION_STATUS_AFTER_10K8ZGD.md",
    ):
        text = _read(ROOT / doc_name)
        assert "Only the final proof-backed provider foundation compatibility shims are deleted in this phase." in text
        assert "provider_registry" in text
        assert "provider_write_firewall" in text

