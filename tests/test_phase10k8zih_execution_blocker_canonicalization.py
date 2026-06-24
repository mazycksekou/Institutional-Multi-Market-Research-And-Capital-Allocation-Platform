from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIH_EXECUTION_BLOCKER_CANONICALIZATION.md",
    ROOT / "EXECUTION_BLOCKER_CANONICALIZATION_MAP_AFTER_10K8ZIH.md",
    ROOT / "EXECUTION_BLOCKER_COMPATIBILITY_REPORT_AFTER_10K8ZIH.md",
    ROOT / "EXECUTION_BLOCKER_RUNTIME_REDIRECTION_AFTER_10K8ZIH.md",
]


def test_execution_blocker_canonicalization_docs_state_wrapper_only() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Canonical live-shaped execution path remains:",
        "src.brokerage.orders",
        "src.brokerage.execution",
        "src.brokerage.ledger",
        "src.brokerage.readiness",
        "compatibility wrappers remain on disk",
    ]:
        assert phrase in text


def test_execution_blocker_canonicalization_modules_import_and_delegate() -> None:
    decision_engine = importlib.import_module("src.services.decision_engine")
    brokerage = importlib.import_module("src.brokerage")
    execution = importlib.import_module("src.brokerage.execution")
    paper_trade_ledger = importlib.import_module("automation_scheduler.paper_trade_ledger")
    paper_decision_ledger = importlib.import_module("automation_scheduler.paper_decision_ledger")
    gatekeeper = importlib.import_module("automation_scheduler.execution_gatekeeper")
    authorization = importlib.import_module("automation_scheduler.execution_authorization")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "ABC", "stake": 15, "american_odds": -120, "decision_id": "plan-1", "provider": "demo"}
    )
    assert plan["order_request"]["instrument_id"] == "ABC"
    assert plan["readiness"]["status"] == "disabled"

    assert callable(brokerage.submit_order_disabled)
    assert callable(execution.submit_order_disabled)
    with pytest.raises(Exception):
        brokerage.submit_order_disabled(plan["execution_request"])
    with pytest.raises(Exception):
        execution.submit_order_disabled(plan["execution_request"])

    assert gatekeeper.evaluate_future_execution_eligibility({"weighted_score": 90, "calibration_support_score": 80})["future_execution_eligible"] is False
    assert authorization.evaluate_execution_authorization({"provider": "demo", "action": "submit_order"}, persist_audit=False)["status"] == "execution_attempt_blocked"

    with importlib.import_module("tempfile").TemporaryDirectory() as tmp:
        entry = paper_trade_ledger.create_paper_entry({"recommendation_id": "compat-1", "recommended_odds": -110, "paper_stake": 10}, base_dir=tmp)
        decision = paper_decision_ledger.create_paper_decision_record({"id": "compat-2", "provider_id": "demo", "market_type": "equity", "ticker": "ABC", "execution_allowed": False}, base_data_dir=tmp)
        assert entry["brokerage_ledger_event"]["event_type"] == "paper_trade_entry_created"
        assert decision["brokerage_ledger_event"]["event_type"] == "paper_decision_record_created"


