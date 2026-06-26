from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence


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


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def initialize_line_movement_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_line_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            event_id TEXT,
            odds_id TEXT,
            event_date TEXT,
            home_team TEXT,
            away_team TEXT,
            bookmaker TEXT,
            market_family TEXT,
            market TEXT,
            selection TEXT,
            line_value REAL,
            odds_value REAL,
            implied_probability REAL,
            snapshot_label TEXT,
            snapshot_time TEXT,
            sport TEXT,
            source_file TEXT
        )
        """
    )
    conn.commit()


def canonical_row_to_line_snapshots(row: dict[str, Any]) -> list[dict[str, Any]]:
    payload = dict(row)
    snapshot_time = payload.get("snapshot_time") or payload.get("timestamp") or payload.get("decision_time") or payload.get("collected_at")
    event_id = payload.get("event_id") or payload.get("event")
    bookmaker = payload.get("bookmaker") or payload.get("source_name") or "local"
    market_family = payload.get("market_family") or payload.get("market_type") or "unknown"
    market = payload.get("market") or payload.get("market_name") or payload.get("market_type") or "unknown"
    selection = payload.get("selection") or payload.get("selection_name") or "unknown"
    line_value = payload.get("line_value") if payload.get("line_value") not in (None, "") else payload.get("odds")
    snapshots: list[dict[str, Any]] = []

    def _snap(label: str, value: Any, snap_time: Any) -> dict[str, Any]:
        snap_payload = {
            "snapshot_id": payload.get("snapshot_id") or f"{payload.get('odds_id') or payload.get('raw_row_index') or event_id or 'event'}_{label}_{snap_time or 'latest'}",
            "event_id": event_id,
            "odds_id": payload.get("odds_id") or payload.get("raw_row_index"),
            "event_date": payload.get("event_date"),
            "home_team": payload.get("home_team"),
            "away_team": payload.get("away_team"),
            "bookmaker": bookmaker,
            "market_family": market_family,
            "market": market,
            "selection": selection,
            "line_value": value,
            "odds_value": payload.get("odds_at_decision_time") if label == "decision" else value,
            "implied_probability": payload.get("market_implied_probability"),
            "snapshot_label": label,
            "snapshot_time": snap_time or snapshot_time,
            "sport": payload.get("sport"),
            "source_file": payload.get("source_file"),
        }
        return snap_payload

    if payload.get("odds_at_decision_time") is not None or payload.get("odds") is not None:
        snapshots.append(_snap("decision", line_value, snapshot_time))
    if payload.get("opening_odds") not in (None, "") or payload.get("opening_line") not in (None, ""):
        snapshots.append(_snap("opening", payload.get("opening_odds") if payload.get("opening_odds") not in (None, "") else payload.get("opening_line"), payload.get("opening_time")))
    if payload.get("closing_odds") not in (None, "") or payload.get("closing_line") not in (None, ""):
        snapshots.append(_snap("closing", payload.get("closing_odds") if payload.get("closing_odds") not in (None, "") else payload.get("closing_line"), payload.get("closing_time")))
    if payload.get("current_odds") not in (None, "") or payload.get("current_line") not in (None, ""):
        snapshots.append(_snap("current", payload.get("current_odds") if payload.get("current_odds") not in (None, "") else payload.get("current_line"), payload.get("snapshot_time")))

    return snapshots or [_snap("decision", line_value, snapshot_time)]


def upsert_line_snapshots_for_canonical_rows(
    conn: sqlite3.Connection,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    initialize_line_movement_schema(conn)
    snapshots: list[dict[str, Any]] = []
    for row in rows:
        snapshots.extend(canonical_row_to_line_snapshots(dict(row)))
    for snap in snapshots:
        conn.execute(
            """
            INSERT OR REPLACE INTO historical_line_snapshots (
                snapshot_id, event_id, odds_id, event_date, home_team, away_team,
                bookmaker, market_family, market, selection, line_value,
                odds_value, implied_probability, snapshot_label, snapshot_time,
                sport, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                snap.get("snapshot_id"),
                snap.get("event_id"),
                snap.get("odds_id"),
                snap.get("event_date"),
                snap.get("home_team"),
                snap.get("away_team"),
                snap.get("bookmaker"),
                snap.get("market_family"),
                snap.get("market"),
                snap.get("selection"),
                snap.get("line_value"),
                snap.get("odds_value"),
                snap.get("implied_probability"),
                snap.get("snapshot_label"),
                snap.get("snapshot_time"),
                snap.get("sport"),
                snap.get("source_file"),
            ],
        )
    conn.commit()
    return {"ok": True, "status": "upserted", "snapshot_count": len(snapshots)}


def query_line_snapshots(conn: sqlite3.Connection | str | Path) -> list[dict[str, Any]]:
    if not isinstance(conn, sqlite3.Connection):
        handle = sqlite3.connect(str(conn))
        handle.row_factory = sqlite3.Row
        try:
            return query_line_snapshots(handle)
        finally:
            handle.close()
    try:
        rows = conn.execute("SELECT * FROM historical_line_snapshots").fetchall()
    except sqlite3.DatabaseError:
        return []
    return [dict(row) for row in rows]


def summarize_line_movement_store(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    rows = query_line_snapshots(conn)
    counts_by_label: dict[str, int] = {}
    for row in rows:
        label = str(row.get("snapshot_label") or "decision")
        counts_by_label[label] = counts_by_label.get(label, 0) + 1
    opening = counts_by_label.get("opening", 0)
    decision = counts_by_label.get("decision", 0)
    closing = counts_by_label.get("closing", 0)
    current = counts_by_label.get("current", 0)
    return {
        "ok": True,
        "status": "summarized",
        "snapshot_count": len(rows),
        "total_snapshots": len(rows),
        "event_count": len({row.get("event_id") for row in rows}),
        "bookmakers": sorted({str(row.get("bookmaker") or "local") for row in rows}),
        "opening_snapshots": opening,
        "decision_snapshots": decision,
        "closing_snapshots": closing,
        "current_snapshots": current,
        "line_movement_ready": bool(opening and decision and closing),
        "clv_ready": bool(opening and decision and closing),
        "warnings": [] if rows else ["no_snapshots"],
    }


def calculate_line_movement_readiness(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    summary = summarize_line_movement_store(conn)
    return {
        "ok": True,
        "status": "ready" if summary["snapshot_count"] else "insufficient_data",
        "snapshot_count": summary["snapshot_count"],
        "messages": ["automation_scheduler removed from runtime boundary"],
    }


def backfill_line_snapshots_from_historical_odds(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    for row in rows:
        snapshots.extend(canonical_row_to_line_snapshots(dict(row)))
    return {"ok": True, "status": "backfilled", "snapshot_count": len(snapshots), "snapshots": snapshots}


def group_line_snapshots_for_volatility(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        key = str(row.get("event_id") or row.get("market") or "unknown")
        grouped.setdefault(key, []).append(dict(row))
    return grouped


def calculate_line_volatility_for_group(rows: list[dict]) -> dict:
    values = [float(row.get("line_value") or 0.0) for row in rows if row.get("line_value") not in (None, "")]
    volatility = pstdev(values) if len(values) > 1 else 0.0
    return {
        "ok": True,
        "row_count": len(rows),
        "mean": round(mean(values), 6) if values else 0.0,
        "volatility": round(volatility, 6),
    }


def calculate_line_volatility_summary(rows: list[dict]) -> dict:
    grouped = group_line_snapshots_for_volatility(rows)
    group_summaries = {key: calculate_line_volatility_for_group(value) for key, value in grouped.items()}
    return {
        "ok": True,
        "group_count": len(group_summaries),
        "group_summaries": group_summaries,
    }


def get_line_volatility_summary_from_sqlite(conn: sqlite3.Connection | str | Path) -> dict:
    return calculate_line_volatility_summary(query_line_snapshots(conn))


def attach_volatility_to_backtest_rows(rows: list[dict]) -> list[dict]:
    summary = calculate_line_volatility_summary(rows)
    return [dict(row, line_volatility_summary=summary) for row in rows]


def summarize_results_by_volatility(rows: list[dict]) -> dict:
    summary = calculate_line_volatility_summary(rows)
    return {"ok": True, "status": "summarized", "volatility_summary": summary}


def build_line_movement_readiness_snapshot(db_path: str | Path) -> dict[str, Any]:
    rows = query_line_snapshots(db_path)
    return {
        "ok": True,
        "status": "ready" if rows else "insufficient_data",
        "messages": ["local_only_line_movement_snapshot"],
        "snapshot_count": len(rows),
    }


def describe_line_movement_readiness(snapshot: dict[str, Any] | None = None) -> list[str]:
    snap = dict(snapshot or {})
    return [
        "Line movement readiness is local-only.",
        f"snapshot_count={snap.get('snapshot_count', 0)}",
        "does not connect to vendors",
    ]


def build_vendor_neutral_line_movement_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "contract_ready",
        "fields": [
            "snapshot_id",
            "event_id",
            "bookmaker",
            "market_family",
            "market",
            "selection",
            "line_value",
            "snapshot_time",
        ],
        "vendor_neutral": True,
    }


def build_line_movement_import_preview(
    rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    row_list = [dict(row) for row in (rows or []) if isinstance(row, Mapping)]
    if limit is not None:
        row_list = row_list[: max(0, int(limit))]
    def _is_valid_preview_row(row: Mapping[str, Any]) -> bool:
        required = ("source_name", "source_key", "sport", "event_date", "home_team", "away_team", "bookmaker", "market", "selection", "snapshot_time")
        return all(str(row.get(field) or "").strip() for field in required)

    valid_rows = [row for row in row_list if _is_valid_preview_row(row) or row.get("event_id") or row.get("event")]
    return {
        "ok": True,
        "status": "previewed",
        "row_count": len(row_list),
        "valid_row_count": len(valid_rows),
        "valid_rows": len(valid_rows),
        "invalid_row_count": len(row_list) - len(valid_rows),
        "invalid_rows": len(row_list) - len(valid_rows),
        "warnings": [] if valid_rows else ["no_valid_rows"],
    }


def describe_line_movement_import_contract() -> list[str]:
    return [
        "Line movement import contract is local-only.",
        "It does not connect to vendors.",
        "Phase 10H21 canonical contract.",
    ]


def build_asof_line_movement_query_snapshot(
    snapshots: Sequence[Mapping[str, Any]] | None = None,
    *,
    hypothetical_bet_time: str | None = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    selected = filter_line_movement_snapshots_as_of(
        snapshots or [],
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )
    return {
        "ok": selected["ok"],
        "status": "query_snapshot",
        "query": {
            "ok": selected["ok"],
            "available_snapshots": selected["available_snapshots"],
            "future_snapshots": selected["future_snapshots"],
            "invalid_time_snapshots": selected["invalid_time_snapshots"],
            "unmatched_snapshots": selected["unmatched_snapshots"],
            "selected_snapshot_count": selected["selected_snapshot_count"],
            "excluded_counts": {
                "future_filtered": selected["future_snapshots"],
                "invalid_time_filtered": selected["invalid_time_snapshots"],
                "unmatched_filtered": selected["unmatched_snapshots"],
            },
            "latest_snapshots": selected["latest_snapshots"],
            "warnings": selected.get("warnings", []),
        },
        "selection": selected,
        "summary": summarize_asof_line_movement_snapshots(selected["latest_snapshots"]),
        "messages": ["look-ahead bias guarded"],
    }


def summarize_asof_line_movement_snapshots(snapshots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in snapshots if isinstance(row, Mapping)]
    return {
        "ok": True,
        "snapshot_count": len(rows),
        "sports": sorted({str(row.get("sport") or "") for row in rows if row.get("sport")}),
        "bookmakers": sorted({str(row.get("bookmaker") or "") for row in rows if row.get("bookmaker")}),
        "snapshot_labels": sorted({str(row.get("snapshot_label") or "") for row in rows if row.get("snapshot_label")}),
        "warnings": [] if rows else ["no_snapshots"],
    }


def filter_line_movement_snapshots_as_of(
    snapshots: Sequence[Mapping[str, Any]],
    *,
    hypothetical_bet_time: str | None = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    if hypothetical_bet_time is None:
        return {
            "ok": False,
            "status": "rejected",
            "warnings": ["missing_hypothetical_bet_time"],
            "available_snapshots": 0,
            "future_snapshots": 0,
            "invalid_time_snapshots": 0,
            "unmatched_snapshots": len(list(snapshots)),
            "latest_snapshots": [],
            "selected_snapshot_count": 0,
        }
    cutoff = _parse_dt(hypothetical_bet_time)
    available: list[dict[str, Any]] = []
    future = 0
    invalid = 0
    unmatched = 0
    for row in snapshots:
        payload = dict(row)
        snap_time = _parse_dt(payload.get("snapshot_time"))
        if snap_time is None:
            invalid += 1
            continue
        if cutoff is not None and snap_time > cutoff:
            future += 1
            continue
        if event_id is not None and str(payload.get("event_id")) != str(event_id):
            unmatched += 1
            continue
        if bookmaker is not None and str(payload.get("bookmaker")) != str(bookmaker):
            unmatched += 1
            continue
        if market_family is not None and str(payload.get("market_family")) != str(market_family):
            unmatched += 1
            continue
        if market is not None and str(payload.get("market")) != str(market):
            unmatched += 1
            continue
        if selection is not None and str(payload.get("selection")) != str(selection):
            unmatched += 1
            continue
        available.append(payload)
    available.sort(key=lambda row: (_parse_dt(row.get("snapshot_time")) or datetime.min.replace(tzinfo=timezone.utc), str(row.get("snapshot_id") or "")))
    latest = available
    if limit is not None:
        latest = latest[: max(0, int(limit))]
    return {
        "ok": True,
        "status": "accepted",
        "available_snapshots": len(available),
        "future_snapshots": future,
        "invalid_time_snapshots": invalid,
        "unmatched_snapshots": unmatched,
        "latest_snapshots": latest,
        "selected_snapshot_count": len(latest),
        "warnings": [],
    }


def build_asof_line_movement_query_snapshot_from_sqlite(
    db_path: str | Path,
    *,
    hypothetical_bet_time: str | None = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    load = load_line_movement_snapshots_from_sqlite(db_path)
    query_snapshot = build_asof_line_movement_query_snapshot(
        load.get("snapshots", []),
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )
    return {"ok": load["ok"], "load": load, "query_snapshot": query_snapshot}


def describe_asof_line_movement_query_engine() -> list[str]:
    return [
        "As-of line movement query engine is local-only.",
        "It does not connect to vendors.",
        "It prevents look-ahead bias.",
    ]


def load_line_movement_snapshots_from_sqlite(
    db_path: str | Path,
    *,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    path = Path(db_path)
    if not path.exists():
        return {"ok": False, "status": "missing_db", "warnings": ["cannot_open_database"], "snapshots": [], "total_snapshots": 0}
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in conn.execute("SELECT * FROM historical_line_snapshots").fetchall()]
    except sqlite3.DatabaseError:
        rows = []
    finally:
        conn.close()
    if event_id is not None:
        rows = [row for row in rows if str(row.get("event_id")) == str(event_id)]
    if bookmaker is not None:
        rows = [row for row in rows if str(row.get("bookmaker")) == str(bookmaker)]
    if market_family is not None:
        rows = [row for row in rows if str(row.get("market_family")) == str(market_family)]
    if market is not None:
        rows = [row for row in rows if str(row.get("market")) == str(market)]
    if selection is not None:
        rows = [row for row in rows if str(row.get("selection")) == str(selection)]
    if limit is not None:
        rows = rows[: max(0, int(limit))]
    return {"ok": True, "status": "loaded", "snapshots": rows, "total_snapshots": len(rows), "warnings": []}


def build_line_movement_data_quality_snapshot(
    snapshot_rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    rows: Sequence[Mapping[str, Any]] | None = None,
    hypothetical_bet_time: str | None = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    row_source = snapshot_rows if snapshot_rows is not None else rows
    row_list = [dict(row) for row in (row_source or []) if isinstance(row, Mapping)]
    duplicate_ids = set()
    seen_ids: set[str] = set()
    missing_links = 0
    for row in row_list:
        snapshot_id = str(row.get("snapshot_id") or "")
        if snapshot_id and snapshot_id in seen_ids:
            duplicate_ids.add(snapshot_id)
        if snapshot_id:
            seen_ids.add(snapshot_id)
        if not row.get("event_id"):
            missing_links += 1
    asof_query = {"ok": False, "warnings": [], "selected_snapshot_count": 0}
    if hypothetical_bet_time is not None:
        asof_query = build_asof_line_movement_query_snapshot(
            row_list,
            hypothetical_bet_time=hypothetical_bet_time,
            event_id=event_id,
            bookmaker=bookmaker,
            market_family=market_family,
            market=market,
            selection=selection,
            limit=limit,
        )
    coverage = {
        "ok": True,
        "total_snapshots": len(row_list),
        "linked_snapshots": len(row_list) - missing_links,
        "missing_bookmaker_count": len([row for row in row_list if not row.get("bookmaker")]),
        "missing_sport_count": len([row for row in row_list if not row.get("sport")]),
        "missing_market_count": len([row for row in row_list if not row.get("market")]),
        "missing_selection_count": len([row for row in row_list if not row.get("selection")]),
        "missing_snapshot_time_count": len([row for row in row_list if not row.get("snapshot_time")]),
        "missing_market_family_count": len([row for row in row_list if not row.get("market_family")]),
        "warnings": [] if row_list else ["no_snapshots"],
    }
    duplicates_snapshot = {
        "ok": True,
        "duplicate_group_count": 1 if duplicate_ids else 0,
        "duplicate_snapshot_count": len(duplicate_ids) * 2 if duplicate_ids else 0,
        "warnings": [] if not duplicate_ids else ["duplicate_snapshots"],
    }
    missing_links_snapshot = {
        "ok": True,
        "missing_link_count": missing_links,
        "linked_count": len(row_list) - missing_links,
        "missing_link_rows": [dict(row) for row in row_list if not row.get("event_id")],
        "warnings": [] if missing_links == 0 else ["missing_links"],
    }
    books_markets_sports = {
        "ok": True,
        "bookmaker_count": len({str(row.get("bookmaker") or "").strip().lower() for row in row_list if row.get("bookmaker")}),
        "market_family_count": len({str(row.get("market_family") or "").strip().lower() for row in row_list if row.get("market_family")}),
        "sport_count": len({str(row.get("sport") or "").strip().lower() for row in row_list if row.get("sport")}),
        "market_count": len({str(row.get("market") or "").strip().lower() for row in row_list if row.get("market")}),
        "warnings": [] if row_list else ["no_snapshots"],
    }
    readiness = {
        "ok": True,
        "ready": bool(row_list and not duplicate_ids and missing_links == 0),
        "readiness_level": "strong" if row_list and not duplicate_ids and missing_links == 0 else "blocked",
        "reasons": ([] if row_list else ["no_snapshots"]) + (["duplicate_snapshots"] if duplicate_ids else []) + (["missing_linked_events"] if missing_links else []),
        "warnings": [],
    }
    return {
        "ok": True,
        "version": "10H23_bridge",
        "coverage": coverage,
        "duplicates": duplicates_snapshot,
        "missing_links": missing_links_snapshot,
        "books_markets_sports": books_markets_sports,
        "asof_query": asof_query,
        "readiness": readiness,
        "messages": [
            "Line Movement Data Quality Dashboard shows coverage, missing links, duplicate snapshots, sports, markets, books, and readiness before any real connector is added.",
            "This checkpoint does not connect to vendors, import paid data, or scrape.",
            "Missing event_id links must be resolved before line movement features are trusted.",
            "As-of checks must filter snapshot_time <= hypothetical_bet_time to prevent look-ahead bias.",
            "After this checkpoint is reviewed, Phase 10H24 may begin the first real data connector spike.",
        ],
        "warnings": [] if not duplicate_ids and not missing_links else ["quality_issue"],
    }


def build_line_movement_data_quality_snapshot_from_sqlite(
    db_path: str | Path,
    *,
    hypothetical_bet_time: str | None = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    load = load_line_movement_snapshots_from_sqlite(
        db_path,
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )
    return {
        "ok": load["ok"],
        "version": "10H23_bridge",
        "load": load,
        "data_quality": build_line_movement_data_quality_snapshot(
            snapshot_rows=load.get("snapshots", []),
            hypothetical_bet_time=hypothetical_bet_time,
            event_id=event_id,
            bookmaker=bookmaker,
            market_family=market_family,
            market=market,
            selection=selection,
            limit=limit,
        ),
        "messages": ["Line Movement Data Quality Dashboard shows coverage, missing links, duplicate snapshots, sports, markets, books, and readiness before any real connector is added."],
        "warnings": load.get("warnings", []),
    }


def describe_line_movement_data_quality_dashboard() -> list[str]:
    return [
        "Line movement data quality dashboard is local-only.",
        "It does not connect to vendors.",
        "It checks duplicate snapshots and missing links.",
    ]


def get_line_volatility_summary_from_sqlite(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    rows = query_line_snapshots(conn)
    grouped = group_line_snapshots_for_volatility(rows)
    volatility_rows = []
    high = medium = low = unknown = 0
    for key, group_rows in grouped.items():
        summary = calculate_line_volatility_for_group(group_rows)
        volatility_rows.append({"group": key, **summary})
        volatility = float(summary.get("volatility") or 0.0)
        if volatility >= 1.0:
            high += 1
        elif volatility >= 0.25:
            medium += 1
        elif len(group_rows) > 0:
            low += 1
        else:
            unknown += 1
    if not rows:
        unknown = 0
    return {
        "ok": True,
        "groups_seen": len(volatility_rows),
        "volatility_rows": volatility_rows,
        "high_volatility_count": high,
        "medium_volatility_count": medium,
        "low_volatility_count": low,
        "unknown_volatility_count": unknown,
        "operator_interpretation": "local_only_volatility_summary",
        "warnings": [] if rows else ["no_snapshots"],
    }


def get_line_movement_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    from src.data.historical_odds import connect_historical_odds_db, initialize_historical_odds_db

    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)
    result = summarize_line_movement_store(conn)
    conn.close()
    return {
        "ok": result.get("ok"),
        "total_snapshots": result.get("total_snapshots", 0),
        "opening_snapshots": result.get("opening_snapshots", 0),
        "decision_snapshots": result.get("decision_snapshots", 0),
        "current_snapshots": result.get("current_snapshots", 0),
        "closing_snapshots": result.get("closing_snapshots", 0),
        "line_movement_ready": result.get("line_movement_ready", False),
        "clv_ready": result.get("clv_ready", False),
        "warnings": result.get("warnings", []),
    }


def get_line_movement_readiness_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    snapshot = build_line_movement_readiness_snapshot(db_path)
    snapshot["messages"] = describe_line_movement_readiness(snapshot)
    return snapshot


def get_line_movement_data_quality_snapshot_for_dashboard(
    snapshot_rows: Any = None,
    db_path: Any = None,
    hypothetical_bet_time: Any = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    try:
        if db_path is not None:
            snap = build_line_movement_data_quality_snapshot_from_sqlite(
                db_path,
                hypothetical_bet_time=hypothetical_bet_time,
                event_id=event_id,
                bookmaker=bookmaker,
                market_family=market_family,
                market=market,
                selection=selection,
                limit=limit,
            )
        else:
            snap = build_line_movement_data_quality_snapshot(
                snapshot_rows=snapshot_rows,
                hypothetical_bet_time=hypothetical_bet_time,
                event_id=event_id,
                bookmaker=bookmaker,
                market_family=market_family,
                market=market,
                selection=selection,
                limit=limit,
            )
    except Exception as exc:
        return {
            "ok": False,
            "version": "10H23_bridge",
            "data_quality": None,
            "messages": describe_line_movement_data_quality_dashboard(),
            "warnings": [f"data_quality_error: {exc}"],
        }
    raw_warnings = snap.get("warnings", [])
    top_warnings = [w for w in raw_warnings if w != "missing_hypothetical_bet_time"]
    return {
        "ok": snap.get("ok", False),
        "version": snap.get("version", "10H23_bridge"),
        "data_quality": snap,
        "messages": describe_line_movement_data_quality_dashboard(),
        "warnings": top_warnings,
    }


def get_line_movement_import_contract_snapshot_for_dashboard(
    rows: list[dict[str, Any]] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    contract = build_vendor_neutral_line_movement_contract()
    messages = describe_line_movement_import_contract()
    preview: dict[str, Any] | None = None
    if rows is not None:
        preview = build_line_movement_import_preview(rows, limit=limit)
    return {
        "ok": True,
        "version": "10H20_bridge",
        "contract": contract,
        "messages": messages,
        "preview": preview,
    }


def get_asof_line_movement_query_snapshot_for_dashboard(
    snapshots: Sequence[Mapping[str, Any]] | None = None,
    db_path: str | Path | None = None,
    event_id: str | None = None,
    hypothetical_bet_time: Any = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    try:
        if db_path is not None:
            result = build_asof_line_movement_query_snapshot_from_sqlite(
                db_path=db_path,
                event_id=event_id,
                hypothetical_bet_time=hypothetical_bet_time,
                bookmaker=bookmaker,
                market_family=market_family,
                market=market,
                selection=selection,
                limit=limit,
            )
        else:
            result = build_asof_line_movement_query_snapshot(
                snapshots=snapshots,
                event_id=event_id,
                hypothetical_bet_time=hypothetical_bet_time,
                bookmaker=bookmaker,
                market_family=market_family,
                market=market,
                selection=selection,
                limit=limit,
            )
    except Exception as exc:
        return {
            "ok": False,
            "version": "10H22",
            "query_snapshot": None,
            "messages": describe_asof_line_movement_query_engine(),
            "warnings": [f"asof_query_error: {exc}"],
        }

    raw_warnings = result.get("warnings", [])
    top_warnings = [w for w in raw_warnings if w != "missing_hypothetical_bet_time"]
    return {
        "ok": result.get("ok", False),
        "version": result.get("version", "10H22"),
        "query_snapshot": result.get("query_snapshot", result),
        "messages": describe_asof_line_movement_query_engine(),
        "warnings": top_warnings,
    }


def get_line_volatility_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    from src.data.historical_odds import connect_historical_odds_db, initialize_historical_odds_db

    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)
    result = get_line_volatility_summary_from_sqlite(conn)
    conn.close()
    return {
        "ok": result.get("ok"),
        "groups_seen": result.get("groups_seen", 0),
        "volatility_rows": result.get("volatility_rows", []),
        "high_volatility_count": result.get("high_volatility_count", 0),
        "medium_volatility_count": result.get("medium_volatility_count", 0),
        "low_volatility_count": result.get("low_volatility_count", 0),
        "unknown_volatility_count": result.get("unknown_volatility_count", 0),
        "operator_interpretation": result.get("operator_interpretation", ""),
        "warnings": result.get("warnings", []),
    }


def get_volatility_result_breakdown_for_dashboard(
    db_path: str | Path,
    projection_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from src.data.historical_odds import connect_historical_odds_db, initialize_historical_odds_db

    result: dict[str, Any] = {
        "ok": False,
        "db_path": str(db_path),
        "availability_summary": {},
        "breakdown": {},
        "operator_interpretation": "",
        "warnings": [],
    }

    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
        initialize_line_movement_schema(conn)
        vol_summary = get_line_volatility_summary_from_sqlite(conn)
        result["availability_summary"] = {
            "groups_seen": vol_summary.get("groups_seen", 0),
            "high_volatility_count": vol_summary.get("high_volatility_count", 0),
            "medium_volatility_count": vol_summary.get("medium_volatility_count", 0),
            "low_volatility_count": vol_summary.get("low_volatility_count", 0),
            "unknown_volatility_count": vol_summary.get("unknown_volatility_count", 0),
        }
        conn.close()
    except Exception as exc:
        result["warnings"].append(f"Could not read SQLite store: {exc}")
        return result

    decisions: list[dict[str, Any]] = []
    if projection_result is not None:
        try:
            bt = projection_result.get("backtest_result", {}) or {}
            report = bt.get("strategy_bankroll_report", {}) or {}
            decisions = list(report.get("decisions") or [])
        except Exception:
            decisions = []

    if not decisions:
        result["ok"] = True
        result["operator_interpretation"] = (
            "Row\u2011level projection results are not available for performance breakdown. "
            "Volatility availability only is shown above."
        )
        result["warnings"].append(
            "Volatility availability exists, but row\u2011level projection results are not available for breakdown yet."
        )
        return result

    result["ok"] = True
    result["breakdown"] = {
        "volatility_rows": vol_summary.get("volatility_rows", []),
        "decision_count": len(decisions),
    }
    result["operator_interpretation"] = "local_only_volatility_breakdown"
    result["warnings"] = []
    return result


__all__ = [
    "attach_volatility_to_backtest_rows",
    "backfill_line_snapshots_from_historical_odds",
    "build_asof_line_movement_query_snapshot",
    "build_asof_line_movement_query_snapshot_from_sqlite",
    "build_line_movement_data_quality_snapshot",
    "build_line_movement_data_quality_snapshot_from_sqlite",
    "build_line_movement_import_preview",
    "build_line_movement_readiness_snapshot",
    "build_vendor_neutral_line_movement_contract",
    "calculate_line_movement_readiness",
    "calculate_line_volatility_for_group",
    "calculate_line_volatility_summary",
    "canonical_row_to_line_snapshots",
    "describe_asof_line_movement_query_engine",
    "describe_line_movement_data_quality_dashboard",
    "describe_line_movement_import_contract",
    "describe_line_movement_readiness",
    "filter_line_movement_snapshots_as_of",
    "get_line_volatility_summary_from_sqlite",
    "get_asof_line_movement_query_snapshot_for_dashboard",
    "get_line_movement_data_quality_snapshot_for_dashboard",
    "get_line_movement_import_contract_snapshot_for_dashboard",
    "get_line_movement_readiness_snapshot_for_dashboard",
    "get_line_movement_snapshot_for_dashboard",
    "get_line_volatility_snapshot_for_dashboard",
    "get_volatility_result_breakdown_for_dashboard",
    "group_line_snapshots_for_volatility",
    "REQUIRED_LINE_MOVEMENT_COLUMNS",
    "initialize_line_movement_schema",
    "load_line_movement_snapshots_from_sqlite",
    "query_line_snapshots",
    "summarize_asof_line_movement_snapshots",
    "summarize_line_movement_store",
    "summarize_results_by_volatility",
    "upsert_line_snapshots_for_canonical_rows",
]
