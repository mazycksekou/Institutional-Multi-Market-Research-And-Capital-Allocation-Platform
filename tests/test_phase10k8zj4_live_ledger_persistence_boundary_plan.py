from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_live_ledger_persistence_docs_exist_and_state() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ4_LIVE_LEDGER_PERSISTENCE_BOUNDARY_PLAN.md",
        ROOT / "LIVE_LEDGER_PERSISTENCE_OWNERSHIP_MAP_AFTER_10K8ZJ4.md",
        ROOT / "LIVE_LEDGER_PERSISTENCE_DEFERRED_PLAN_AFTER_10K8ZJ4.md",
        ROOT / "LEDGER_COMPATIBILITY_STATUS_AFTER_10K8ZJ4.md",
    ]
    for path in docs:
        assert path.is_file(), path

    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    for phrase in [
        "src.brokerage.ledger",
        "src.services.ledger_service",
        "automation_scheduler/paper_trade_ledger.py",
        "automation_scheduler/paper_decision_ledger.py",
        "bet_log.py",
        "compatibility inputs only",
        "Live ledger persistence remains disabled",
        "no external writes",
    ]:
        assert phrase in text


def test_live_ledger_persistence_imports_are_local_only(monkeypatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage_ledger = _fresh_import("src.brokerage.ledger")
    ledger_service = _fresh_import("src.services.ledger_service")
    paper_trade_ledger = _fresh_import("src.brokerage.paper_trade_ledger")
    paper_decision_ledger = _fresh_import("src.brokerage.paper_decision_ledger")
    bet_log = _fresh_import("src.services.bet_log")

    event = brokerage_ledger.record_ledger_event(event_type="unit_test", subject_id="subject-1")
    assert event["event_type"] == "unit_test"
    assert brokerage_ledger.get_ledger_events()[-1]["subject_id"] == "subject-1"

    with tempfile.TemporaryDirectory() as tmp:
        audit = ledger_service.append_security_event(event_type="unit_test", actor_type="system", base_data_dir=tmp)
        assert audit["ok"] is True
        paper_entry = paper_trade_ledger.create_paper_entry({"recommendation_id": "r1", "recommended_odds": -110}, base_dir=tmp)
        paper_decision = paper_decision_ledger.create_paper_decision_record({"id": "d1", "provider_id": "demo", "market_type": "equity", "ticker": "ABC"}, base_data_dir=tmp)
        assert Path(tmp).joinpath("security", "audit").exists()
        assert Path(tmp).joinpath("paper_ledger").exists()
        assert paper_entry["ledger_id"]
        assert paper_decision["decision_id"]

    assert callable(bet_log.create_bet_log_entry)
    assert callable(bet_log.create_bet_log_entry)
