from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

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

WRAPPER_FILES = [
    ROOT / "automation_scheduler" / "provider_contracts.py",
    ROOT / "automation_scheduler" / "provider_registry.py",
    ROOT / "automation_scheduler" / "provider_health.py",
    ROOT / "automation_scheduler" / "provider_adapter_base.py",
    ROOT / "automation_scheduler" / "provider_normalization_contract.py",
    ROOT / "automation_scheduler" / "provider_payload_validator.py",
    ROOT / "automation_scheduler" / "provider_secret_policy.py",
    ROOT / "automation_scheduler" / "provider_write_firewall.py",
    ROOT / "providers" / "base_provider.py",
    ROOT / "betting_providers" / "base.py",
    ROOT / "betting_providers" / "normalization.py",
]

DELETE_READY_WRAPPERS = [
    "automation_scheduler/provider_contracts.py",
    "automation_scheduler/provider_health.py",
    "automation_scheduler/provider_adapter_base.py",
    "automation_scheduler/provider_normalization_contract.py",
    "automation_scheduler/provider_payload_validator.py",
    "automation_scheduler/provider_secret_policy.py",
    "providers/base_provider.py",
    "betting_providers/base.py",
    "betting_providers/normalization.py",
]

RUNTIME_BLOCKERS = {
    "automation_scheduler/provider_registry.py",
    "automation_scheduler/provider_write_firewall.py",
}
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
}
TARGET_IMPORTS = {
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_registry",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_secret_policy",
    "automation_scheduler.provider_write_firewall",
    "providers.base_provider",
    "betting_providers.base",
    "betting_providers.normalization",
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


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


def _scan_for_targets() -> dict[str, set[str]]:
    hits: dict[str, set[str]] = {"runtime": set(), "tests": set(), "docs": set(), "wrappers": set()}
    wrapper_paths = {path.as_posix() for path in WRAPPER_FILES}
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in TARGET_IMPORTS:
                found = True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in TARGET_IMPORTS:
                        found = True
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "import_module" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and arg.value in TARGET_IMPORTS:
                        found = True
        if not found:
            continue
        path_posix = path.as_posix()
        if path_posix.startswith((ROOT / "tests").as_posix()):
            hits["tests"].add(path_posix)
        elif path.suffix == ".md":
            hits["docs"].add(path_posix)
        elif path_posix in wrapper_paths:
            hits["wrappers"].add(path_posix)
        else:
            hits["runtime"].add(path_posix)
    return hits


def test_phase10k8zg8_provider_foundation_deletion_proof(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {name: importlib.import_module(name) for name in CANONICAL_MODULES}
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

    for wrapper_path in WRAPPER_FILES:
        assert wrapper_path.is_file(), wrapper_path
        text = wrapper_path.read_text(encoding="utf-8")
        if wrapper_path.as_posix().endswith("provider_write_firewall.py"):
            assert "append_security_event" in text
            assert "evaluate_owner_approval" in text
            assert "locked_safety_flags" in text
        else:
            assert "src.providers" in text
        assert not ("requests" in text or "httpx" in text or "yfinance" in text)

    for runtime_blocker in RUNTIME_BLOCKERS:
        runtime_text = _read(runtime_blocker)
        assert runtime_text
        assert runtime_blocker in _read("PROVIDER_FOUNDATION_DELETE_READINESS_AFTER_10K8ZG8.md")

    scan = _scan_for_targets()
    assert not scan["runtime"], scan["runtime"]
    assert scan["tests"], "expected test-only compatibility references to remain documented"

    docs = [
        "PHASE10K8ZG8_PROVIDER_FOUNDATION_DELETION_PROOF.md",
        "PROVIDER_FOUNDATION_IMPORT_SCAN_AFTER_10K8ZG8.md",
        "PROVIDER_FOUNDATION_WRAPPER_STATUS_AFTER_10K8ZG8.md",
        "PROVIDER_FOUNDATION_DELETE_READINESS_AFTER_10K8ZG8.md",
        "NEXT_PROVIDER_FOUNDATION_DELETION_BATCH_AFTER_10K8ZG8.md",
    ]
    for doc in docs:
        text = _read(doc)
        assert "No deletion occurs in this phase" in text

    proof = _read("PHASE10K8ZG8_PROVIDER_FOUNDATION_DELETION_PROOF.md")
    assert "Provider foundation wrapper deletion is not performed in this phase." in proof
    assert "src.providers" in proof
    assert "Delete-ready Files" in proof or "Delete-Ready Files" in proof or "Delete-ready files" in proof
    assert "Remaining Blockers" in proof
    assert "automation_scheduler/provider_registry.py" in proof
    assert "automation_scheduler/provider_write_firewall.py" in proof
    assert "providers/base_provider.py" in proof

    import_scan = _read("PROVIDER_FOUNDATION_IMPORT_SCAN_AFTER_10K8ZG8.md")
    assert "tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py" in import_scan
    assert "betting_providers.normalization" in import_scan

    wrapper_status = _read("PROVIDER_FOUNDATION_WRAPPER_STATUS_AFTER_10K8ZG8.md")
    for path in DELETE_READY_WRAPPERS:
        assert path in wrapper_status
    for blocker in RUNTIME_BLOCKERS:
        assert blocker in wrapper_status

    readiness = _read("PROVIDER_FOUNDATION_DELETE_READINESS_AFTER_10K8ZG8.md")
    assert "Delete-ready" in readiness
    for blocker in RUNTIME_BLOCKERS:
        assert blocker in readiness

    next_batch = _read("NEXT_PROVIDER_FOUNDATION_DELETION_BATCH_AFTER_10K8ZG8.md")
    assert "Delete the thin compatibility wrappers" in next_batch
    assert "automation_scheduler/provider_registry.py" in next_batch
    assert "automation_scheduler/provider_write_firewall.py" in next_batch
