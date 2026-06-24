from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIX_FINAL_EXECUTION_BLOCKER_CANONICALIZATION.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_CANONICALIZATION_MAP_AFTER_10K8ZIX.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_COMPATIBILITY_REPORT_AFTER_10K8ZIX.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_RUNTIME_REDIRECTION_AFTER_10K8ZIX.md",
]


def test_final_execution_blocker_canonicalization_docs_exist() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "src.brokerage.readiness",
        "src.services.decision_engine",
        "src.services.execution_service",
        "paper ledgers remain compatibility inputs",
        "delete-ready after proof",
    ]:
        assert phrase in text


def test_final_execution_blocker_canonicalization_imports_safe() -> None:
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")
    execution_service = importlib.import_module("src.services.execution_service")
    ledger_service = importlib.import_module("src.services.ledger_service")
    paper_trade_ledger = importlib.import_module("automation_scheduler.paper_trade_ledger")
    paper_decision_ledger = importlib.import_module("automation_scheduler.paper_decision_ledger")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "AAPL", "stake": 12, "american_odds": -120, "decision_id": "d2", "provider": "demo"}
    )
    assert readiness.get_execution_readiness(plan["order_request"]).ready is False
    assert callable(execution_service.build_broker_quality_report)
    assert callable(ledger_service.load_security_audit_records)
    assert callable(paper_trade_ledger.create_paper_entry)
    assert callable(paper_decision_ledger.create_paper_decision_record)
    assert not (ROOT / "automation_scheduler" / "execution_gatekeeper.py").exists()
    assert not (ROOT / "automation_scheduler" / "execution_authorization.py").exists()
