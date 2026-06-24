from __future__ import annotations

import importlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIC_EXECUTION_OWNERSHIP_MIGRATION.md",
    ROOT / "EXECUTION_OWNERSHIP_MIGRATION_MAP_AFTER_10K8ZIC.md",
    ROOT / "EXECUTION_RUNTIME_REDIRECTION_AFTER_10K8ZIC.md",
    ROOT / "EXECUTION_COMPATIBILITY_REPORT_AFTER_10K8ZIC.md",
]


def test_execution_migration_docs_state_wrapper_only_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "automation_scheduler/execution_gatekeeper.py",
        "automation_scheduler/execution_authorization.py",
        "automation_scheduler/paper_trade_ledger.py",
        "automation_scheduler/paper_decision_ledger.py",
        "src.brokerage.orders",
        "src.brokerage.execution",
        "src.brokerage.ledger",
        "src.brokerage.readiness",
        "Compatibility wrappers still exist",
        "No live execution exists.",
        "No paper-only canonical path exists.",
    ]:
        assert phrase in text


def test_execution_migration_modules_use_canonical_brokerage_surfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")
    gatekeeper = importlib.import_module("automation_scheduler.execution_gatekeeper")
    authorization = importlib.import_module("automation_scheduler.execution_authorization")
    paper_trade_ledger = importlib.import_module("automation_scheduler.paper_trade_ledger")
    paper_decision_ledger = importlib.import_module("automation_scheduler.paper_decision_ledger")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "TEST", "stake": 10, "american_odds": -110, "decision_id": "d1", "provider": "demo"}
    )
    assert plan["readiness"]["ready"] is False
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
        assert Path(tmp).exists()

    assert readiness.get_execution_readiness(plan["order_request"]).ready is False


def test_no_legacy_deletion_in_migration() -> None:
    for relpath in [
        "automation_scheduler/execution_gatekeeper.py",
        "automation_scheduler/execution_authorization.py",
        "automation_scheduler/paper_trade_ledger.py",
        "automation_scheduler/paper_decision_ledger.py",
    ]:
        assert (ROOT / relpath).exists()

