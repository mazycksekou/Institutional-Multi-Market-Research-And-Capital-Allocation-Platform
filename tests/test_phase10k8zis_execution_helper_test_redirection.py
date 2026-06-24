from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIS_EXECUTION_HELPER_TEST_REDIRECTION.md",
    ROOT / "EXECUTION_HELPER_TEST_REDIRECTION_MAP_AFTER_10K8ZIS.md",
    ROOT / "EXECUTION_HELPER_TEST_COMPATIBILITY_REPORT_AFTER_10K8ZIS.md",
    ROOT / "EXECUTION_HELPER_TEST_DELETE_READINESS_AFTER_10K8ZIS.md",
]

TEST_FILES = [
    ROOT / "tests" / "test_settlement_rule_checker.py",
    ROOT / "tests" / "test_settlement_discovery.py",
    ROOT / "tests" / "test_institutional_execution_desk.py",
    ROOT / "tests" / "test_small_account_strategy.py",
    ROOT / "tests" / "test_broker_quality_scoring.py",
    ROOT / "tests" / "test_institutional_audit_ledger.py",
    ROOT / "tests" / "test_outcome_store.py",
    ROOT / "tests" / "test_market_state_manifold.py",
    ROOT / "tests" / "test_security_framework.py",
]


def test_test_redirection_docs_exist() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "tests/test_settlement_rule_checker.py",
        "src.services.settlement_service",
        "src.services.ledger_service",
        "src.services.execution_service",
        "Wrapper references are historical evidence only.",
        "All nine wrapper-only execution helpers remain delete-ready after test redirection.",
    ]:
        assert fragment in text


def test_redirected_tests_use_canonical_helpers() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in TEST_FILES)
    for fragment in [
        "src.brokerage.settlement",
        "src.services.settlement_service",
        "src.services.ledger_service",
        "src.services.execution_service",
    ]:
        assert fragment in text
    for wrapper_name in [
        "automation_scheduler.settlement_rule_checker",
        "automation_scheduler.settlement_discovery",
        "automation_scheduler.audit_ledger",
        "automation_scheduler.institutional_audit_ledger",
        "automation_scheduler.strategy_performance_ledger",
        "automation_scheduler.broker_quality_scoring",
        "automation_scheduler.small_account_strategy",
        "automation_scheduler.manifold_no_bet_detector",
        "automation_scheduler.institutional_execution_desk",
    ]:
        assert wrapper_name not in text
