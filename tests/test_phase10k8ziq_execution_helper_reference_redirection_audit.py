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
    'src/automation_scheduler_legacy/settlement_rule_checker.py',
    'src/automation_scheduler_legacy/settlement_discovery.py',
    'src/automation_scheduler_legacy/audit_ledger.py',
    'src/automation_scheduler_legacy/institutional_audit_ledger.py',
    'src/automation_scheduler_legacy/strategy_performance_ledger.py',
    'src/automation_scheduler_legacy/broker_quality_scoring.py',
    'src/automation_scheduler_legacy/small_account_strategy.py',
    'src/automation_scheduler_legacy/manifold_no_bet_detector.py',
    'src/automation_scheduler_legacy/institutional_execution_desk.py',
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
