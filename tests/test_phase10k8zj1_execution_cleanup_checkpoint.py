from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_execution_cleanup_checkpoint_docs_exist_and_state() -> None:
    for path in [
        ROOT / "PHASE10K8ZJ1_EXECUTION_CLEANUP_CHECKPOINT.md",
        ROOT / "POST_EXECUTION_CLEANUP_ARCHITECTURE_MAP_AFTER_10K8ZJ1.md",
        ROOT / "REMAINING_EXECUTION_BLOCKERS_AFTER_10K8ZJ1.md",
        ROOT / "NEXT_LIVE_TRADING_READINESS_PLAN_AFTER_10K8ZJ1.md",
    ]:
        assert path.is_file(), path

    text = (ROOT / "PHASE10K8ZJ1_EXECUTION_CLEANUP_CHECKPOINT.md").read_text(encoding="utf-8")
    for phrase in [
        "automation_scheduler/execution_gatekeeper.py: deleted",
        "automation_scheduler/execution_authorization.py: deleted",
        "automation_scheduler/paper_trade_ledger.py: preserved",
        "automation_scheduler/paper_decision_ledger.py: preserved",
        "Live trading remains disabled",
        "broker account creation remains disabled",
    ]:
        assert phrase in text


def test_execution_cleanup_checkpoint_imports_safe() -> None:
    brokerage = importlib.import_module("src.brokerage")
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")
    paper_trade_ledger = importlib.import_module("automation_scheduler.paper_trade_ledger")
    paper_decision_ledger = importlib.import_module("automation_scheduler.paper_decision_ledger")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "META", "stake": 7, "american_odds": -108, "decision_id": "d6", "provider": "demo"}
    )
    assert brokerage.get_execution_readiness(plan["order_request"]).ready is False
    assert callable(readiness.get_execution_readiness)
    assert callable(paper_trade_ledger.create_paper_entry)
    assert callable(paper_decision_ledger.create_paper_decision_record)
