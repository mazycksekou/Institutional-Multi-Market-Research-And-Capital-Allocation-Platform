from __future__ import annotations

import importlib
from pathlib import Path


def test_ledger_canonical_modules_import_and_delegate(tmp_path: Path) -> None:
    service = importlib.import_module("src.services.ledger_service")
    audit = importlib.import_module("automation_scheduler.audit_ledger")
    institutional = importlib.import_module("automation_scheduler.institutional_audit_ledger")
    strategy = importlib.import_module("automation_scheduler.strategy_performance_ledger")

    assert audit.append_security_event.__module__ == "src.services.ledger_service"
    assert institutional.append_audit_record.__module__ == "src.services.ledger_service"
    assert strategy.append_strategy_performance_record.__module__ == "src.services.ledger_service"
    assert strategy.SCHEMA_VERSION == service.STRATEGY_PERFORMANCE_SCHEMA_VERSION

    security = audit.append_security_event(
        event_type="integration_test",
        request_payload={"api_key": "redacted"},
        response_payload={"status": "ok"},
        base_data_dir=str(tmp_path),
    )
    assert security["status"] == "audit_record_written"
    assert audit.load_security_audit_records(base_data_dir=str(tmp_path))["count"] == 1

    record = institutional.append_audit_record(
        action_type="daily_report",
        provider="demo",
        asset_class="stock",
        input_payload={"answer": 1},
        output_payload={"result": "ok"},
        base_data_dir=str(tmp_path),
    )
    assert record["record"]["provider_write"] is False
    assert institutional.load_audit_records(base_data_dir=str(tmp_path))["count"] == 1

    perf = strategy.append_strategy_performance_record(
        {"strategy_id": "alpha", "candidate_id": "c1", "expected_value": 1.5},
        base_data_dir=str(tmp_path),
    )
    assert perf["status"] == "strategy_performance_record_written"
    ledger = strategy.load_strategy_performance_ledger(base_data_dir=str(tmp_path))
    assert ledger["count"] == 1
    summary = strategy.summarize_strategy_performance(ledger["items"])
    assert summary["total_records"] == 1
    assert summary["strategies"][0]["strategy_id"] == "alpha"


def test_ledger_wrapper_files_still_exist() -> None:
    for relpath in [
        "automation_scheduler/audit_ledger.py",
        "automation_scheduler/institutional_audit_ledger.py",
        "automation_scheduler/strategy_performance_ledger.py",
        "src/services/ledger_service.py",
        "src/brokerage/ledger.py",
    ]:
        assert Path(relpath).exists(), relpath
