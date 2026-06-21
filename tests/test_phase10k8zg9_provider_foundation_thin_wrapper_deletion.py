from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DELETED_FILES = [
    ROOT / "automation_scheduler" / "provider_contracts.py",
    ROOT / "automation_scheduler" / "provider_health.py",
    ROOT / "automation_scheduler" / "provider_adapter_base.py",
    ROOT / "automation_scheduler" / "provider_normalization_contract.py",
    ROOT / "automation_scheduler" / "provider_payload_validator.py",
    ROOT / "automation_scheduler" / "provider_secret_policy.py",
    ROOT / "providers" / "base_provider.py",
    ROOT / "betting_providers" / "base.py",
    ROOT / "betting_providers" / "normalization.py",
]

REMAINING_BLOCKERS = [
    ROOT / "automation_scheduler" / "provider_registry.py",
    ROOT / "automation_scheduler" / "provider_write_firewall.py",
]

CANONICAL_MODULES = [
    "src.providers.contracts",
    "src.providers.registry",
    "src.providers.health",
    "src.providers.base",
    "src.providers.normalization",
    "src.providers.validation",
    "src.providers.policy.allowlist",
    "src.providers.policy.secret_policy",
    "src.providers.policy.write_firewall",
    "src.providers.compat",
]

DELETED_IMPORT_TARGETS = {
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_secret_policy",
    "providers.base_provider",
    "betting_providers.base",
    "betting_providers.normalization",
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _scan_import_targets() -> dict[str, set[str]]:
    hits: dict[str, set[str]] = {"runtime": set(), "tests": set(), "docs": set()}
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts or path.name == Path(__file__).name:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in DELETED_IMPORT_TARGETS:
                found = True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in DELETED_IMPORT_TARGETS:
                        found = True
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "import_module" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and arg.value in DELETED_IMPORT_TARGETS:
                        found = True
        if not found:
            continue
        posix = path.as_posix()
        if posix.startswith((ROOT / "tests").as_posix()):
            hits["tests"].add(posix)
        elif path.suffix == ".md":
            hits["docs"].add(posix)
        else:
            hits["runtime"].add(posix)
    return hits


def test_phase10k8zg9_provider_foundation_thin_wrapper_deletion(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {module_name: importlib.import_module(module_name) for module_name in CANONICAL_MODULES}
    assert imported["src.providers.contracts"].ProviderContract.__name__ == "ProviderContract"
    assert imported["src.providers.registry"].ProviderRegistry.__name__ == "ProviderRegistry"
    assert imported["src.providers.health"].ProviderHealthStatus.__name__ == "ProviderHealthStatus"
    assert imported["src.providers.base"].ProviderAdapterBase.__name__ == "ProviderAdapterBase"
    assert imported["src.providers.normalization"].normalize_provider_payload("sportsbook_odds", {"event_id": "e1"})["provider_type"] == "sportsbook_odds"
    assert callable(imported["src.providers.validation"].validate_provider_payload)
    assert callable(imported["src.providers.policy.allowlist"].classify_provider)
    assert callable(imported["src.providers.policy.secret_policy"].redact_secret)
    assert callable(imported["src.providers.policy.write_firewall"].check_provider_write_attempt)
    assert hasattr(imported["src.providers.compat"], "provider_error")

    for deleted_path in DELETED_FILES:
        assert not deleted_path.exists(), deleted_path

    for blocker_path in REMAINING_BLOCKERS:
        assert blocker_path.is_file(), blocker_path

    scan = _scan_import_targets()
    assert not scan["runtime"], scan["runtime"]
    assert not scan["tests"], scan["tests"]

    docs = [
        "PHASE10K8ZG9_PROVIDER_FOUNDATION_THIN_WRAPPER_DELETION.md",
        "PROVIDER_FOUNDATION_THIN_WRAPPER_DELETION_PROOF_AFTER_10K8ZG9.md",
        "POST_PROVIDER_FOUNDATION_DELETION_IMPORT_SCAN_AFTER_10K8ZG9.md",
        "REMAINING_PROVIDER_FOUNDATION_BLOCKERS_AFTER_10K8ZG9.md",
    ]
    for doc in docs:
        text = _read(doc)
        assert "Only the 10K8ZG8 proof-backed provider foundation thin wrappers are deleted in this phase." in text
        assert "automation_scheduler/provider_registry.py" in text
        assert "automation_scheduler/provider_write_firewall.py" in text

    report = _read("PHASE10K8ZG9_PROVIDER_FOUNDATION_THIN_WRAPPER_DELETION.md")
    for phrase in [
        "Files Deleted",
        "Proof Source From 10K8ZG8",
        "Import Scan Before Deletion",
        "Import Scan After Deletion",
        "Tests Run",
        "Behavior Preserved",
        "Remaining Blockers",
        "Next Recommended Phase",
        "Only the 10K8ZG8 proof-backed provider foundation thin wrappers are deleted in this phase.",
    ]:
        assert phrase in report
