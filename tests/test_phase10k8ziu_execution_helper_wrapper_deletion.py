from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELETED = [
    ROOT / "automation_scheduler" / "settlement_rule_checker.py",
    ROOT / "automation_scheduler" / "settlement_discovery.py",
    ROOT / "automation_scheduler" / "audit_ledger.py",
    ROOT / "automation_scheduler" / "institutional_audit_ledger.py",
    ROOT / "automation_scheduler" / "strategy_performance_ledger.py",
    ROOT / "automation_scheduler" / "broker_quality_scoring.py",
    ROOT / "automation_scheduler" / "small_account_strategy.py",
    ROOT / "automation_scheduler" / "manifold_no_bet_detector.py",
    ROOT / "automation_scheduler" / "institutional_execution_desk.py",
]

PRESERVED = [
    ROOT / "automation_scheduler" / "paper_trade_ledger.py",
    ROOT / "automation_scheduler" / "paper_decision_ledger.py",
    ROOT / "src" / "brokerage" / "settlement.py",
    ROOT / "src" / "services" / "settlement_service.py",
    ROOT / "src" / "services" / "ledger_service.py",
    ROOT / "src" / "services" / "execution_service.py",
    ROOT / "src" / "brokerage" / "readiness.py",
]


def test_wrapper_deletion_only_approved_files() -> None:
    for path in DELETED:
        assert not path.exists()
    for path in PRESERVED:
        assert path.exists()
    for path in [
        ROOT / "automation_scheduler" / "execution_gatekeeper.py",
        ROOT / "automation_scheduler" / "execution_authorization.py",
    ]:
        assert not path.exists()


def test_canonical_execution_path_still_imports_and_stays_disabled() -> None:
    brokerage = importlib.import_module("src.brokerage")
    orders = importlib.import_module("src.brokerage.orders")
    execution = importlib.import_module("src.brokerage.execution")
    ledger = importlib.import_module("src.brokerage.ledger")
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "TEST", "stake": 10, "american_odds": -110, "decision_id": "d1", "provider": "demo"}
    )
    assert plan["readiness"]["ready"] is False
    assert plan["readiness"]["brokerage_boundary_disabled"] is True
    assert callable(brokerage.submit_order_disabled)
    assert callable(orders.build_order_request)
    assert callable(execution.submit_order_disabled)
    assert callable(ledger.record_ledger_event)
    assert callable(readiness.get_execution_readiness)
