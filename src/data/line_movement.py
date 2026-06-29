from __future__ import annotations

from importlib import import_module
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

LINE_MOVEMENT_READINESS_VERSION = "10H19"
LINE_MOVEMENT_IMPORT_CONTRACT_VERSION = "10H20"
AS_OF_LINE_MOVEMENT_QUERY_VERSION = "10H22"
LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION = "10H23"


_LEGACY_LINE_MOVEMENT_MODULES: tuple[str, ...] = (
    "src.automation_scheduler_legacy.line_movement_import_contract",
    "src.automation_scheduler_legacy.line_movement_readiness",
    "src.automation_scheduler_legacy.line_movement_data_quality_dashboard",
    "src.automation_scheduler_legacy.asof_line_movement_query",
    "src.automation_scheduler_legacy.historical_line_movement",
)


def __getattr__(name: str) -> Any:
    for module_name in _LEGACY_LINE_MOVEMENT_MODULES:
        module = import_module(module_name)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def initialize_line_movement_schema(conn: sqlite3.Connection) -> None:
    from src.automation_scheduler_legacy.historical_line_movement import initialize_line_movement_schema as _legacy_initialize_line_movement_schema

    _legacy_initialize_line_movement_schema(conn)


def canonical_row_to_line_snapshots(row: dict[str, Any]) -> list[dict[str, Any]]:
    payload = dict(row)
    snapshot_time = payload.get("snapshot_time") or payload.get("timestamp") or payload.get("decision_time") or payload.get("collected_at")
    now = _utc_now()
    event_id = payload.get("event_id") or payload.get("event")
    source_key = payload.get("source_key") or ""
    source_file = payload.get("source_file") or ""
    league = payload.get("league") or ""
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
            "source_key": source_key,
            "source_file": source_file,
            "sport": payload.get("sport"),
            "league": league,
            "event_date": payload.get("event_date"),
            "home_team": payload.get("home_team"),
            "away_team": payload.get("away_team"),
            "bookmaker": bookmaker,
            "market_family": market_family,
            "market": market,
            "selection": selection,
            "player_name": payload.get("player_name"),
            "team_name": payload.get("team_name"),
            "line_value": value,
            "odds_value": payload.get("odds_at_decision_time") if label == "decision" else value,
            "implied_probability": payload.get("market_implied_probability"),
            "snapshot_label": label,
            "snapshot_time": snap_time or snapshot_time,
            "raw_market_name": payload.get("raw_market_name") or "",
            "raw_selection_name": payload.get("raw_selection_name") or "",
            "created_at": payload.get("created_at") or snapshot_time or now,
            "updated_at": payload.get("updated_at") or snapshot_time or now,
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


def upsert_line_snapshots(
    conn: sqlite3.Connection,
    snapshots: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    from src.automation_scheduler_legacy.historical_line_movement import upsert_line_snapshots as _legacy_upsert_line_snapshots

    return _legacy_upsert_line_snapshots(conn, [dict(row) for row in snapshots if isinstance(row, Mapping)])


def upsert_line_snapshots_for_canonical_rows(
    conn: sqlite3.Connection,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    for row in rows:
        snapshots.extend(canonical_row_to_line_snapshots(dict(row)))
    return upsert_line_snapshots(conn, snapshots)


def query_line_snapshots(
    conn: sqlite3.Connection | str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    snapshot_label: str | None = None,
    player_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    close_conn = False
    if not isinstance(conn, sqlite3.Connection):
        path = Path(conn)
        if not path.exists():
            return []
        handle = sqlite3.connect(str(path))
        handle.row_factory = sqlite3.Row
        conn = handle
        close_conn = True
    try:
        conditions: list[str] = []
        params: list[Any] = []
        if sport is not None:
            conditions.append("LOWER(sport) = LOWER(?)")
            params.append(sport)
        if league is not None:
            conditions.append("LOWER(league) = LOWER(?)")
            params.append(league)
        if market is not None:
            conditions.append("LOWER(market) = LOWER(?)")
            params.append(market)
        if source_key is not None:
            conditions.append("LOWER(source_key) = LOWER(?)")
            params.append(source_key)
        if snapshot_label is not None:
            conditions.append("LOWER(snapshot_label) = LOWER(?)")
            params.append(snapshot_label)
        if player_name is not None:
            conditions.append("LOWER(player_name) LIKE LOWER(?)")
            params.append(f"%{player_name}%")
        if start_date is not None:
            conditions.append("event_date >= ?")
            params.append(start_date)
        if end_date is not None:
            conditions.append("event_date <= ?")
            params.append(end_date)
        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM historical_line_snapshots WHERE {where} ORDER BY event_date, snapshot_time LIMIT ?"
        params.append(max(0, int(limit)))
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.DatabaseError:
            return []
        return [dict(row) for row in rows]
    finally:
        if close_conn:
            conn.close()


def summarize_line_movement_store(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    from src.automation_scheduler_legacy.historical_line_movement import summarize_line_movement_store as _legacy_summarize_line_movement_store

    if isinstance(conn, sqlite3.Connection):
        return _legacy_summarize_line_movement_store(conn)
    path = Path(conn)
    if not path.exists():
        return {
            "ok": True,
            "total_snapshots": 0,
            "opening_snapshots": 0,
            "decision_snapshots": 0,
            "current_snapshots": 0,
            "closing_snapshots": 0,
            "sports": [],
            "leagues": [],
            "markets": [],
            "market_families": [],
            "source_keys": [],
            "player_names": [],
            "line_movement_ready": False,
            "clv_ready": False,
            "warnings": ["missing_db"],
        }
    handle = sqlite3.connect(str(path))
    handle.row_factory = sqlite3.Row
    try:
        return _legacy_summarize_line_movement_store(handle)
    finally:
        handle.close()


def calculate_line_movement_readiness(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    if isinstance(conn, dict):
        summary_or_rows = conn
    elif isinstance(conn, list):
        summary_or_rows = conn
    else:
        summary = summarize_line_movement_store(conn)
        summary_or_rows = summary

    if isinstance(summary_or_rows, dict) and {"opening_snapshots", "decision_snapshots", "closing_snapshots"} & set(summary_or_rows):
        opening = int(summary_or_rows.get("opening_snapshots", 0) or 0)
        decision = int(summary_or_rows.get("decision_snapshots", 0) or 0)
        closing = int(summary_or_rows.get("closing_snapshots", 0) or 0)
    else:
        rows = summary_or_rows if isinstance(summary_or_rows, list) else []
        opening = sum(1 for row in rows if isinstance(row, Mapping) and str(row.get("snapshot_label") or "").lower() == "opening")
        decision = sum(1 for row in rows if isinstance(row, Mapping) and str(row.get("snapshot_label") or "").lower() == "decision")
        closing = sum(1 for row in rows if isinstance(row, Mapping) and str(row.get("snapshot_label") or "").lower() == "closing")

    line_movement_ready = bool(opening and decision and closing)
    clv_ready = bool(line_movement_ready and closing)
    missing: list[str] = []
    if not opening:
        missing.append("opening")
    if not decision:
        missing.append("decision")
    if not closing:
        missing.append("closing")
    return {
        "line_movement_ready": line_movement_ready,
        "clv_ready": clv_ready,
        "has_opening": bool(opening),
        "has_decision": bool(decision),
        "has_closing": bool(closing),
        "reason": "Line movement is ready. CLV is ready." if clv_ready else f"Missing: {', '.join(missing)} snapshots",
        "missing": missing,
    }


def backfill_line_snapshots_from_historical_odds(
    source: sqlite3.Connection | str | Path | Sequence[Mapping[str, Any]],
    *,
    limit: int = 100000,
) -> dict[str, Any]:
    if isinstance(source, sqlite3.Connection):
        from src.data.historical_odds import query_historical_odds_rows

        rows = query_historical_odds_rows(source, limit=limit)
    elif isinstance(source, (str, Path)):
        from src.data.historical_odds import connect_historical_odds_db, query_historical_odds_rows

        path = Path(source)
        if not path.exists():
            return {"ok": True, "status": "backfilled", "rows_read": 0, "snapshots_created": 0, "warnings": ["missing_db"]}
        conn = connect_historical_odds_db(path)
        try:
            rows = query_historical_odds_rows(conn, limit=limit)
        finally:
            conn.close()
    else:
        rows = [dict(row) for row in source if isinstance(row, Mapping)]

    snapshots: list[dict[str, Any]] = []
    for row in rows:
        snapshots.extend(canonical_row_to_line_snapshots(dict(row)))
    result = {"rows_inserted_or_updated": len(snapshots), "warnings": []}
    if snapshots:
        if isinstance(source, sqlite3.Connection):
            conn = source
            initialize_line_movement_schema(conn)
            result = upsert_line_snapshots(conn, snapshots)
        elif isinstance(source, (str, Path)):
            from src.data.historical_odds import connect_historical_odds_db

            conn = connect_historical_odds_db(Path(source))
            try:
                initialize_line_movement_schema(conn)
                result = upsert_line_snapshots(conn, snapshots)
            finally:
                conn.close()
    return {
        "ok": True,
        "status": "backfilled",
        "rows_read": len(rows),
        "snapshots_created": int(result.get("rows_inserted_or_updated", result.get("snapshot_count", len(snapshots))) or 0),
        "warnings": list(result.get("warnings", [])),
    }


def group_line_snapshots_for_volatility(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        key = str(row.get("event_id") or row.get("market") or "unknown")
        grouped.setdefault(key, []).append(dict(row))
    return grouped


def calculate_line_volatility_for_group(rows: list[dict]) -> dict:
    from src.automation_scheduler_legacy.historical_line_movement import calculate_line_volatility_for_group as _legacy_calculate_line_volatility_for_group

    return _legacy_calculate_line_volatility_for_group([dict(row) for row in rows if isinstance(row, Mapping)])


def calculate_line_volatility_summary(rows: list[dict]) -> dict:
    from src.automation_scheduler_legacy.historical_line_movement import calculate_line_volatility_summary as _legacy_calculate_line_volatility_summary

    return _legacy_calculate_line_volatility_summary([dict(row) for row in rows if isinstance(row, Mapping)])


def get_line_volatility_summary_from_sqlite(conn: sqlite3.Connection | str | Path) -> dict:
    from src.automation_scheduler_legacy.historical_line_movement import get_line_volatility_summary_from_sqlite as _legacy_get_line_volatility_summary_from_sqlite

    return _legacy_get_line_volatility_summary_from_sqlite(conn)


def attach_volatility_to_backtest_rows(
    rows: list[dict],
    volatility_rows: list[dict] | None = None,
) -> list[dict]:
    from src.automation_scheduler_legacy.historical_line_movement import attach_volatility_to_backtest_rows as _legacy_attach_volatility_to_backtest_rows

    return _legacy_attach_volatility_to_backtest_rows(
        [dict(row) for row in rows if isinstance(row, Mapping)],
        [dict(row) for row in (volatility_rows or []) if isinstance(row, Mapping)],
    )


def summarize_results_by_volatility(rows: list[dict]) -> dict:
    from src.automation_scheduler_legacy.historical_line_movement import summarize_results_by_volatility as _legacy_summarize_results_by_volatility

    return _legacy_summarize_results_by_volatility([dict(row) for row in rows if isinstance(row, Mapping)])


def build_line_movement_readiness_snapshot(db_path: str | Path) -> dict[str, Any]:
    from src.automation_scheduler_legacy.line_movement_readiness import build_line_movement_readiness_snapshot as _legacy_build_line_movement_readiness_snapshot

    return _legacy_build_line_movement_readiness_snapshot(db_path)


def describe_line_movement_readiness(snapshot: dict[str, Any] | None = None) -> list[str]:
    from src.automation_scheduler_legacy.line_movement_readiness import describe_line_movement_readiness as _legacy_describe_line_movement_readiness

    return _legacy_describe_line_movement_readiness(dict(snapshot or {}))


def build_vendor_neutral_line_movement_contract() -> dict[str, Any]:
    from src.automation_scheduler_legacy.line_movement_import_contract import build_vendor_neutral_line_movement_contract as _legacy_build_vendor_neutral_line_movement_contract

    return _legacy_build_vendor_neutral_line_movement_contract()


def build_line_movement_import_preview(
    rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    from src.automation_scheduler_legacy.line_movement_import_contract import build_line_movement_import_preview as _legacy_build_line_movement_import_preview

    effective_limit = 100 if limit is None else int(limit)
    return _legacy_build_line_movement_import_preview([dict(row) for row in (rows or []) if isinstance(row, Mapping)], limit=effective_limit)


def describe_line_movement_import_contract() -> list[str]:
    from src.automation_scheduler_legacy.line_movement_import_contract import describe_line_movement_import_contract as _legacy_describe_line_movement_import_contract

    return _legacy_describe_line_movement_import_contract()


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
    from src.automation_scheduler_legacy.asof_line_movement_query import build_asof_line_movement_query_snapshot as _legacy_build_asof_line_movement_query_snapshot

    effective_limit = 100 if limit is None else int(limit)
    return _legacy_build_asof_line_movement_query_snapshot(
        snapshots or [],
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=effective_limit,
    )


def summarize_asof_line_movement_snapshots(snapshots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    from src.automation_scheduler_legacy.asof_line_movement_query import summarize_asof_line_movement_snapshots as _legacy_summarize_asof_line_movement_snapshots

    return _legacy_summarize_asof_line_movement_snapshots([dict(row) for row in snapshots if isinstance(row, Mapping)])


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
    from src.automation_scheduler_legacy.asof_line_movement_query import filter_line_movement_snapshots_as_of as _legacy_filter_line_movement_snapshots_as_of

    return _legacy_filter_line_movement_snapshots_as_of(
        [dict(row) for row in snapshots if isinstance(row, Mapping)],
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
    )


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
    from src.automation_scheduler_legacy.asof_line_movement_query import build_asof_line_movement_query_snapshot_from_sqlite as _legacy_build_asof_line_movement_query_snapshot_from_sqlite

    effective_limit = 100 if limit is None else int(limit)
    return _legacy_build_asof_line_movement_query_snapshot_from_sqlite(
        db_path,
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=effective_limit,
    )


def describe_asof_line_movement_query_engine() -> list[str]:
    from src.automation_scheduler_legacy.asof_line_movement_query import describe_asof_line_movement_query_engine as _legacy_describe_asof_line_movement_query_engine

    return _legacy_describe_asof_line_movement_query_engine()


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
    from src.automation_scheduler_legacy.asof_line_movement_query import load_line_movement_snapshots_from_sqlite as _legacy_load_line_movement_snapshots_from_sqlite

    return _legacy_load_line_movement_snapshots_from_sqlite(
        db_path,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )


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
    from src.automation_scheduler_legacy.line_movement_data_quality_dashboard import build_line_movement_data_quality_snapshot as _legacy_build_line_movement_data_quality_snapshot

    return _legacy_build_line_movement_data_quality_snapshot(
        snapshot_rows=snapshot_rows,
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )


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
    from src.automation_scheduler_legacy.line_movement_data_quality_dashboard import build_line_movement_data_quality_snapshot_from_sqlite as _legacy_build_line_movement_data_quality_snapshot_from_sqlite

    return _legacy_build_line_movement_data_quality_snapshot_from_sqlite(
        db_path,
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )


def describe_line_movement_data_quality_dashboard() -> list[str]:
    from src.automation_scheduler_legacy.line_movement_data_quality_dashboard import describe_line_movement_data_quality_dashboard as _legacy_describe_line_movement_data_quality_dashboard

    return _legacy_describe_line_movement_data_quality_dashboard()


def get_line_volatility_summary_from_sqlite(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    from src.automation_scheduler_legacy.historical_line_movement import get_line_volatility_summary_from_sqlite as _legacy_get_line_volatility_summary_from_sqlite

    return _legacy_get_line_volatility_summary_from_sqlite(conn)


def get_line_movement_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_line_movement_snapshot_for_dashboard as _legacy_get_line_movement_snapshot_for_dashboard

    return _legacy_get_line_movement_snapshot_for_dashboard(db_path)


def get_line_movement_readiness_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_line_movement_readiness_snapshot_for_dashboard as _legacy_get_line_movement_readiness_snapshot_for_dashboard

    return _legacy_get_line_movement_readiness_snapshot_for_dashboard(db_path)


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
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_line_movement_data_quality_snapshot_for_dashboard as _legacy_get_line_movement_data_quality_snapshot_for_dashboard

    return _legacy_get_line_movement_data_quality_snapshot_for_dashboard(
        snapshot_rows=snapshot_rows,
        db_path=db_path,
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )


def get_line_movement_import_contract_snapshot_for_dashboard(
    rows: list[dict[str, Any]] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_line_movement_import_contract_snapshot_for_dashboard as _legacy_get_line_movement_import_contract_snapshot_for_dashboard

    return _legacy_get_line_movement_import_contract_snapshot_for_dashboard(rows=rows, limit=limit)


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
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_asof_line_movement_query_snapshot_for_dashboard as _legacy_get_asof_line_movement_query_snapshot_for_dashboard

    return _legacy_get_asof_line_movement_query_snapshot_for_dashboard(
        snapshots=snapshots,
        db_path=db_path,
        event_id=event_id,
        hypothetical_bet_time=hypothetical_bet_time,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )


def get_line_volatility_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_line_volatility_snapshot_for_dashboard as _legacy_get_line_volatility_snapshot_for_dashboard

    return _legacy_get_line_volatility_snapshot_for_dashboard(db_path)


def get_volatility_result_breakdown_for_dashboard(
    db_path: str | Path,
    projection_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from src.automation_scheduler_legacy.streamlit_dashboard_data import get_volatility_result_breakdown_for_dashboard as _legacy_get_volatility_result_breakdown_for_dashboard

    return _legacy_get_volatility_result_breakdown_for_dashboard(db_path, projection_result=projection_result)


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
