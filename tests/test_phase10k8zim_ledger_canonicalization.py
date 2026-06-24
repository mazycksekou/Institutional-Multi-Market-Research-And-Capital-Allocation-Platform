from __future__ import annotations

import importlib
from pathlib import Path


def test_ledger_canonical_modules_import_and_delegate(tmp_path: Path) -> None:
    service = importlib.import_module("src.services.ledger_service")

    assert service.append_security_event.__module__ == "src.services.ledger_service"
    assert service.append_audit_record.__module__ == "src.services.ledger_service"
    assert service.append_strategy_performance_record.__module__ == "src.services.ledger_service"
    assert service.STRATEGY_PERFORMANCE_SCHEMA_VERSION.endswith("strategy_performance_ledger.v1")

    security = service.append_security_event(
        event_type="integration_test",
        request_payload={"api_key": "redacted"},
        response_payload={"status": "ok"},
        base_data_dir=str(tmp_path),
    )
    assert security["status"] == "audit_record_written"
    assert service.load_security_audit_records(base_data_dir=str(tmp_path))["count"] == 1

    record = service.append_audit_record(
        action_type="daily_report",
        provider="demo",
        asset_class="stock",
        input_payload={"answer": 1},
        output_payload={"result": "ok"},
        base_data_dir=str(tmp_path),
    )
    assert record["record"]["provider_write"] is False
    assert service.load_audit_records(base_data_dir=str(tmp_path))["count"] == 1

    perf = service.append_strategy_performance_record(
        {"strategy_id": "alpha", "candidate_id": "c1", "expected_value": 1.5},
        base_data_dir=str(tmp_path),
    )
    assert perf["status"] == "strategy_performance_record_written"
    ledger = service.load_strategy_performance_ledger(base_data_dir=str(tmp_path))
    assert ledger["count"] == 1
    summary = service.summarize_strategy_performance(ledger["items"])
    assert summary["total_records"] == 1
    assert summary["strategies"][0]["strategy_id"] == "alpha"


def test_ledger_canonical_files_still_exist() -> None:
    for relpath in [
        "src/services/ledger_service.py",
        "src/brokerage/ledger.py",
    ]:
        assert Path(relpath).exists(), relpath
