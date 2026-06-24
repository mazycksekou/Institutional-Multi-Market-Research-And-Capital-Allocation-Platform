from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIR_EXECUTION_HELPER_RUNTIME_REDIRECTION.md",
    ROOT / "EXECUTION_HELPER_RUNTIME_REDIRECTION_MAP_AFTER_10K8ZIR.md",
    ROOT / "EXECUTION_HELPER_COMPATIBILITY_REPORT_AFTER_10K8ZIR.md",
    ROOT / "EXECUTION_HELPER_RUNTIME_DELETE_READINESS_AFTER_10K8ZIR.md",
]

RUNTIME_FILES = [
    ROOT / "automation_scheduler" / "__init__.py",
    ROOT / "src" / "brokerage" / "readiness.py",
    ROOT / "src" / "api" / "automation_institutional_lab_routes.py",
]


def test_runtime_redirection_docs_exist() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "automation_scheduler/__init__.py",
        "src.services.settlement_service",
        "src.services.ledger_service",
        "src.services.execution_service",
        "src.brokerage.settlement",
        "All nine wrapper-only execution helpers are delete-ready after proof.",
    ]:
        assert fragment in text


def test_runtime_files_import_canonical_services_only() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in RUNTIME_FILES)
    for fragment in [
        "from src.services.settlement_service import build_outcome_completion_report, write_outcome_completion_candidates",
        "from src.services.ledger_service import load_security_audit_records",
        "from src.services.execution_service import build_broker_quality_report",
        "from src.services.execution_service import SAFETY_FLAGS",
        "from src.services.execution_service import run_small_account_review",
        "from src.services.execution_service import simulate_execution",
        "from src.services.execution_service import rejection_response",
        "from src.services.ledger_service import append_security_event",
    ]:
        assert fragment in text
    for wrapper_name in [
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
