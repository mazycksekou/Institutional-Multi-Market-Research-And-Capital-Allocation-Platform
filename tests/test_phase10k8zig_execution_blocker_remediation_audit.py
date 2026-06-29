from __future__ import annotations

import importlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIG_EXECUTION_BLOCKER_REMEDIATION_AUDIT.md",
    ROOT / "EXECUTION_BLOCKER_OWNERSHIP_MAP_AFTER_10K8ZIG.md",
    ROOT / "EXECUTION_BLOCKER_IMPORT_SCAN_AFTER_10K8ZIG.md",
    ROOT / "EXECUTION_BLOCKER_TEST_SCAN_AFTER_10K8ZIG.md",
]


def test_execution_blocker_audit_docs_state_blocked_and_wrapper_only() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Canonical execution path:",
        "DELETE_READY_AFTER_PROOF: none",
        "COMPATIBILITY_WRAPPER_ONLY",
        "MIGRATE_TO_SRC_BROKERAGE",
        "MIGRATE_TO_SRC_SERVICES",
        "MIGRATE_TO_SRC_CORE",
        "main.py is not a deletion candidate.",
        "streamlit_app.py is not a deletion candidate.",
    ]:
        assert phrase in text


def test_execution_blocker_modules_import_safely_and_remain_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    decision_engine = importlib.import_module("src.services.decision_engine")
    brokerage = importlib.import_module("src.brokerage")
    orders = importlib.import_module("src.brokerage.orders")
    execution = importlib.import_module("src.brokerage.execution")
    ledger = importlib.import_module("src.brokerage.ledger")
    readiness = importlib.import_module("src.brokerage.readiness")
    gatekeeper = importlib.import_module("src.brokerage.readiness")
    authorization = importlib.import_module("src.brokerage.readiness")
    paper_trade_ledger = importlib.import_module('src.automation_scheduler_legacy.paper_trade_ledger')
    paper_decision_ledger = importlib.import_module('src.automation_scheduler_legacy.paper_decision_ledger')
    settlement_rule_checker = importlib.import_module("src.brokerage.settlement")
    settlement_discovery = importlib.import_module("src.services.settlement_service")
    bet_log = importlib.import_module("bet_log")
    bet_decision_engine = importlib.import_module("bet_decision_engine")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "TEST", "stake": 10, "american_odds": -110, "decision_id": "d1", "provider": "demo"}
    )
    assert plan["readiness"]["ready"] is False
    assert plan["readiness"]["brokerage_boundary_disabled"] is True
    assert plan["order_request"]["instrument_id"] == "TEST"

    eligibility = gatekeeper.evaluate_future_execution_eligibility({"weighted_score": 90, "calibration_support_score": 80})
    assert eligibility["future_execution_eligible"] is False
    auth = authorization.evaluate_execution_authorization({"provider": "demo", "action": "submit_order"}, persist_audit=False)
    assert auth["status"] == "execution_attempt_blocked"

    with TemporaryDirectory() as tmp:
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

    assert callable(orders.build_order_request)
    assert callable(execution.submit_order_disabled)
    assert callable(ledger.record_ledger_event)
    assert readiness.get_execution_readiness(plan["order_request"]).ready is False
    assert callable(settlement_rule_checker.compare_settlement_rules)
    assert callable(settlement_discovery.classify_kalshi_settlement)
    assert callable(bet_log.create_bet_log_entry)
    assert callable(bet_decision_engine.evaluate_lines_payload)

    for relpath in [
        'src/automation_scheduler_legacy/paper_trade_ledger.py',
        'src/automation_scheduler_legacy/paper_decision_ledger.py',
        "bet_decision_engine.py",
        "bet_log.py",
        "src/brokerage/readiness.py",
    ]:
        assert (ROOT / relpath).exists()
