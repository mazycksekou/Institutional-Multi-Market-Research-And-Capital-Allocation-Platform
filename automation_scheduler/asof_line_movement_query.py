"""
Phase 10H22 – As-Of Line Movement Query Engine.

Provides a read‑only, vendor‑neutral query engine that filters historical
line‑movement snapshots to only those whose snapshot_time ≤ hypothetical_bet_time,
preventing look‑ahead bias.

No SQL writes, no vendor connectors, no paid data, no scraping, no external API calls.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

# ---------------------------------------------------------------------------
# Phase marker
# ---------------------------------------------------------------------------

AS_OF_LINE_MOVEMENT_QUERY_VERSION: str = "10H22"

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def normalize_asof_line_movement_value(value: Any) -> str:
    """Convert any value to a stable normalized string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, set, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    s = str(value).strip()
    return s


def parse_asof_datetime(value: Any) -> datetime | None:
    """Parse a datetime string, returning an aware UTC datetime or None."""
    if value is None:
        return None
    s = normalize_asof_line_movement_value(value)
    if not s:
        return None

    # Try full ISO format first
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass

    # Try YYYY-MM-DD (no time)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        try:
            dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # Try YYYY-MM-DDTHH:MM:SS with optional Z/offset (already handled by fromisoformat)
    # fallback for stripped Z
    if s.endswith("Z"):
        candidate = s[:-1]
        try:
            dt = datetime.fromisoformat(candidate)
            dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            pass

    return None


def normalize_asof_date_time_label(value: Any) -> str:
    """Return a normalized ISO string or empty string if unparseable."""
    dt = parse_asof_datetime(value)
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Snapshot availability check
# ---------------------------------------------------------------------------


def is_snapshot_available_as_of(snapshot_time: Any, hypothetical_bet_time: Any) -> bool:
    """Return True only when both times parse and snapshot_time ≤ hypothetical_bet_time."""
    snapshot_dt = parse_asof_datetime(snapshot_time)
    bet_dt = parse_asof_datetime(hypothetical_bet_time)
    if snapshot_dt is None or bet_dt is None:
        return False
    return snapshot_dt <= bet_dt


# ---------------------------------------------------------------------------
# Group key builder
# ---------------------------------------------------------------------------


_DEFAULT_ASOF_GROUP_FIELDS = [
    "event_id",
    "bookmaker",
    "market_family",
    "market",
    "selection",
    "line_value",
]


def build_asof_snapshot_group_key(
    row: dict[str, Any],
    group_fields: Sequence[str] | None = None,
) -> str:
    """Deterministic group key from the given fields."""
    fields = list(group_fields) if group_fields else list(_DEFAULT_ASOF_GROUP_FIELDS)
    parts = [normalize_asof_line_movement_value(row.get(f, "")) for f in fields]
    return "|".join(parts)


# ---------------------------------------------------------------------------
# Filter snapshots as‑of
# ---------------------------------------------------------------------------


def filter_line_movement_snapshots_as_of(
    snapshots: Any,
    event_id: str | None = None,
    hypothetical_bet_time: Any = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
) -> dict[str, Any]:
    """Filter snapshots by event_id, time, and optional fields.

    Returns a stable dict.
    """
    version = AS_OF_LINE_MOVEMENT_QUERY_VERSION
    warnings: list[str] = []
    total = 0
    available = 0
    future = 0
    invalid = 0
    unmatched = 0
    filtered: list[dict[str, Any]] = []

    # Validate hypothetical_bet_time
    if hypothetical_bet_time is None:
        warnings.append("missing_hypothetical_bet_time")
        return {
            "ok": False,
            "version": version,
            "total_snapshots": 0,
            "available_snapshots": 0,
            "future_snapshots": 0,
            "invalid_time_snapshots": 0,
            "unmatched_snapshots": 0,
            "snapshots": [],
            "warnings": warnings,
        }

    # Ensure snapshots is iterable of dicts
    if not isinstance(snapshots, (list, tuple)):
        snapshots = []
        warnings.append("snapshots_not_list")

    for row in snapshots:
        if not isinstance(row, dict):
            unmatched += 1
            continue
        total += 1

        # event_id filter
        if event_id is not None:
            row_event = normalize_asof_line_movement_value(row.get("event_id"))
            if row_event != normalize_asof_line_movement_value(event_id):
                unmatched += 1
                continue

        # bookmaker filter
        if bookmaker is not None:
            row_book = normalize_asof_line_movement_value(row.get("bookmaker"))
            if row_book != normalize_asof_line_movement_value(bookmaker):
                unmatched += 1
                continue

        # market_family filter
        if market_family is not None:
            row_mf = normalize_asof_line_movement_value(row.get("market_family"))
            if row_mf != normalize_asof_line_movement_value(market_family):
                unmatched += 1
                continue

        # market filter
        if market is not None:
            row_mkt = normalize_asof_line_movement_value(row.get("market"))
            if row_mkt != normalize_asof_line_movement_value(market):
                unmatched += 1
                continue

        # selection filter
        if selection is not None:
            row_sel = normalize_asof_line_movement_value(row.get("selection"))
            if row_sel != normalize_asof_line_movement_value(selection):
                unmatched += 1
                continue

        # parse snapshot_time
        snapshot_time_str = row.get("snapshot_time")
        snapshot_dt = parse_asof_datetime(snapshot_time_str)
        if snapshot_dt is None:
            invalid += 1
            continue

        bet_dt = parse_asof_datetime(hypothetical_bet_time)
        if bet_dt is None:
            invalid += 1
            continue

        if snapshot_dt <= bet_dt:
            available += 1
            filtered.append(dict(row))
        else:
            future += 1

    return {
        "ok": True,
        "version": version,
        "total_snapshots": total,
        "available_snapshots": available,
        "future_snapshots": future,
        "invalid_time_snapshots": invalid,
        "unmatched_snapshots": unmatched,
        "snapshots": filtered,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Select latest snapshot per group
# ---------------------------------------------------------------------------


def select_latest_asof_snapshots(
    snapshots: Any,
    hypothetical_bet_time: Any,
    event_id: str | None = None,
    group_fields: Sequence[str] | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Filter and then for each group pick the snapshot with latest snapshot_time.

    Uses filter_line_movement_snapshots_as_of first.
    Returns stable dict.
    """
    version = AS_OF_LINE_MOVEMENT_QUERY_VERSION
    warnings: list[str] = []

    filtered_result = filter_line_movement_snapshots_as_of(
        snapshots,
        event_id=event_id,
        hypothetical_bet_time=hypothetical_bet_time,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
    )

    if filtered_result.get("warnings"):
        warnings.extend(filtered_result["warnings"])

    if not filtered_result.get("ok"):
        return {
            "ok": False,
            "version": version,
            "total_snapshots": 0,
            "available_snapshots": 0,
            "selected_snapshot_count": 0,
            "latest_snapshots": [],
            "excluded_counts": {},
            "warnings": warnings,
        }

    available_snapshots = filtered_result["snapshots"]
    # Build grouped dict
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in available_snapshots:
        key = build_asof_snapshot_group_key(row, group_fields=group_fields)
        groups.setdefault(key, []).append(row)

    latest_list: list[dict[str, Any]] = []
    for key, group_rows in groups.items():
        # sort by snapshot_time desc, then snapshot_id deterministic
        def _sort_key(r: dict[str, Any]) -> tuple:
            st = parse_asof_datetime(r.get("snapshot_time"))
            if st is None:
                st = datetime.min.replace(tzinfo=timezone.utc)
            sid = normalize_asof_line_movement_value(r.get("snapshot_id", ""))
            return (-st.timestamp(), sid)

        group_rows.sort(key=_sort_key)
        latest_list.append(group_rows[0])

    # sort the selected results by event_id
    latest_list.sort(key=lambda r: normalize_asof_line_movement_value(r.get("event_id", "")))

    selected_count = len(latest_list)
    # apply limit
    limited = latest_list[:limit]

    # excluded counts
    excluded = {
        "future_filtered": filtered_result.get("future_snapshots", 0),
        "invalid_time_filtered": filtered_result.get("invalid_time_snapshots", 0),
        "unmatched_filtered": filtered_result.get("unmatched_snapshots", 0),
    }

    return {
        "ok": True,
        "version": version,
        "total_snapshots": filtered_result.get("total_snapshots", 0),
        "available_snapshots": filtered_result.get("available_snapshots", 0),
        "selected_snapshot_count": selected_count,
        "latest_snapshots": limited,
        "excluded_counts": excluded,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Summarize
# ---------------------------------------------------------------------------


def summarize_asof_line_movement_snapshots(
    latest_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return summary of the selected latest snapshots."""
    version = AS_OF_LINE_MOVEMENT_QUERY_VERSION
    if not latest_snapshots:
        return {
            "ok": True,
            "version": version,
            "snapshot_count": 0,
            "sports": [],
            "market_families": [],
            "bookmakers": [],
            "snapshot_labels": [],
            "earliest_snapshot_time": "",
            "latest_snapshot_time": "",
            "warnings": ["no_snapshots"],
        }

    sports = set()
    market_families = set()
    bookmakers = set()
    snapshot_labels = set()
    times: list[str] = []

    for s in latest_snapshots:
        sp = normalize_asof_line_movement_value(s.get("sport"))
        if sp:
            sports.add(sp)
        mf = normalize_asof_line_movement_value(s.get("market_family"))
        if mf:
            market_families.add(mf)
        bk = normalize_asof_line_movement_value(s.get("bookmaker"))
        if bk:
            bookmakers.add(bk)
        sl = normalize_asof_line_movement_value(s.get("snapshot_label"))
        if sl:
            snapshot_labels.add(sl)
        tsp = s.get("snapshot_time")
        if tsp:
            times.append(normalize_asof_line_movement_value(tsp))

    earliest = min(times) if times else ""
    latest = max(times) if times else ""

    return {
        "ok": True,
        "version": version,
        "snapshot_count": len(latest_snapshots),
        "sports": sorted(sports),
        "market_families": sorted(market_families),
        "bookmakers": sorted(bookmakers),
        "snapshot_labels": sorted(snapshot_labels),
        "earliest_snapshot_time": earliest,
        "latest_snapshot_time": latest,
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Dashboard wrapper (in‑memory)
# ---------------------------------------------------------------------------


def build_asof_line_movement_query_snapshot(
    snapshots: Any = None,
    event_id: str | None = None,
    hypothetical_bet_time: Any = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    group_fields: Sequence[str] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Build a dashboard‑friendly query snapshot from in‑memory snapshots."""
    version = AS_OF_LINE_MOVEMENT_QUERY_VERSION
    messages = describe_asof_line_movement_query_engine()

    # Run select_latest
    selection_result = select_latest_asof_snapshots(
        snapshots=snapshots or [],
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        group_fields=group_fields,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )

    latest = selection_result.get("latest_snapshots", [])
    summary = summarize_asof_line_movement_snapshots(latest)

    # Ensure warnings
    warnings: list[str] = []
    warnings.extend(selection_result.get("warnings", []))
    warnings.extend(summary.get("warnings", []))

    return {
        "ok": selection_result.get("ok", False),
        "version": version,
        "query": selection_result,
        "selection": selection_result,
        "summary": summary,
        "messages": messages,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# SQLite read
# ---------------------------------------------------------------------------


def load_line_movement_snapshots_from_sqlite(
    db_path: str | Path,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Read historical_line_snapshots from SQLite read‑only.

    No writes, no schema changes.
    Returns stable dict.
    """
    version = AS_OF_LINE_MOVEMENT_QUERY_VERSION
    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as exc:
        return {
            "ok": False,
            "version": version,
            "total_snapshots": 0,
            "snapshots": [],
            "warnings": [f"cannot_open_database: {exc}"],
        }

    try:
        # check table exists
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='historical_line_snapshots'"
        ).fetchall()
        if not tables:
            conn.close()
            return {
                "ok": False,
                "version": version,
                "total_snapshots": 0,
                "snapshots": [],
                "warnings": ["table_not_found: historical_line_snapshots"],
            }

        # Build query dynamically
        columns_to_select = [
            "snapshot_id", "event_id", "source_key", "source_file",
            "sport", "league", "event_date", "home_team", "away_team",
            "bookmaker", "market", "market_family", "selection",
            "player_name", "team_name", "line_value", "odds_value",
            "implied_probability", "snapshot_label", "snapshot_time",
            "raw_market_name", "raw_selection_name", "created_at", "updated_at",
        ]
        # ensure only existing columns
        col_names = [r["name"] for r in conn.execute("PRAGMA table_info(historical_line_snapshots)")]
        safe_cols = [c for c in columns_to_select if c in col_names]

        where_parts: list[str] = []
        params: list[Any] = []

        if event_id is not None:
            where_parts.append("event_id = ?")
            params.append(event_id)
        if bookmaker is not None:
            where_parts.append("bookmaker = ?")
            params.append(bookmaker)
        if market_family is not None:
            where_parts.append("market_family = ?")
            params.append(market_family)
        if market is not None:
            where_parts.append("market = ?")
            params.append(market)
        if selection is not None:
            where_parts.append("selection = ?")
            params.append(selection)

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        query = f"SELECT {','.join(safe_cols)} FROM historical_line_snapshots WHERE {where_clause}"
        if limit is not None and limit >= 0:
            query += " LIMIT ?"
            params.append(limit)

        rows = conn.execute(query, params).fetchall()
        snapshots = [dict(r) for r in rows]
        conn.close()
        return {
            "ok": True,
            "version": version,
            "total_snapshots": len(snapshots),
            "snapshots": snapshots,
            "warnings": [],
        }
    except Exception as exc:
        conn.close()
        return {
            "ok": False,
            "version": version,
            "total_snapshots": 0,
            "snapshots": [],
            "warnings": [f"query_error: {exc}"],
        }


# ---------------------------------------------------------------------------
# Dashboard wrapper (SQLite)
# ---------------------------------------------------------------------------


def build_asof_line_movement_query_snapshot_from_sqlite(
    db_path: str | Path,
    event_id: str | None = None,
    hypothetical_bet_time: Any = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    group_fields: Sequence[str] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Load from SQLite then apply as‑of query.

    No SQL writes.
    """
    load_result = load_line_movement_snapshots_from_sqlite(
        db_path,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )

    snapshots = load_result.get("snapshots", [])
    query_snapshot = build_asof_line_movement_query_snapshot(
        snapshots=snapshots,
        event_id=event_id,
        hypothetical_bet_time=hypothetical_bet_time,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        group_fields=group_fields,
        limit=limit,
    )

    # Merge warnings
    all_warnings: list[str] = []
    all_warnings.extend(load_result.get("warnings", []))
    all_warnings.extend(query_snapshot.get("warnings", []))

    return {
        "ok": load_result.get("ok", False) and query_snapshot.get("ok", False),
        "version": AS_OF_LINE_MOVEMENT_QUERY_VERSION,
        "load": load_result,
        "query_snapshot": query_snapshot,
        "messages": describe_asof_line_movement_query_engine(),
        "warnings": all_warnings,
    }


# ---------------------------------------------------------------------------
# Operator messages
# ---------------------------------------------------------------------------


def describe_asof_line_movement_query_engine() -> list[str]:
    """Return operator‑friendly messages."""
    return [
        "As-Of Line Movement Query Engine filters historical snapshots to only "
        "those available at or before a hypothetical bet time.",
        "It prevents look-ahead bias by requiring snapshot_time ≤ hypothetical_bet_time.",
        "It does not connect to vendors, import paid data, or scrape.",
        "Phase 10H23 will turn these checks into a Line Movement Data Quality Dashboard.",
        "Future model features should use resolved event_id plus as-of filtered snapshots only.",
    ]
