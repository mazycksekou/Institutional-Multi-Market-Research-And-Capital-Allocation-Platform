from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .feature_control import ABLATION_NEVER_FEATURE_FIELDS


EXPERIMENT_HISTORY_STORE_VERSION = "src.research.v1.experiment_history_store.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_experiment_history_store(db_path: str | Path) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_history_runs (
                run_id TEXT PRIMARY KEY,
                run_type TEXT NOT NULL,
                run_label TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                result_json TEXT NOT NULL,
                active_fields_json TEXT,
                performance_json TEXT,
                metrics_json TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "created_or_exists", "table": "experiment_history_runs"}


def normalize_experiment_history_run_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"feature_ablation", "calibration_strategy_filter"}:
        return text
    return "feature_ablation"


def make_experiment_run_id(prefix: str | None = None) -> str:
    return f"{prefix or 'exp'}_{uuid.uuid4().hex[:12]}"


def extract_experiment_history_metrics(result: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    performance = dict(payload.get("performance") or {})
    metrics = {
        "total_rows": int(performance.get("total_rows", payload.get("total_rows", 0)) or 0),
        "included_row_count": int(performance.get("included_row_count", payload.get("included_row_count", 0)) or 0),
        "excluded_row_count": int(performance.get("excluded_row_count", payload.get("excluded_row_count", 0)) or 0),
        "eligible_rows": int(performance.get("eligible_rows", payload.get("eligible_rows", 0)) or 0),
        "skipped_rows": int(performance.get("skipped_rows", payload.get("skipped_rows", 0)) or 0),
        "settled_count": int(performance.get("settled_count", payload.get("settled_count", 0)) or 0),
        "wins": int(performance.get("wins", payload.get("wins", 0)) or 0),
        "losses": int(performance.get("losses", payload.get("losses", 0)) or 0),
        "pushes": int(performance.get("pushes", payload.get("pushes", 0)) or 0),
        "net_result": float(performance.get("net_result", payload.get("net_result", 0.0)) or 0.0),
        "roi_percent": float(performance.get("roi_percent", payload.get("roi_percent", 0.0)) or 0.0),
        "win_rate_percent": float(performance.get("win_rate_percent", payload.get("win_rate_percent", 0.0)) or 0.0),
        "roi_by_sport": dict(performance.get("roi_by_sport") or {}),
        "roi_by_market_family": dict(performance.get("roi_by_market_family") or {}),
        "warnings": list(payload.get("warnings") or performance.get("warnings") or []),
    }
    return metrics


def sanitize_experiment_history_result(result: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    active_fields = [field for field in payload.get("active_fields", []) if field not in ABLATION_NEVER_FEATURE_FIELDS]
    warnings = list(payload.get("warnings") or [])
    if len(active_fields) != len(list(payload.get("active_fields", []))):
        warnings.append("leakage_fields_removed")
    payload["active_fields"] = active_fields
    payload["warnings"] = warnings
    return payload


def save_experiment_history_run(
    db_path: str | Path,
    result: Mapping[str, Any],
    *,
    run_type: str | None = None,
    run_label: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    initialize_experiment_history_store(db_path)
    payload = sanitize_experiment_history_result(result)
    run_type = normalize_experiment_history_run_type(run_type or payload.get("run_type"))
    run_id = make_experiment_run_id()
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO experiment_history_runs (
                run_id, run_type, run_label, notes, created_at, result_json,
                active_fields_json, performance_json, metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                run_type,
                run_label,
                notes,
                _utc_now_iso(),
                json.dumps(payload, sort_keys=True),
                json.dumps(payload.get("active_fields", []), sort_keys=True),
                json.dumps(payload.get("performance", {}), sort_keys=True),
                json.dumps(extract_experiment_history_metrics(payload), sort_keys=True),
            ],
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": True,
        "saved": True,
        "run_id": run_id,
        "run_type": run_type,
        "run_label": run_label,
        "notes": notes,
    }


def list_experiment_history_runs(
    db_path: str | Path,
    *,
    limit: int = 10,
    run_type: str | None = None,
    mode: str | None = None,
    sport: str | None = None,
    market: str | None = None,
) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM experiment_history_runs ORDER BY created_at DESC, run_id DESC LIMIT ?",
            [max(0, int(limit))],
        ).fetchall()
    except sqlite3.DatabaseError:
        rows = []
    finally:
        conn.close()
    runs = [dict(row) for row in rows]
    if run_type is not None:
        runs = [run for run in runs if str(run.get("run_type") or "").lower() == str(run_type).lower()]
    return {"ok": True, "runs": runs, "total": len(runs)}


def get_experiment_history_run(db_path: str | Path, run_id: str) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT * FROM experiment_history_runs WHERE run_id = ?", [run_id]).fetchone()
    except sqlite3.DatabaseError:
        row = None
    finally:
        conn.close()
    if row is None:
        return {"ok": True, "found": False, "warnings": ["run not found"], "run": None}
    payload = dict(row)
    if payload.get("active_fields_json"):
        try:
            payload["active_fields_json"] = json.loads(payload["active_fields_json"])
        except json.JSONDecodeError:
            pass
    if payload.get("performance_json"):
        try:
            payload["performance_json"] = json.loads(payload["performance_json"])
        except json.JSONDecodeError:
            pass
    if payload.get("metrics_json"):
        try:
            payload["metrics_json"] = json.loads(payload["metrics_json"])
        except json.JSONDecodeError:
            pass
    return {"ok": True, "found": True, "warnings": [], "run": payload}


def compare_experiment_history_runs(db_path: str | Path, run_ids: Sequence[str]) -> dict[str, Any]:
    run_ids = [str(run_id) for run_id in run_ids if str(run_id).strip()]
    if not run_ids:
        return {"ok": False, "warnings": ["no run ids provided"], "comparison_rows": []}
    runs = [get_experiment_history_run(db_path, run_id)["run"] for run_id in run_ids]
    runs = [run for run in runs if run]
    if not runs:
        return {"ok": False, "warnings": ["no runs found"], "comparison_rows": []}
    baseline = dict(runs[0])
    base_metrics = dict(baseline.get("metrics_json") or baseline.get("performance_json") or {})
    comparison_rows: list[dict[str, Any]] = []
    for run in runs:
        metrics = dict(run.get("metrics_json") or run.get("performance_json") or {})
        roi_delta = float(metrics.get("roi_percent", 0.0)) - float(base_metrics.get("roi_percent", 0.0))
        win_rate_delta = float(metrics.get("win_rate_percent", 0.0)) - float(base_metrics.get("win_rate_percent", 0.0))
        included_delta = int(metrics.get("included_row_count", 0)) - int(base_metrics.get("included_row_count", 0))
        comparison_rows.append(
            {
                "run_id": run.get("run_id"),
                "run_label": run.get("run_label"),
                "roi_delta_vs_baseline": round(roi_delta, 2),
                "win_rate_delta_vs_baseline": round(win_rate_delta, 2),
                "included_row_delta_vs_baseline": included_delta,
            }
        )
    return {"ok": True, "comparison_rows": comparison_rows, "warnings": []}


def normalize_report_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def format_report_percent(value: Any) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip().replace("%", "")
    try:
        return f"{float(text):.2f}%"
    except ValueError:
        return str(value)


def format_report_money(value: Any) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip().replace("$", "").replace(",", "")
    try:
        return f"{float(text):.2f}"
    except ValueError:
        return str(value)


def build_experiment_report_sections(run: Mapping[str, Any]) -> dict[str, Any]:
    from src.research.experiment_report_exporter import (
        build_experiment_report_sections as legacy_build_experiment_report_sections,
    )

    return legacy_build_experiment_report_sections(run)


def render_experiment_report_markdown(run: Mapping[str, Any]) -> dict[str, Any]:
    from src.research.experiment_report_exporter import (
        render_experiment_report_markdown as legacy_render_experiment_report_markdown,
    )

    return legacy_render_experiment_report_markdown(run)


def build_experiment_report_export(
    db_path: str | Path,
    run_id: str,
    *,
    export_format: str = "markdown",
) -> dict[str, Any]:
    from src.research.experiment_report_exporter import (
        build_experiment_report_export as legacy_build_experiment_report_export,
    )

    return legacy_build_experiment_report_export(
        db_path,
        run_id,
        export_format=export_format,
    )


def get_experiment_history_snapshot_for_dashboard(
    db_path: str | Path,
    limit: int = 50,
    run_type: str | None = None,
    mode: str | None = None,
    sport: str | None = None,
    market: str | None = None,
) -> dict[str, Any]:
    try:
        listing = list_experiment_history_runs(
            db_path,
            limit=limit,
            run_type=run_type,
            mode=mode,
            sport=sport,
            market=market,
        )
    except Exception as exc:
        return {
            "ok": False,
            "version": "10H17",
            "runs": [],
            "total": 0,
            "warnings": [f"Could not retrieve history: {exc}"],
        }
    return {
        "ok": listing.get("ok", True),
        "version": listing.get("version", "10H17"),
        "runs": listing.get("runs", []),
        "total": listing.get("total", 0),
        "warnings": listing.get("warnings", []),
    }


def save_experiment_history_run_for_dashboard(
    db_path: str | Path,
    result: Mapping[str, Any],
    run_type: str = "feature_ablation",
    run_label: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    try:
        saved = save_experiment_history_run(
            db_path,
            result,
            run_type=run_type,
            run_label=run_label,
            notes=notes,
        )
    except Exception as exc:
        return {
            "ok": False,
            "version": "10H17",
            "run_id": "",
            "saved": False,
            "warnings": [f"Could not save experiment: {exc}"],
        }
    return {
        "ok": saved.get("ok", True),
        "version": saved.get("version", "10H17"),
        "run_id": saved.get("run_id", ""),
        "run_type": saved.get("run_type", run_type),
        "run_label": saved.get("run_label"),
        "saved": saved.get("saved", False),
        "warnings": saved.get("warnings", []),
    }


def compare_experiment_history_runs_for_dashboard(
    db_path: str | Path,
    run_ids: Sequence[str],
) -> dict[str, Any]:
    try:
        comp = compare_experiment_history_runs(db_path, run_ids)
    except Exception as exc:
        return {
            "ok": False,
            "version": "10H17",
            "baseline_run_id": None,
            "runs": [],
            "comparison_rows": [],
            "warnings": [f"Could not compare runs: {exc}"],
        }
    return {
        "ok": comp.get("ok", True),
        "version": comp.get("version", "10H17"),
        "baseline_run_id": comp.get("baseline_run_id"),
        "runs": comp.get("runs", []),
        "comparison_rows": comp.get("comparison_rows", []),
        "warnings": comp.get("warnings", []),
    }


def get_experiment_report_export_for_dashboard(
    db_path: str | Path,
    run_id: str,
    export_format: str = "markdown",
) -> dict[str, Any]:
    try:
        export = build_experiment_report_export(
            str(db_path), run_id, export_format=export_format
        )
    except Exception as exc:
        return {
            "ok": False,
            "version": "10H18",
            "run_id": run_id,
            "export_format": export_format,
            "filename": "",
            "content": "",
            "markdown": "",
            "warnings": [f"export error: {exc}"],
        }
    return {
        "ok": export.get("ok", False),
        "version": export.get("version", "10H18"),
        "run_id": export.get("run_id", run_id),
        "export_format": export.get("export_format", export_format),
        "filename": export.get("filename", ""),
        "content": export.get("content", ""),
        "markdown": export.get("markdown", ""),
        "warnings": export.get("warnings", []),
    }


__all__ = [
    "ABLATION_NEVER_FEATURE_FIELDS",
    "EXPERIMENT_HISTORY_STORE_VERSION",
    "build_experiment_report_export",
    "compare_experiment_history_runs_for_dashboard",
    "build_experiment_report_sections",
    "compare_experiment_history_runs",
    "extract_experiment_history_metrics",
    "format_report_money",
    "format_report_percent",
    "get_experiment_history_snapshot_for_dashboard",
    "get_experiment_history_run",
    "get_experiment_report_export_for_dashboard",
    "initialize_experiment_history_store",
    "list_experiment_history_runs",
    "make_experiment_run_id",
    "normalize_experiment_history_run_type",
    "normalize_report_value",
    "render_experiment_report_markdown",
    "sanitize_experiment_history_result",
    "save_experiment_history_run_for_dashboard",
    "save_experiment_history_run",
]
