from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIQ_EXECUTION_HELPER_REFERENCE_REDIRECTION_AUDIT.md",
    ROOT / "EXECUTION_HELPER_ACTIVE_REFERENCE_SCAN_AFTER_10K8ZIQ.md",
    ROOT / "EXECUTION_HELPER_TEST_REFERENCE_SCAN_AFTER_10K8ZIQ.md",
    ROOT / "EXECUTION_HELPER_REDIRECTION_PLAN_AFTER_10K8ZIQ.md",
]

WRAPPERS = [
    "automation_scheduler/settlement_rule_checker.py",
    "automation_scheduler/settlement_discovery.py",
    "automation_scheduler/audit_ledger.py",
    "automation_scheduler/institutional_audit_ledger.py",
    "automation_scheduler/strategy_performance_ledger.py",
    "automation_scheduler/broker_quality_scoring.py",
    "automation_scheduler/small_account_strategy.py",
    "automation_scheduler/manifold_no_bet_detector.py",
    "automation_scheduler/institutional_execution_desk.py",
]


def test_reference_redirection_docs_exist_and_state_delete_readiness() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "Canonical execution flow:",
        "Runtime references: none.",
        "Test references: none.",
        "Doc-only references: historical proof only.",
        "All nine wrappers are `DELETE_READY_AFTER_PROOF`.",
        "src.services.settlement_service",
        "src.services.ledger_service",
        "src.services.execution_service",
        "src.brokerage.settlement",
    ]:
        assert fragment in text
    for wrapper in WRAPPERS:
        assert wrapper in text
