from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZID_EXECUTION_FINAL_DELETE_READINESS.md",
    ROOT / "FINAL_EXECUTION_IMPORT_SCAN_AFTER_10K8ZID.md",
    ROOT / "FINAL_EXECUTION_TEST_SCAN_AFTER_10K8ZID.md",
    ROOT / "FINAL_EXECUTION_DELETE_DECISION_AFTER_10K8ZID.md",
]

DOC_REFERENCES = [
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

CANONICAL_FILES = [
    "automation_scheduler/paper_trade_ledger.py",
    "automation_scheduler/paper_decision_ledger.py",
    "src/brokerage/settlement.py",
    "src/services/settlement_service.py",
    "src/services/ledger_service.py",
    "src/services/execution_service.py",
    "src/brokerage/readiness.py",
    "bet_decision_engine.py",
    "bet_log.py",
]

REMOVED_FILES = [
    "automation_scheduler/execution_gatekeeper.py",
    "automation_scheduler/execution_authorization.py",
]


def test_final_delete_readiness_docs_state_no_delete_ready_targets() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Canonical execution flow:",
        "src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary",
        "DELETE_READY_AFTER_PROOF: none",
        "main.py is not a deletion candidate.",
        "streamlit_app.py is not a deletion candidate.",
    ]:
        assert phrase in text
    for relpath in DOC_REFERENCES:
        assert relpath in text
    for classification in [
        "COMPATIBILITY_WRAPPER_ONLY",
        "ACTIVE_RUNTIME_DEPENDENCY",
        "UNSAFE_TO_TOUCH",
    ]:
        assert classification in text


def test_final_delete_readiness_modules_import_and_remain_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = importlib.import_module("src.brokerage")
    orders = importlib.import_module("src.brokerage.orders")
    execution = importlib.import_module("src.brokerage.execution")
    ledger = importlib.import_module("src.brokerage.ledger")
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")
    gatekeeper = importlib.import_module("src.brokerage.readiness")
    authorization = importlib.import_module("src.brokerage.readiness")
    paper_trade_ledger = importlib.import_module("automation_scheduler.paper_trade_ledger")
    paper_decision_ledger = importlib.import_module("automation_scheduler.paper_decision_ledger")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "TEST", "stake": 10, "american_odds": -110, "decision_id": "d1", "provider": "demo"}
    )
    assert plan["readiness"]["ready"] is False
    assert plan["readiness"]["status"] == "disabled"
    assert plan["readiness"]["brokerage_boundary_disabled"] is True
    assert plan["order_request"]["instrument_id"] == "TEST"

    eligibility = gatekeeper.evaluate_future_execution_eligibility({"weighted_score": 90, "calibration_support_score": 80})
    assert eligibility["future_execution_eligible"] is False
    auth = authorization.evaluate_execution_authorization({"provider": "demo", "action": "submit_order"}, persist_audit=False)
    assert auth["status"] == "execution_attempt_blocked"

    assert callable(brokerage.submit_order_disabled)
    assert callable(orders.build_order_request)
    assert callable(execution.submit_order_disabled)
    assert callable(ledger.record_ledger_event)
    assert callable(readiness.get_execution_readiness)

    with pytest.raises(Exception):
        execution.submit_order_disabled(plan["execution_request"])

    with pytest.raises(Exception):
        brokerage.submit_order_disabled(plan["execution_request"])

    for relpath in CANONICAL_FILES:
        assert (ROOT / relpath).exists()
    for relpath in REMOVED_FILES:
        assert not (ROOT / relpath).exists()

    with importlib.import_module("tempfile").TemporaryDirectory() as tmp:
        paper_entry = paper_trade_ledger.create_paper_entry(
            {
                "recommendation_id": "rec1",
                "model_id": "m1",
                "model_group": "sports",
                "market_type": "moneyline",
                "recommended_odds": -110,
                "paper_stake": 10,
            },
            base_dir=tmp,
        )
        paper_decision = paper_decision_ledger.create_paper_decision_record(
            {
                "id": "review_1",
                "provider_id": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "ticker": "KXTEST",
                "contract_id": "KXTEST",
                "implied_probability": 0.55,
                "recommendation_status": "review_only",
                "execution_allowed": False,
            },
            base_data_dir=tmp,
        )
        assert paper_entry["human_approval_required"] is True
        assert "brokerage_ledger_event" in paper_entry
        assert paper_decision["paper_only"] is True
        assert "brokerage_ledger_event" in paper_decision


def test_final_delete_readiness_no_delete_ready_queue() -> None:
    text = (ROOT / "FINAL_EXECUTION_DELETE_DECISION_AFTER_10K8ZID.md").read_text(encoding="utf-8")
    assert "DELETE_READY_AFTER_PROOF: none" in text
    assert "No execution/trade/bet/settlement wrapper was proven safe to delete" in (ROOT / "PHASE10K8ZID_EXECUTION_FINAL_DELETE_READINESS.md").read_text(encoding="utf-8")
