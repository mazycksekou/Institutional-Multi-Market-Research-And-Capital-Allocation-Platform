from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .institutional_audit_ledger import append_audit_record
from .institutional_cross_asset_adapters import compact_redact, read_existing_outputs
from .institutional_cross_asset_calibration import build_calibration_by_asset_class
from .institutional_risk_engine import assess_institutional_risk
from .scheduler_config import safe_run_id, sanitize_filename, utc_now_iso


EXECUTION_SAFETY_FLAGS = {
    "simulation_only": True,
    "live_execution_enabled": False,
    "provider_write": False,
    "execution_allowed": False,
    "requires_human_command": True,
    "actual_order_submitted": False,
    "actual_bet_submitted": False,
    "actual_trade_submitted": False,
}

LIVE_FLAG_FIELDS = (
    "live_execution_requested",
    "submit_live_order",
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "auto_execution_enabled",
    "auto_bet_enabled",
    "auto_trade_enabled",
    "kalshi_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "broker_order_execution_enabled",
)


class ExecutionDeskRejected(ValueError):
    pass


def _execution_dir(base_data_dir: str = "data") -> Path:
    path = Path(base_data_dir) / "institutional_lab" / "execution_sim"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def validate_simulation_request(payload: dict[str, Any]) -> None:
    if payload.get("simulation_only") is not True:
        raise ExecutionDeskRejected("execution desk requires simulation_only=true")
    for field in LIVE_FLAG_FIELDS:
        if payload.get(field) is True:
            raise ExecutionDeskRejected(f"execution desk rejects {field}=true")
    if payload.get("human_command") not in (None, "simulate_only"):
        raise ExecutionDeskRejected("execution desk only accepts human_command=simulate_only")


def _find_candidate(records: list[dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any] | None:
    candidate_id = str(payload.get("candidate_id") or "")
    if not candidate_id:
        return None
    for row in records:
        if candidate_id in {str(row.get("sidecar_id")), str(row.get("source_record_id")), str(row.get("contract_id")), str(row.get("symbol_or_ticker"))}:
            return row
    return None


def _theoretical_size(payload: dict[str, Any], record: dict[str, Any], risk_result: dict[str, Any]) -> float | None:
    max_risk = payload.get("max_theoretical_risk")
    try:
        max_risk_float = float(max_risk)
    except (TypeError, ValueError):
        max_risk_float = 0.0
    if max_risk_float <= 0:
        return None
    if risk_result.get("risk_blocks"):
        return None
    confidence = float(record.get("confidence_score") or 0.0) / 100.0
    liquidity = float(record.get("liquidity_score") or 0.0) / 100.0
    return round(max_risk_float * min(0.25, confidence * liquidity * 0.25), 6)


def simulate_execution(
    payload: dict[str, Any],
    *,
    records: list[dict[str, Any]] | None = None,
    calibration_report: dict[str, Any] | None = None,
    base_data_dir: str = "data",
    persist: bool = True,
) -> dict[str, Any]:
    validate_simulation_request(payload)
    available_records = records if records is not None else read_existing_outputs(
        base_data_dir=base_data_dir,
        asset_classes=[payload.get("asset_class") or "prediction_market"],
    ).get("records", [])
    candidate = _find_candidate(available_records, payload) if available_records else None
    if candidate is None:
        candidate = {
            "sidecar_id": payload.get("candidate_id"),
            "source_record_id": payload.get("candidate_id"),
            "asset_class": payload.get("asset_class"),
            "provider": payload.get("provider"),
            "reason_codes": ["missing_candidate"],
            "execution_allowed": False,
            "paper_only": True,
            "review_only": True,
            "simulation_only": True,
        }
    if calibration_report is None and available_records:
        calibration_report = build_calibration_by_asset_class(available_records)
    risk_result = assess_institutional_risk(candidate, calibration_report=calibration_report)
    if candidate.get("reason_codes") and "missing_candidate" in candidate.get("reason_codes"):
        risk_result["risk_blocks"] = sorted(set(list(risk_result.get("risk_blocks", [])) + ["missing_candidate"]))
    run_id = f"execution_sim_{safe_run_id('institutional_execution_sim', utc_now_iso() + str(payload.get('candidate_id')))}"
    audit = append_audit_record(
        action_type="execution_simulation",
        run_id=run_id,
        asset_class=str(candidate.get("asset_class") or payload.get("asset_class") or "unknown"),
        provider=str(candidate.get("provider") or payload.get("provider") or "unknown"),
        source_record_id=str(candidate.get("source_record_id") or payload.get("candidate_id") or ""),
        input_payload=payload,
        output_payload=risk_result,
        safety_flags={**EXECUTION_SAFETY_FLAGS, "simulated_ticket_created": True},
        compact_summary="Execution desk simulation only; no provider write.",
        base_data_dir=base_data_dir,
    )
    result = {
        "ok": True,
        "status": "simulated",
        "execution_desk_status": "simulation_only",
        "run_id": run_id,
        "live_execution_enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "asset_class": candidate.get("asset_class") or payload.get("asset_class"),
        "provider": candidate.get("provider") or payload.get("provider"),
        "candidate_id": payload.get("candidate_id"),
        "pre_trade_checks_passed": False,
        "risk_blocks": sorted(set(risk_result.get("risk_blocks", []))),
        "warnings": sorted(set(risk_result.get("warnings", []))),
        "risk_score": risk_result.get("risk_score"),
        "risk_tier": risk_result.get("risk_tier"),
        "theoretical_size": _theoretical_size(payload, candidate, risk_result),
        "simulated_ticket_created": True,
        "actual_order_submitted": False,
        "actual_bet_submitted": False,
        "actual_trade_submitted": False,
        "human_command_required": True,
        "requires_human_command": True,
        "audit_id": audit["audit_id"],
        "simulation_only": True,
        "actual_provider_destination": None,
        "broker_order_id": None,
        "sportsbook_bet_id": None,
        "kalshi_order_id": None,
        "raw_payload_included": False,
    }
    result.update(EXECUTION_SAFETY_FLAGS)
    if persist:
        path = _execution_dir(base_data_dir) / f"{sanitize_filename(run_id)}.json"
        _atomic_write_json(path, compact_redact(result))
        latest = _execution_dir(base_data_dir) / "latest.json"
        _atomic_write_json(latest, compact_redact(result))
        result["execution_sim_path"] = str(path.relative_to(Path(base_data_dir))).replace("\\", "/")
    return result


def rejection_response(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "rejected",
        "rejected_reason": reason,
        "execution_desk_status": "simulation_only",
        **EXECUTION_SAFETY_FLAGS,
        "simulated_ticket_created": False,
        "pre_trade_checks_passed": False,
        "risk_blocks": ["live_execution_flags_rejected"],
        "human_command_required": True,
        "raw_payload_included": False,
    }
