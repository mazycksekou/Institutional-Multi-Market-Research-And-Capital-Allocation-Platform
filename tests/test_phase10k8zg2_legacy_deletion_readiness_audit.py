from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


DOCS = {
    "PHASE10K8ZG2_LEGACY_DELETION_READINESS_AUDIT.md": [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Method",
        "Canonical Ownership Snapshot",
        "Legacy Ownership Snapshot",
        "Retention / Shim Status",
        "Dependency Evidence",
        "Top 20 Retirement Blockers",
        "First 20 Delete Candidates",
        "Safest Deletion Batch",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
    "CANONICAL_OWNERSHIP_STATUS_AFTER_10K8ZG2.md": [
        "Executive Summary",
        "Canonical Owners",
        "Provider Ownership Estimate",
        "Connector Ownership Estimate",
        "Legacy Ownership Still Present",
        "Canonical Replacement Summary",
        "Compatibility and Deletion Status",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
    "LEGACY_SHIM_STATUS_AFTER_10K8ZG2.md": [
        "Executive Summary",
        "Shim-Only Files",
        "Legacy Runtime Owners",
        "Compatibility Wrappers Preserved",
        "Mixed Files",
        "Deletion Readiness",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
    "LEGACY_RUNTIME_DEPENDENCY_REPORT_AFTER_10K8ZG2.md": [
        "Executive Summary",
        "Search Methodology",
        "High-Signal Runtime Dependencies",
        "Legacy Runtime Modules That Still Own Behavior",
        "Dependency Hotspots",
        "Evidence Summary",
        "Blocking Conclusion",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
    "AUTOMATION_SCHEDULER_RETIREMENT_PROGRESS_AFTER_10K8ZG2.md": [
        "Executive Summary",
        "Current Scope",
        "What Has Already Left",
        "What Still Lives In `automation_scheduler`",
        "Progress Against Retirement",
        "Retirement Blockers",
        "Exit State",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
    "LEGACY_DELETE_CANDIDATE_QUEUE_AFTER_10K8ZG2.md": [
        "Executive Summary",
        "Delete-Ready-After-Import-Proof",
        "Requires Dependency Migration First",
        "Requires Test Rewrite First",
        "Must Not Delete Yet",
        "Non-Goal but Still Requires Proof",
        "Recommended Deletion Phase",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
    "NEXT_DELETION_BATCH_RECOMMENDATIONS_AFTER_10K8ZG2.md": [
        "Executive Summary",
        "Recommended Batch 1",
        "Recommended Batch 2",
        "Recommended Batch 3",
        "Safest Batch Definition",
        "Acceptance Results",
        "Next Phase Recommendation",
    ],
}

REQUIRED_PHRASES = [
    "No deletion occurs in this phase. This phase establishes deletion readiness evidence only.",
    "CANONICAL_REPLACED",
    "SHIM_ONLY",
    "LEGACY_RUNTIME_OWNER",
    "RETIREMENT_BLOCKER",
    "DELETE_READY_AFTER_IMPORT_PROOF",
    "UNKNOWN",
    "src/providers",
    "src/connectors",
    "providers/",
    "betting_providers/",
    "automation_scheduler/",
    "Top 20 Retirement Blockers",
    "First 20 Delete Candidates",
    "Safest Deletion Batch",
    "~55%",
    "~84%",
]

CANONICAL_IMPORTS = [
    "src.providers",
    "src.providers.prediction_markets.adapters",
    "src.providers.sportsbooks.adapters",
    "src.providers.zero_dte_stocks.provider",
    "src.connectors",
    "src.connectors.market_data.models",
    "src.connectors.prediction_market_data.adapter",
    "src.connectors.odds_data.adapter",
]

LEGACY_IMPORTS = [
    "providers.base_provider",
    "providers.odds_provider_router",
    "providers.kalshi_provider",
    "providers.sharp_provider",
    "betting_providers.base",
    "betting_providers.normalization",
    "betting_providers.provider_router",
    "betting_providers.kalshi_api",
    "betting_providers.sharp_api",
    "betting_providers.the_odds_api",
    "betting_providers.sportsgameodds",
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_registry",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_secret_policy",
    "automation_scheduler.provider_write_firewall",
    "src.services.enrichment_service",
    "src.api.provider_status_routes",
]

FORBIDDEN_IMPORT_ROOTS = {
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def assert_doc(path: str, sections: list[str]) -> None:
    text = read(path)
    for section in sections:
        assert section in text, f"missing section {section!r} in {path}"


def test_phase10k8zg2_legacy_deletion_readiness_audit():
    # Documentation artifacts
    for doc, sections in DOCS.items():
        assert (ROOT / doc).exists(), doc
        assert_doc(doc, sections)

    main_audit = read("PHASE10K8ZG2_LEGACY_DELETION_READINESS_AUDIT.md")
    for phrase in REQUIRED_PHRASES:
        assert phrase in main_audit, phrase

    # Canonical package import safety
    original_getenv = os.getenv
    try:
        def forbidden_getenv(*_args, **_kwargs):
            raise AssertionError("import-time credential access is forbidden")

        os.getenv = forbidden_getenv  # type: ignore[assignment]
        for module_name in CANONICAL_IMPORTS:
            sys.modules.pop(module_name, None)
            importlib.import_module(module_name)
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]

    # Legacy compatibility imports still resolve for the wrapper-only surface.
    for module_name in LEGACY_IMPORTS:
        importlib.import_module(module_name)

    # The canonical package trees must not directly import live network clients.
    for package in (ROOT / "src/providers", ROOT / "src/connectors"):
        for py_file in package.rglob("*.py"):
            roots = imported_roots(py_file)
            assert not (roots & FORBIDDEN_IMPORT_ROOTS), f"forbidden import in {py_file}: {roots & FORBIDDEN_IMPORT_ROOTS}"
            assert "automation_scheduler" not in roots
            assert "betting_providers" not in roots
            assert "providers" not in roots

    # Legacy retention evidence.
    dependency_report = read("LEGACY_RUNTIME_DEPENDENCY_REPORT_AFTER_10K8ZG2.md")
    for required in [
        "main.py",
        "streamlit_app.py",
        "src/api/provider_status_routes.py",
        "src/services/enrichment_service.py",
        "providers/kalshi_provider.py",
        "providers/sharp_provider.py",
        "betting_providers/provider_router.py",
        "automation_scheduler/kalshi_readonly_adapter.py",
        "automation_scheduler/sharp_sportsbook_adapter.py",
        "kalshi_client.py",
        "sharp_client.py",
    ]:
        assert required in dependency_report, required

    # The audit must clearly state that deletion is not authorized yet.
    for doc in DOCS:
        text = read(doc)
        assert "No deletion occurs in this phase" in text or "No deletion occurs in this phase." in text
