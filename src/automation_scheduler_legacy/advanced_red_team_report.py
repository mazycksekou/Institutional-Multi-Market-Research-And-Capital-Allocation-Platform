from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .advanced_shape_diagnostics import run_advanced_shape_diagnostics
from src.data.data_paths import resolve_base_data_dir
from src.services.scheduler_config import safe_run_id, sanitize_filename, utc_now_iso
from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import locked_safety_flags


SCHEMA_VERSION = "automation_scheduler.v1.advanced_red_team.v1"


def _root(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "advanced_red_team"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _reason_counts(rows: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason in list(row.get(key) or []):
            text = str(reason)
            counts[text] = counts.get(text, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def write_advanced_red_team_report(report: Mapping[str, Any], *, base_data_dir: str | None = None) -> dict[str, Any]:
    safe = redact_sensitive(dict(report))
    root = _root(base_data_dir)
    latest = root / "latest.json"
    date = str(safe.get("date") or utc_now_iso()[:10])
    history = root / "history" / f"{sanitize_filename(date)}.json"
    _atomic_write(latest, safe)
    _atomic_write(history, safe)
    return {
        "ok": True,
        "status": "advanced_red_team_report_written",
        "latest_path": "advanced_red_team/latest.json",
        "history_path": f"advanced_red_team/history/{history.name}",
        **locked_safety_flags(),
    }


def write_advanced_diagnostics(payload: Mapping[str, Any], *, base_data_dir: str | None = None) -> dict[str, Any]:
    safe = redact_sensitive(dict(payload))
    path = _root(base_data_dir) / "diagnostics" / "latest.json"
    _atomic_write(path, safe)
    return {
        "ok": True,
        "status": "advanced_red_team_diagnostics_written",
        "latest_path": "advanced_red_team/diagnostics/latest.json",
        **locked_safety_flags(),
    }


def load_advanced_red_team_latest(*, base_data_dir: str | None = None) -> dict[str, Any]:
    path = _root(base_data_dir) / "latest.json"
    if not path.exists():
        return {"ok": True, "status": "not_run", "items": [], "red_team_only": True, **locked_safety_flags()}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "status": "read_error", "items": [], "red_team_only": True, **locked_safety_flags()}
    if isinstance(payload, dict):
        payload.update(locked_safety_flags())
        payload["red_team_only"] = True
        return payload
    return {"ok": False, "status": "invalid_report", "items": [], "red_team_only": True, **locked_safety_flags()}


def build_advanced_red_team_report(
    *,
    candidates: list[Mapping[str, Any]] | None = None,
    candidate: Mapping[str, Any] | None = None,
    historical_records: list[Mapping[str, Any]] | None = None,
    labeled_records: list[Mapping[str, Any]] | None = None,
    calibration_records: list[Mapping[str, Any]] | None = None,
    sequences: Mapping[str, Any] | None = None,
    provider: str | None = None,
    persist_report: bool = True,
    base_data_dir: str | None = None,
    max_items: int = 25,
) -> dict[str, Any]:
    created_at = utc_now_iso()
    rows = [dict(row) for row in (candidates or []) if isinstance(row, Mapping)]
    if candidate:
        rows = [dict(candidate)] + rows
    cap = max(1, min(int(max_items or 25), 100))
    diagnostics = [
        run_advanced_shape_diagnostics(
            row,
            historical_records=historical_records,
            labeled_records=labeled_records,
            calibration_records=calibration_records,
            sequences=sequences,
            provider=provider,
        )
        for row in rows[:cap]
    ]
    report_id = f"advanced_red_team_{safe_run_id('advanced_red_team', created_at + str(len(diagnostics)))}"
    fake_edge_count = sum(1 for row in diagnostics if "static_correlation_not_predictive" in list(row.get("no_bet_reasons") or []))
    data_insufficient_count = sum(1 for row in diagnostics if bool(row.get("insufficient_sample")))
    report = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "status": "advanced_red_team_report",
        "report_id": report_id,
        "date": created_at[:10],
        "created_at": created_at,
        "candidate_count": len(diagnostics),
        "provider": provider,
        "deepseek_used": any(bool(row.get("deepseek_used")) for row in diagnostics),
        "openai_used": any(bool(row.get("openai_used")) for row in diagnostics),
        "external_ai_call_performed": False,
        "fake_edge_warning_count": fake_edge_count,
        "data_insufficient_count": data_insufficient_count,
        "fatal_safety_blocker_count": sum(1 for row in diagnostics if bool(row.get("fatal_safety_blocker"))),
        "no_bet_reason_counts": _reason_counts(diagnostics, "no_bet_reasons"),
        "no_trade_reason_counts": _reason_counts(diagnostics, "no_trade_reasons"),
        "missing_input_counts": _reason_counts(diagnostics, "missing_inputs"),
        "recommended_action_adjustment_counts": {
            key: sum(1 for row in diagnostics if row.get("recommended_action_adjustment") == key)
            for key in ["NONE", "LOWER_CONFIDENCE", "DATA_INSUFFICIENT", "NO_BET", "NO_TRADE"]
        },
        "items": diagnostics,
        "red_team_only": True,
        **secret_safety_fields(source_payload={"candidate": candidate, "candidates": candidates}, redacted_payload={"items": diagnostics}),
        **locked_safety_flags(),
    }
    if persist_report:
        report["persistence"] = write_advanced_red_team_report(report, base_data_dir=base_data_dir)
        write_advanced_diagnostics({"items": diagnostics, "created_at": created_at, "red_team_only": True, **locked_safety_flags()}, base_data_dir=base_data_dir)
    return redact_sensitive(report)
