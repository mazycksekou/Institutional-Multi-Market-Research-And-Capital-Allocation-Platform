"""Experiment History Store – Phase 10H17.

Persists ablation and calibration run results so operators can compare
experiments over time.

No schema changes to existing tables.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from automation_scheduler.feature_ablation_lab import (
    ABLATION_NEVER_FEATURE_FIELDS,
)

EXPERIMENT_HISTORY_STORE_VERSION: str = "10H17"


def _utc_now_iso() -> str:
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _short_uuid() -> str:
    return uuid.uuid4().hex[:8]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        f = float(value)
        if not (f != f):
            return f
        return default
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

EXPERIMENT_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiment_history_runs (
    run_id TEXT PRIMARY KEY NOT NULL,
    created_at TEXT NOT NULL,
    run_type TEXT NOT NULL,
    run_label TEXT,
    notes TEXT,
    mode TEXT,
    sport_key TEXT,
    market_family TEXT,
    selected_groups_json TEXT,
    selected_fields_json TEXT,
    removed_fields_json TEXT,
    active_fields_json TEXT,
    included_sports_json TEXT,
    excluded_sports_json TEXT,
    included_market_families_json TEXT,
    excluded_market_families_json TEXT,
    performance_json TEXT,
    roi_by_sport_json TEXT,
    roi_by_market_family_json TEXT,
    warnings_json TEXT,
    config_json TEXT,
    result_json TEXT,
    total_rows INTEGER,
    included_row_count INTEGER,
    excluded_row_count INTEGER,
    eligible_rows INTEGER,
    skipped_rows INTEGER,
    settled_count INTEGER,
    wins INTEGER,
    losses INTEGER,
    pushes INTEGER,
    net_result REAL,
    roi_percent REAL,
    win_rate_percent REAL
);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def initialize_experiment_history_store(db_path: str | Path) -> dict[str, Any]:
    """Create experiment_history_runs table if missing.

    Returns stable status dict.
    """
    db_path_str = str(db_path)
    try:
        conn = sqlite3.connect(db_path_str)
        conn.execute(EXPERIMENT_HISTORY_SCHEMA)
        conn.commit()
        conn.close()
    except Exception as exc:
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "table": "experiment_history_runs",
            "status": "error",
            "warnings": [f"Could not initialize history store: {exc}"],
        }
    return {
        "ok": True,
        "version": EXPERIMENT_HISTORY_STORE_VERSION,
        "table": "experiment_history_runs",
        "status": "created_or_exists",
        "warnings": [],
    }


def normalize_experiment_history_run_type(value: Any) -> str:
    """Return allowed run type or default."""
    val = _safe_str(value)
    if val in ("feature_ablation", "calibration_strategy_filter"):
        return val
    return "feature_ablation"


def make_experiment_run_id(prefix: str | None = None) -> str:
    """Create a stable unique run ID.

    Example: exp_20260101T120000Z_ab12cd34
    """
    ts = _utc_now_iso().replace(":", "").replace("-", "")
    short = _short_uuid()
    pfx = _safe_str(prefix) if prefix else "exp"
    return f"{pfx}_{ts}_{short}"


def extract_experiment_history_metrics(result: Mapping[str, Any]) -> dict[str, Any]:
    """Pull stable metric fields from an ablation/calibration result.

    Returns a dict with all expected numeric/JSON keys.
    """
    perf = dict(result.get("performance") or result)

    total_rows = _safe_int(perf.get("total_rows"))
    included = _safe_int(perf.get("included_row_count"))
    excluded = _safe_int(perf.get("excluded_row_count"))
    eligible = _safe_int(perf.get("eligible_rows"))
    skipped = _safe_int(perf.get("skipped_rows"))
    settled = _safe_int(perf.get("settled_count"))
    wins = _safe_int(perf.get("wins"))
    losses = _safe_int(perf.get("losses"))
    pushes = _safe_int(perf.get("pushes"))
    net = _safe_float(perf.get("net_result"))
    roi = _safe_float(perf.get("roi_percent"))
    win_rate = _safe_float(perf.get("win_rate_percent"))

    roi_by_sport = dict(perf.get("roi_by_sport") or {})
    roi_by_market = dict(perf.get("roi_by_market_family") or {})
    warnings_raw = list(perf.get("warnings") or result.get("warnings") or [])

    return {
        "total_rows": total_rows,
        "included_row_count": included,
        "excluded_row_count": excluded,
        "eligible_rows": eligible,
        "skipped_rows": skipped,
        "settled_count": settled,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "net_result": round(net, 2),
        "roi_percent": round(roi, 2),
        "win_rate_percent": round(win_rate, 2),
        "roi_by_sport": roi_by_sport,
        "roi_by_market_family": roi_by_market,
        "warnings": warnings_raw,
    }


def sanitize_experiment_history_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON‑safe copy, never mutating the input.

    Ensures active_fields does not contain leakage fields.
    """
    import copy

    safe = copy.deepcopy(dict(result))

    never_set = set(ABLATION_NEVER_FEATURE_FIELDS)

    active = list(safe.get("active_fields") or [])
    removed = []
    for f in active:
        if f in never_set:
            removed.append(f)
    if removed:
        safe["active_fields"] = [f for f in active if f not in never_set]
        safe.setdefault("warnings", []).append(
            f"Removed leakage fields from active_fields: {', '.join(removed)}"
        )

    # ensure warnings is a list
    warnings = list(safe.get("warnings") or [])
    safe["warnings"] = warnings

    # json-safe stringification for any nested fields that may contain non‑serializable
    for key in (
        "selected_groups",
        "selected_fields",
        "removed_fields",
        "active_fields",
        "included_sports",
        "excluded_sports",
        "included_market_families",
        "excluded_market_families",
        "roi_by_sport",
        "roi_by_market_family",
        "warnings",
    ):
        val = safe.get(key)
        if isinstance(val, (list, dict)):
            safe[f"{key}_json"] = json.dumps(val, ensure_ascii=False, sort_keys=True, default=str)
        else:
            safe.setdefault(f"{key}_json", json.dumps([]))

    return safe


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


def save_experiment_history_run(
    db_path: str | Path,
    result: Mapping[str, Any],
    run_type: str = "feature_ablation",
    run_label: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Insert one experiment run into the history store.

    Initializes table if needed.
    Returns stable dict with run_id.
    """
    init = initialize_experiment_history_store(db_path)
    if not init.get("ok"):
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "run_id": "",
            "saved": False,
            "warnings": init.get("warnings", ["Table creation failed"]),
        }

    sanitized = sanitize_experiment_history_result(result)
    metrics = extract_experiment_history_metrics(result)

    run_id = make_experiment_run_id()
    created_at = _utc_now_iso()
    rtype = normalize_experiment_history_run_type(run_type)

    mode = _safe_str(result.get("mode"))
    sport_key = _safe_str(result.get("sport_key"))
    market_family = _safe_str(result.get("market_family"))

    # JSON text columns
    def _to_json(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return json.dumps([])

    selected_groups_json = _to_json(result.get("selected_groups", []))
    selected_fields_json = _to_json(result.get("selected_fields", []))
    removed_fields_json = _to_json(result.get("removed_fields", []))
    active_fields_json = _to_json(result.get("active_fields", []))
    included_sports_json = _to_json(result.get("included_sports", []))
    excluded_sports_json = _to_json(result.get("excluded_sports", []))
    included_market_families_json = _to_json(result.get("included_market_families", []))
    excluded_market_families_json = _to_json(result.get("excluded_market_families", []))
    performance_json = _to_json(result.get("performance", {}))
    roi_by_sport_json = _to_json(metrics.get("roi_by_sport", {}))
    roi_by_market_family_json = _to_json(metrics.get("roi_by_market_family", {}))
    warnings_json = _to_json(metrics.get("warnings", []))
    config_json = _to_json(result.get("config", {}))
    result_json = _to_json(result)

    total_rows = metrics["total_rows"]
    included_row_count = metrics["included_row_count"]
    excluded_row_count = metrics["excluded_row_count"]
    eligible_rows = metrics["eligible_rows"]
    skipped_rows = metrics["skipped_rows"]
    settled_count = metrics["settled_count"]
    wins = metrics["wins"]
    losses = metrics["losses"]
    pushes = metrics["pushes"]
    net_result = metrics["net_result"]
    roi_percent = metrics["roi_percent"]
    win_rate_percent = metrics["win_rate_percent"]

    sql = """
        INSERT INTO experiment_history_runs (
            run_id, created_at, run_type, run_label, notes,
            mode, sport_key, market_family,
            selected_groups_json, selected_fields_json, removed_fields_json,
            active_fields_json,
            included_sports_json, excluded_sports_json,
            included_market_families_json, excluded_market_families_json,
            performance_json, roi_by_sport_json, roi_by_market_family_json,
            warnings_json, config_json, result_json,
            total_rows, included_row_count, excluded_row_count,
            eligible_rows, skipped_rows,
            settled_count, wins, losses, pushes,
            net_result, roi_percent, win_rate_percent
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?,
            ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?
        )
    """

    params = (
        run_id,
        created_at,
        rtype,
        run_label,
        notes,
        mode,
        sport_key,
        market_family,
        selected_groups_json,
        selected_fields_json,
        removed_fields_json,
        active_fields_json,
        included_sports_json,
        excluded_sports_json,
        included_market_families_json,
        excluded_market_families_json,
        performance_json,
        roi_by_sport_json,
        roi_by_market_family_json,
        warnings_json,
        config_json,
        result_json,
        total_rows,
        included_row_count,
        excluded_row_count,
        eligible_rows,
        skipped_rows,
        settled_count,
        wins,
        losses,
        pushes,
        net_result,
        roi_percent,
        win_rate_percent,
    )

    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute(sql, params)
        conn.commit()
        conn.close()
    except Exception as exc:
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "run_id": run_id,
            "created_at": created_at,
            "run_type": rtype,
            "run_label": run_label,
            "saved": False,
            "warnings": [f"Could not save run: {exc}"],
        }

    return {
        "ok": True,
        "version": EXPERIMENT_HISTORY_STORE_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "run_type": rtype,
        "run_label": run_label,
        "saved": True,
        "warnings": [],
    }


def list_experiment_history_runs(
    db_path: str | Path,
    limit: int = 100,
    run_type: str | None = None,
    mode: str | None = None,
    sport: str | None = None,
    market: str | None = None,
) -> dict[str, Any]:
    """Return recent runs, newest first.

    Returns compact row summaries.
    """
    init = initialize_experiment_history_store(db_path)
    if not init.get("ok"):
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "runs": [],
            "total": 0,
            "warnings": init.get("warnings", []),
        }

    where_clauses: list[str] = []
    params: list[Any] = []
    if run_type:
        where_clauses.append("run_type = ?")
        params.append(run_type)
    if mode:
        where_clauses.append("mode = ?")
        params.append(mode)
    if sport:
        where_clauses.append("sport_key = ?")
        params.append(sport)
    if market:
        where_clauses.append("market_family = ?")
        params.append(market)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT
            run_id, created_at, run_type, run_label,
            mode, sport_key, market_family,
            total_rows, included_row_count, excluded_row_count,
            eligible_rows, skipped_rows,
            settled_count, wins, losses, pushes,
            net_result, roi_percent, win_rate_percent,
            warnings_json
        FROM experiment_history_runs
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(limit)

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
    except Exception as exc:
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "runs": [],
            "total": 0,
            "warnings": [f"Could not query history: {exc}"],
        }

    runs: list[dict[str, Any]] = []
    for row in rows:
        warnings_list: list[str] = []
        raw_w = row["warnings_json"]
        if raw_w:
            try:
                parsed = json.loads(raw_w)
                if isinstance(parsed, list):
                    warnings_list = parsed
            except (json.JSONDecodeError, TypeError):
                warnings_list = [str(raw_w)]

        runs.append(
            {
                "run_id": row["run_id"],
                "created_at": row["created_at"],
                "run_type": row["run_type"],
                "run_label": row["run_label"],
                "mode": row["mode"],
                "sport_key": row["sport_key"],
                "market_family": row["market_family"],
                "total_rows": row["total_rows"],
                "included_row_count": row["included_row_count"],
                "excluded_row_count": row["excluded_row_count"],
                "eligible_rows": row["eligible_rows"],
                "skipped_rows": row["skipped_rows"],
                "settled_count": row["settled_count"],
                "wins": row["wins"],
                "losses": row["losses"],
                "pushes": row["pushes"],
                "net_result": row["net_result"],
                "roi_percent": row["roi_percent"],
                "win_rate_percent": row["win_rate_percent"],
                "warnings": warnings_list,
            }
        )

    return {
        "ok": True,
        "version": EXPERIMENT_HISTORY_STORE_VERSION,
        "runs": runs,
        "total": len(runs),
        "warnings": [],
    }


def get_experiment_history_run(
    db_path: str | Path,
    run_id: str,
) -> dict[str, Any]:
    """Return full saved result for one run.

    Returns not_found result if missing.
    """
    init = initialize_experiment_history_store(db_path)
    if not init.get("ok"):
        return {
            "ok": False,
            "found": False,
            "run": {},
            "warnings": init.get("warnings", []),
        }

    sql = """
        SELECT * FROM experiment_history_runs WHERE run_id = ?
    """
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, (run_id,)).fetchone()
        conn.close()
    except Exception as exc:
        return {
            "ok": False,
            "found": False,
            "run": {},
            "warnings": [f"Could not query run: {exc}"],
        }

    if row is None:
        return {
            "ok": True,
            "found": False,
            "run": {},
            "warnings": [f"Run {run_id} not found."],
        }

    run: dict[str, Any] = {}
    for key in row.keys():
        val = row[key]
        # decode JSON text columns
        if key.endswith("_json") and isinstance(val, str):
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
        run[key] = val

    return {
        "ok": True,
        "found": True,
        "run": run,
        "warnings": [],
    }


def compare_experiment_history_runs(
    db_path: str | Path,
    run_ids: Sequence[str],
) -> dict[str, Any]:
    """Compare 1 or more runs using the first as baseline.

    Returns deltas for numeric metrics.
    """
    if not run_ids:
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "baseline_run_id": None,
            "runs": [],
            "comparison_rows": [],
            "warnings": ["No run IDs provided."],
        }

    first_result = get_experiment_history_run(db_path, run_ids[0])
    if not first_result.get("found"):
        return {
            "ok": False,
            "version": EXPERIMENT_HISTORY_STORE_VERSION,
            "baseline_run_id": run_ids[0],
            "runs": [],
            "comparison_rows": [],
            "warnings": [f"Baseline run {run_ids[0]} not found."],
        }

    baseline = first_result.get("run", {})
    baseline_net = _safe_float(baseline.get("net_result"))
    baseline_roi = _safe_float(baseline.get("roi_percent"))
    baseline_win_rate = _safe_float(baseline.get("win_rate_percent"))
    baseline_inc = _safe_int(baseline.get("included_row_count"))

    runs_detail: list[dict] = []
    comparison_rows: list[dict] = []

    for rid in run_ids:
        current_result = get_experiment_history_run(db_path, rid)
        if not current_result.get("found"):
            continue
        cur = current_result.get("run", {})
        runs_detail.append(cur)

        row = {
            "run_id": cur.get("run_id"),
            "run_label": cur.get("run_label"),
            "run_type": cur.get("run_type"),
            "mode": cur.get("mode"),
            "sport_key": cur.get("sport_key"),
            "market_family": cur.get("market_family"),
            "active_field_count": len(
                cur.get("active_fields_json", [])
                if isinstance(cur.get("active_fields_json"), list)
                else (json.loads(cur.get("active_fields_json", "[]")) if isinstance(cur.get("active_fields_json"), str) else [])
            ),
            "removed_field_count": len(
                cur.get("removed_fields_json", [])
                if isinstance(cur.get("removed_fields_json"), list)
                else (json.loads(cur.get("removed_fields_json", "[]")) if isinstance(cur.get("removed_fields_json"), str) else [])
            ),
            "included_row_count": _safe_int(cur.get("included_row_count")),
            "excluded_row_count": _safe_int(cur.get("excluded_row_count")),
            "eligible_rows": _safe_int(cur.get("eligible_rows")),
            "skipped_rows": _safe_int(cur.get("skipped_rows")),
            "settled_count": _safe_int(cur.get("settled_count")),
            "net_result": _safe_float(cur.get("net_result")),
            "roi_percent": _safe_float(cur.get("roi_percent")),
            "win_rate_percent": _safe_float(cur.get("win_rate_percent")),
            "roi_delta_vs_baseline": round(
                _safe_float(cur.get("roi_percent")) - baseline_roi, 2
            ),
            "win_rate_delta_vs_baseline": round(
                _safe_float(cur.get("win_rate_percent")) - baseline_win_rate, 2
            ),
            "included_row_delta_vs_baseline": _safe_int(cur.get("included_row_count")) - baseline_inc,
        }
        comparison_rows.append(row)

    warnings: list[str] = []
    if len(comparison_rows) < len(run_ids):
        warnings.append("Some run IDs could not be resolved.")

    return {
        "ok": True,
        "version": EXPERIMENT_HISTORY_STORE_VERSION,
        "baseline_run_id": run_ids[0],
        "runs": runs_detail,
        "comparison_rows": comparison_rows,
        "warnings": warnings,
    }
