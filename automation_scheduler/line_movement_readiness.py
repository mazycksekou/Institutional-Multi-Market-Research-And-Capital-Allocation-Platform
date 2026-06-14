"""
Phase 10H19 – Historical Line Movement Readiness Layer.

Readiness inspection for the local SQLite historical_line_snapshots table.
No vendor connectors, no paid data imports, no scraping, no external API calls.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Phase marker
# ---------------------------------------------------------------------------

LINE_MOVEMENT_READINESS_VERSION: str = "10H19"

# ---------------------------------------------------------------------------
# Required columns for the historical_line_snapshots table
# ---------------------------------------------------------------------------

REQUIRED_LINE_MOVEMENT_COLUMNS: list[str] = [
    "snapshot_id",
    "event_id",
    "odds_id",
    "source_key",
    "source_file",
    "sport",
    "league",
    "event_date",
    "home_team",
    "away_team",
    "bookmaker",
    "market",
    "market_family",
    "selection",
    "player_name",
    "team_name",
    "line_value",
    "odds_value",
    "implied_probability",
    "snapshot_label",
    "snapshot_time",
    "raw_market_name",
    "raw_selection_name",
    "created_at",
    "updated_at",
]

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

SNIPPET_KEY_TRANSFORM: dict[type, str] = {}


def _safe_str(value: Any) -> str:
    """Convert *value* to a JSON‑safe string, never raising."""
    try:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (list, dict)):
            # keep as stable JSON string
            return json.dumps(value, sort_keys=True, default=str)
        return str(value)
    except Exception:
        return str(value)


normalize_line_movement_readiness_value = _safe_str

# ---------------------------------------------------------------------------
# Table introspection
# ---------------------------------------------------------------------------

def _try_connect(db_path: str | Path) -> tuple[sqlite3.Connection | None, list[str]]:
    """Attempt to open an SQLite connection.  Returns (conn, warnings)."""
    warnings: list[str] = []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("SELECT 1")
    except Exception as exc:
        return None, [f"sqlite_error: {exc}"]
    return conn, warnings


def _close_conn(conn: sqlite3.Connection | None) -> None:
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# get_sqlite_table_names
# ---------------------------------------------------------------------------


def get_sqlite_table_names(db_path: str | Path) -> dict[str, Any]:
    """Return a dict of table names present in the SQLite file.

    Returns keys: ok, version, tables, warnings.
    Missing / unreadable db returns ok=False and a warning.
    """
    if not db_path:
        return {"ok": False, "version": LINE_MOVEMENT_READINESS_VERSION,
                "tables": [], "warnings": ["missing_db_path"]}

    path = Path(db_path)
    if not path.exists():
        return {"ok": False, "version": LINE_MOVEMENT_READINESS_VERSION,
                "tables": [], "warnings": ["missing_db_file"]}

    conn, warnings = _try_connect(db_path)
    if conn is None:
        return {"ok": False, "version": LINE_MOVEMENT_READINESS_VERSION,
                "tables": [], "warnings": warnings}

    tables: list[str] = []
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        for row in cur:
            tables.append(str(row["name"]))
    except Exception as exc:
        warnings.append(f"sqlite_error reading table names: {exc}")
    finally:
        _close_conn(conn)

    return {
        "ok": True,
        "version": LINE_MOVEMENT_READINESS_VERSION,
        "tables": tables,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# get_sqlite_table_columns
# ---------------------------------------------------------------------------


def get_sqlite_table_columns(db_path: str | Path, table_name: str) -> dict[str, Any]:
    """Return columns of *table_name*.

    Safe: missing table returns ok=False and warning.
    """
    tables_info = get_sqlite_table_names(db_path)
    if not tables_info["ok"]:
        return {
            "ok": False,
            "version": LINE_MOVEMENT_READINESS_VERSION,
            "table_name": table_name,
            "columns": [],
            "warnings": tables_info.get("warnings", []),
        }

    if table_name not in tables_info["tables"]:
        return {
            "ok": False,
            "version": LINE_MOVEMENT_READINESS_VERSION,
            "table_name": table_name,
            "columns": [],
            "warnings": ["missing_table"],
        }

    conn, warnings = _try_connect(db_path)
    if conn is None:
        return {
            "ok": False,
            "version": LINE_MOVEMENT_READINESS_VERSION,
            "table_name": table_name,
            "columns": [],
            "warnings": warnings,
        }

    columns: list[str] = []
    try:
        cur = conn.execute(f"PRAGMA table_info([{table_name}])")
        for row in cur:
            columns.append(str(row["name"]))
    except Exception as exc:
        warnings.append(f"sqlite_error: {exc}")
    finally:
        _close_conn(conn)

    return {
        "ok": True,
        "version": LINE_MOVEMENT_READINESS_VERSION,
        "table_name": table_name,
        "columns": columns,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# inspect_line_movement_schema
# ---------------------------------------------------------------------------


def inspect_line_movement_schema(db_path: str | Path) -> dict[str, Any]:
    """Inspect whether the historical_line_snapshots table exists and has
    the required columns.

    Returns keys:
        ok, version, table_name, table_exists,
        required_columns, present_columns, missing_columns, extra_columns,
        schema_ready, warnings
    """
    result: dict[str, Any] = {
        "ok": True,
        "version": LINE_MOVEMENT_READINESS_VERSION,
        "table_name": "historical_line_snapshots",
        "table_exists": False,
        "required_columns": list(REQUIRED_LINE_MOVEMENT_COLUMNS),
        "present_columns": [],
        "missing_columns": [],
        "extra_columns": [],
        "schema_ready": False,
        "warnings": [],
    }

    tables_info = get_sqlite_table_names(db_path)
    if not tables_info["ok"]:
        result["ok"] = False
        result["warnings"] = tables_info.get("warnings", [])
        return result

    if "historical_line_snapshots" not in tables_info["tables"]:
        result["warnings"] = ["missing_table"]
        return result

    result["table_exists"] = True

    col_info = get_sqlite_table_columns(db_path, "historical_line_snapshots")
    if not col_info["ok"]:
        result["ok"] = False
        result["warnings"] = col_info.get("warnings", [])
        return result

    present = set(col_info["columns"])
    required_set = set(REQUIRED_LINE_MOVEMENT_COLUMNS)

    result["present_columns"] = sorted(present)
    result["missing_columns"] = sorted(required_set - present)
    result["extra_columns"] = sorted(present - required_set)

    if not result["missing_columns"]:
        result["schema_ready"] = True
    else:
        result["warnings"].append("missing_columns")

    return result


# ---------------------------------------------------------------------------
# build_line_movement_snapshot_coverage
# ---------------------------------------------------------------------------


def build_line_movement_snapshot_coverage(db_path: str | Path) -> dict[str, Any]:
    """Build coverage metrics from the historical_line_snapshots table.

    If schema is not ready, returns a stable dict with ok=False and metrics zeroed.
    """
    schema = inspect_line_movement_schema(db_path)
    if not schema["ok"] or not schema["schema_ready"]:
        return {
            "ok": False,
            "version": LINE_MOVEMENT_READINESS_VERSION,
            "total_snapshots": 0,
            "linked_snapshot_count": 0,
            "unlinked_snapshot_count": 0,
            "event_count": 0,
            "linked_event_count": 0,
            "sport_count": 0,
            "market_family_count": 0,
            "bookmaker_count": 0,
            "earliest_snapshot_time": None,
            "latest_snapshot_time": None,
            "earliest_event_date": None,
            "latest_event_date": None,
            "sports": [],
            "market_families": [],
            "bookmakers": [],
            "snapshot_labels": [],
            "warnings": schema.get("warnings", []),
        }

    conn, warnings = _try_connect(db_path)
    if conn is None:
        return {
            "ok": False,
            "version": LINE_MOVEMENT_READINESS_VERSION,
            "total_snapshots": 0,
            "linked_snapshot_count": 0,
            "unlinked_snapshot_count": 0,
            "event_count": 0,
            "linked_event_count": 0,
            "sport_count": 0,
            "market_family_count": 0,
            "bookmaker_count": 0,
            "earliest_snapshot_time": None,
            "latest_snapshot_time": None,
            "earliest_event_date": None,
            "latest_event_date": None,
            "sports": [],
            "market_families": [],
            "bookmakers": [],
            "snapshot_labels": [],
            "warnings": warnings,
        }

    coverage: dict[str, Any] = {
        "ok": True,
        "version": LINE_MOVEMENT_READINESS_VERSION,
        "total_snapshots": 0,
        "linked_snapshot_count": 0,
        "unlinked_snapshot_count": 0,
        "event_count": 0,
        "linked_event_count": 0,
        "sport_count": 0,
        "market_family_count": 0,
        "bookmaker_count": 0,
        "earliest_snapshot_time": None,
        "latest_snapshot_time": None,
        "earliest_event_date": None,
        "latest_event_date": None,
        "sports": [],
        "market_families": [],
        "bookmakers": [],
        "snapshot_labels": [],
        "warnings": warnings,
    }

    try:
        cur = conn.execute("SELECT COUNT(*) AS cnt FROM historical_line_snapshots")
        coverage["total_snapshots"] = cur.fetchone()["cnt"]
    except Exception as exc:
        warnings.append(f"snapshot count error: {exc}")

    # linked/unlinked
    try:
        cur = conn.execute(
            "SELECT COUNT(*) AS cnt FROM historical_line_snapshots "
            "WHERE event_id IS NOT NULL AND event_id != ''"
        )
        coverage["linked_snapshot_count"] = cur.fetchone()["cnt"]
    except Exception as exc:
        warnings.append(f"linked count error: {exc}")

    coverage["unlinked_snapshot_count"] = (
        coverage["total_snapshots"] - coverage["linked_snapshot_count"]
    )

    # distinct event count (non‑null)
    try:
        cur = conn.execute(
            "SELECT COUNT(DISTINCT event_id) AS cnt FROM historical_line_snapshots "
            "WHERE event_id IS NOT NULL AND event_id != ''"
        )
        coverage["event_count"] = cur.fetchone()["cnt"]
    except Exception as exc:
        warnings.append(f"event count error: {exc}")

    coverage["linked_event_count"] = coverage["event_count"]

    # distinct sports
    try:
        cur = conn.execute(
            "SELECT DISTINCT sport FROM historical_line_snapshots "
            "ORDER BY sport"
        )
        coverage["sports"] = [str(r["sport"]) for r in cur.fetchall()]
        coverage["sport_count"] = len(coverage["sports"])
    except Exception as exc:
        warnings.append(f"distinct sport error: {exc}")

    # distinct market_family
    try:
        cur = conn.execute(
            "SELECT DISTINCT market_family FROM historical_line_snapshots "
            "ORDER BY market_family"
        )
        coverage["market_families"] = [str(r["market_family"]) for r in cur.fetchall()]
        coverage["market_family_count"] = len(coverage["market_families"])
    except Exception as exc:
        warnings.append(f"distinct market_family error: {exc}")

    # distinct bookmaker
    try:
        cur = conn.execute(
            "SELECT DISTINCT bookmaker FROM historical_line_snapshots "
            "ORDER BY bookmaker"
        )
        coverage["bookmakers"] = [str(r["bookmaker"]) for r in cur.fetchall()]
        coverage["bookmaker_count"] = len(coverage["bookmakers"])
    except Exception as exc:
        warnings.append(f"distinct bookmaker error: {exc}")

    # snapshot_time extremes
    try:
        cur = conn.execute(
            "SELECT MIN(snapshot_time) AS min_t, MAX(snapshot_time) AS max_t "
            "FROM historical_line_snapshots "
            "WHERE snapshot_time IS NOT NULL AND snapshot_time != ''"
        )
        row = cur.fetchone()
        coverage["earliest_snapshot_time"] = row["min_t"] if row else None
        coverage["latest_snapshot_time"] = row["max_t"] if row else None
    except Exception as exc:
        warnings.append(f"snapshot_time error: {exc}")

    # event_date extremes
    try:
        cur = conn.execute(
            "SELECT MIN(event_date) AS min_d, MAX(event_date) AS max_d "
            "FROM historical_line_snapshots "
            "WHERE event_date IS NOT NULL AND event_date != ''"
        )
        row = cur.fetchone()
        coverage["earliest_event_date"] = row["min_d"] if row else None
        coverage["latest_event_date"] = row["max_d"] if row else None
    except Exception as exc:
        warnings.append(f"event_date error: {exc}")

    # snapshot_labels
    try:
        cur = conn.execute(
            "SELECT DISTINCT snapshot_label FROM historical_line_snapshots "
            "ORDER BY snapshot_label"
        )
        coverage["snapshot_labels"] = [str(r["snapshot_label"]) for r in cur.fetchall()]
    except Exception as exc:
        warnings.append(f"snapshot label error: {exc}")

    _close_conn(conn)
    coverage["warnings"] = warnings
    return coverage


# ---------------------------------------------------------------------------
# build_line_movement_readiness_snapshot
# ---------------------------------------------------------------------------


def build_line_movement_readiness_snapshot(db_path: str | Path) -> dict[str, Any]:
    """Combine schema inspection and coverage into a single readiness snapshot.

    Returns a stable dict with keys:
        ok, version, table_name, schema, coverage, readiness, warnings
    """
    schema = inspect_line_movement_schema(db_path)
    coverage = build_line_movement_snapshot_coverage(db_path)

    readiness: dict[str, Any] = {
        "ready": False,
        "schema_ready": schema.get("schema_ready", False),
        "has_snapshots": coverage.get("total_snapshots", 0) > 0,
        "has_linked_events": coverage.get("linked_snapshot_count", 0) > 0,
        "has_snapshot_time": coverage.get("earliest_snapshot_time") is not None,
        "has_market_family": coverage.get("market_family_count", 0) > 0,
        "has_bookmaker": coverage.get("bookmaker_count", 0) > 0,
        "reasons": [],
    }

    reasons: list[str] = []
    if not schema.get("schema_ready", False):
        reasons.append("missing_schema")
    if coverage.get("total_snapshots", 0) == 0:
        reasons.append("missing_snapshots")
    if coverage.get("linked_snapshot_count", 0) == 0:
        reasons.append("missing_linked_events")
    if coverage.get("earliest_snapshot_time") is None:
        reasons.append("missing_snapshot_time")
    if coverage.get("market_family_count", 0) == 0:
        reasons.append("missing_market_family")
    if coverage.get("bookmaker_count", 0) == 0:
        reasons.append("missing_bookmaker")

    readiness["reasons"] = reasons

    all_ready = (
        schema.get("schema_ready", False)
        and coverage.get("total_snapshots", 0) > 0
        and coverage.get("linked_snapshot_count", 0) > 0
        and coverage.get("earliest_snapshot_time") is not None
        and coverage.get("market_family_count", 0) > 0
        and coverage.get("bookmaker_count", 0) > 0
    )
    readiness["ready"] = all_ready

    warnings: list[str] = []

    if not schema.get("ok", True):
        warnings.extend(schema.get("warnings", []))
        warnings.append("Schema inspection failed; readiness may be incomplete.")

    return {
        "ok": True,
        "version": LINE_MOVEMENT_READINESS_VERSION,
        "table_name": "historical_line_snapshots",
        "schema": schema,
        "coverage": coverage,
        "readiness": readiness,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# describe_line_movement_readiness
# ---------------------------------------------------------------------------


def describe_line_movement_readiness(snapshot: dict[str, Any]) -> list[str]:
    """Return human‑readable operator messages based on the readiness snapshot."""
    if not snapshot.get("ok"):
        return ["Line movement readiness check could not run."]

    lines: list[str] = []
    schema = snapshot.get("schema", {})
    coverage = snapshot.get("coverage", {})
    readiness = snapshot.get("readiness", {})

    schema_ready = schema.get("schema_ready", False)
    if schema_ready:
        lines.append("Schema is ready: historical_line_snapshots table exists and all required columns are present.")
    else:
        missing = schema.get("missing_columns", [])
        lines.append(
            "Schema is NOT ready. "
            + (f"Missing columns: {', '.join(missing)}." if missing else "Table not found.")
        )

    total = coverage.get("total_snapshots", 0)
    lines.append(f"Snapshot count: {total}")
    lines.append(f"Linked event snapshots: {coverage.get('linked_snapshot_count', 0)}")
    lines.append(f"Unlinked snapshots: {coverage.get('unlinked_snapshot_count', 0)}")
    lines.append(f"Event count (linked): {coverage.get('event_count', 0)}")
    lines.append(f"Sport count: {coverage.get('sport_count', 0)}")
    lines.append(f"Market family count: {coverage.get('market_family_count', 0)}")
    lines.append(f"Bookmaker count: {coverage.get('bookmaker_count', 0)}")

    if coverage.get("earliest_snapshot_time"):
        lines.append(
            f"Snapshot time range: {coverage['earliest_snapshot_time']} → {coverage['latest_snapshot_time']}"
        )
    else:
        lines.append("No snapshot_time data available.")

    if readiness.get("ready"):
        lines.append("Line movement readiness: ready.")
    else:
        reasons = readiness.get("reasons", [])
        lines.append("Line movement readiness: NOT ready.")
        if reasons:
            lines.append("Reasons: " + ", ".join(reasons) + ".")

    lines.append(
        "This readiness check does not connect to vendors or import paid data."
    )
    lines.append(
        "Future as-of queries must filter snapshot_time <= hypothetical_bet_time "
        "to prevent look-ahead bias."
    )

    return lines
