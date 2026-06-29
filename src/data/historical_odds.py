from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS: tuple[str, ...] = (
    "sport",
    "league",
    "event_date",
    "home_team",
    "away_team",
    "selection",
)

CANONICAL_HISTORICAL_ODDS_OPTIONAL_FIELDS: tuple[str, ...] = (
    "event_id",
    "source_key",
    "source_file",
    "source_name",
    "bookmaker",
    "market",
    "market_type",
    "market_name",
    "odds",
    "odds_at_decision_time",
    "opening_odds",
    "closing_odds",
    "closing_line",
    "final_result",
    "home_score",
    "away_score",
    "winner",
    "profit_loss",
    "collected_at",
    "raw_event_id",
    "raw_market_name",
    "raw_selection_name",
    "raw_row_index",
    "season",
    "features",
)

SUPPORTED_IMPORTER_KEYS: list[str] = [
    "football_data_uk",
    "arnav_mlb_odds_scraper",
    "sportsbookreview_scraper",
]


def get_supported_importer_keys() -> list[str]:
    return list(SUPPORTED_IMPORTER_KEYS)


def _stable_hash_id(prefix: str, parts: Sequence[Any]) -> str:
    raw = prefix + ":" + "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    candidate = text
    if "/" in candidate:
        parts = candidate.split("/")
        if len(parts) == 3 and len(parts[0]) <= 2:
            day, month, year = parts
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text
    return parsed.date().isoformat()


def normalize_team_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return " ".join(text.replace("_", " ").split()).title()


def normalize_market_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "match winner": "moneyline",
        "moneyline": "moneyline",
        "spread": "spread",
        "run line": "runline",
        "over/under": "total",
        "total": "total",
        "1x2": "1x2",
    }
    return mapping.get(text, text)


def normalize_selection_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "o": "over",
        "over": "over",
        "u": "under",
        "under": "under",
        "home": "home",
        "away": "away",
        "yes": "yes",
        "no": "no",
        "draw": "draw",
    }
    return mapping.get(text, text)


def odds_to_implied_probability(odds: Any) -> float:
    try:
        value = float(odds)
    except (TypeError, ValueError):
        return 0.0
    if value == 0:
        return 0.0
    if value > 0:
        return round(100.0 / (value + 100.0), 6)
    return round(abs(value) / (abs(value) + 100.0), 6)


def validate_canonical_historical_odds_row(row: Mapping[str, Any]) -> dict[str, Any]:
    from src.automation_scheduler_legacy.historical_odds_importers import (
        validate_canonical_historical_odds_row as legacy_validate_canonical_historical_odds_row,
    )

    payload = dict(row)
    legacy_result = dict(legacy_validate_canonical_historical_odds_row(payload))
    missing_required_fields = list(legacy_result.get("missing_required_fields") or legacy_result.get("missing_fields") or [])
    warnings = list(legacy_result.get("warnings") or [])
    ok = bool(legacy_result.get("ok", not missing_required_fields))
    return {
        "ok": ok,
        "status": "accepted" if ok else "rejected",
        "missing_required_fields": missing_required_fields,
        "warnings": warnings,
        "row": payload,
    }


def _load_payload(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if isinstance(payload, Mapping):
                rows.append(dict(payload))
        return rows
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, Mapping)]
    if isinstance(payload, Mapping):
        return [dict(payload)]
    return []


def _build_football_data_rows(row: Mapping[str, Any], *, source_key: str, source_file: str | None) -> list[dict[str, Any]]:
    date = _normalize_date(row.get("Date") or row.get("event_date"))
    home_team = normalize_team_name(row.get("HomeTeam") or row.get("home_team"))
    away_team = normalize_team_name(row.get("AwayTeam") or row.get("away_team"))
    final_result = str(row.get("FTR") or row.get("final_result") or "").strip().upper()
    home_score = row.get("FTHG")
    away_score = row.get("FTAG")
    bookmaker = row.get("bookmaker") or row.get("Bookmaker") or "football-data"
    odds_map = [
        ("home", row.get("B365H") or row.get("home_odds") or row.get("H")),
        ("draw", row.get("B365D") or row.get("draw_odds") or row.get("D")),
        ("away", row.get("B365A") or row.get("away_odds") or row.get("A")),
    ]
    market = normalize_market_name(row.get("market") or row.get("market_type") or "1x2") or "1x2"
    rows: list[dict[str, Any]] = []
    for idx, (selection, odds) in enumerate(odds_map):
        selection_name = home_team if selection == "home" else away_team if selection == "away" else "Draw"
        rows.append(
            {
                "source_name": "Football-Data.co.uk",
                "source_key": source_key,
                "source_file": source_file,
                "sport": "soccer",
                "league": str(row.get("Div") or row.get("league") or "").strip(),
                "event_date": date,
                "home_team": home_team,
                "away_team": away_team,
                "market": market,
                "market_type": market,
                "market_name": market,
                "selection": selection_name if selection_name else selection,
                "odds": odds,
                "odds_at_decision_time": odds,
                "market_implied_probability": odds_to_implied_probability(odds),
                "final_result": final_result,
                "season": row.get("Season"),
                "bookmaker": bookmaker,
                "opening_odds": None,
                "closing_odds": row.get("closing_odds"),
                "home_score": home_score,
                "away_score": away_score,
                "winner": home_team if final_result == "H" else away_team if final_result == "A" else "Draw" if final_result == "D" else None,
                "profit_loss": row.get("profit_loss"),
                "collected_at": row.get("collected_at"),
                "raw_event_id": row.get("raw_event_id") or row.get("EventID") or row.get("event_id"),
                "raw_row_index": idx,
                "raw_market_name": row.get("market") or row.get("market_type") or "1x2",
                "raw_selection_name": selection,
                "validation_warnings": row.get("validation_warnings"),
                "features_known_at_decision_time": row.get("features_known_at_decision_time"),
            }
        )
    return rows


def _build_generic_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    source_key: str,
    source_file: str | None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        payload = dict(row)
        market = normalize_market_name(payload.get("market") or payload.get("market_type") or payload.get("market_name"))
        odds = payload.get("odds_at_decision_time") if payload.get("odds_at_decision_time") not in (None, "") else payload.get("odds")
        result.append(
            {
                "source_name": payload.get("source_name") or source_key,
                "source_key": source_key,
                "source_file": source_file or payload.get("source_file"),
                "sport": str(payload.get("sport") or "").strip().lower() or "unknown",
                "league": str(payload.get("league") or "").strip(),
                "event_date": _normalize_date(payload.get("event_date")),
                "home_team": normalize_team_name(payload.get("home_team")),
                "away_team": normalize_team_name(payload.get("away_team")),
                "market": market,
                "market_type": market,
                "market_name": market,
                "selection": normalize_selection_name(payload.get("selection")),
                "odds": odds,
                "odds_at_decision_time": odds,
                "market_implied_probability": odds_to_implied_probability(odds),
                "final_result": payload.get("final_result"),
                "season": payload.get("season"),
                "bookmaker": payload.get("bookmaker"),
                "opening_odds": payload.get("opening_odds"),
                "closing_odds": payload.get("closing_odds"),
                "home_score": payload.get("home_score"),
                "away_score": payload.get("away_score"),
                "winner": payload.get("winner"),
                "profit_loss": payload.get("profit_loss"),
                "collected_at": payload.get("collected_at"),
                "raw_event_id": payload.get("raw_event_id") or payload.get("event_id"),
                "raw_row_index": payload.get("raw_row_index", index),
                "raw_market_name": payload.get("raw_market_name") or payload.get("market"),
                "raw_selection_name": payload.get("raw_selection_name") or payload.get("selection"),
                "validation_warnings": payload.get("validation_warnings"),
                "features_known_at_decision_time": payload.get("features_known_at_decision_time"),
            }
        )
    return result


def import_historical_odds_file(*args: Any, source_file: str | None = None) -> list[dict[str, Any]]:
    from src.automation_scheduler_legacy.historical_odds_importers import (
        import_historical_odds_file as legacy_import_historical_odds_file,
    )

    if source_file is None:
        return legacy_import_historical_odds_file(*args)
    return legacy_import_historical_odds_file(*args, source_file=source_file)


def connect_historical_odds_db(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_historical_odds_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_imports (
            import_id TEXT PRIMARY KEY,
            source_key TEXT,
            source_name TEXT,
            source_file TEXT,
            imported_at TEXT,
            rows_seen INTEGER,
            rows_inserted INTEGER,
            rows_rejected INTEGER,
            warning_total INTEGER,
            projection_ready INTEGER,
            summary_json TEXT
        );

        CREATE TABLE IF NOT EXISTS historical_events (
            event_id TEXT PRIMARY KEY,
            source_key TEXT,
            source_file TEXT,
            sport TEXT,
            league TEXT,
            season TEXT,
            event_date TEXT,
            home_team TEXT,
            away_team TEXT,
            raw_event_id TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS historical_odds (
            odds_id TEXT PRIMARY KEY,
            event_id TEXT,
            source_key TEXT,
            source_file TEXT,
            source_name TEXT,
            sport TEXT,
            league TEXT,
            event_date TEXT,
            bookmaker TEXT,
            market TEXT,
            market_type TEXT,
            market_name TEXT,
            selection TEXT,
            odds REAL,
            odds_at_decision_time REAL,
            market_implied_probability REAL,
            opening_odds REAL,
            closing_odds REAL,
            closing_line REAL,
            collected_at TEXT,
            raw_market_name TEXT,
            raw_selection_name TEXT,
            raw_row_index INTEGER,
            final_result TEXT,
            home_score REAL,
            away_score REAL,
            winner TEXT,
            profit_loss REAL,
            features_json TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS historical_results (
            event_id TEXT PRIMARY KEY,
            final_result TEXT,
            home_score REAL,
            away_score REAL,
            winner TEXT,
            profit_loss REAL,
            created_at TEXT,
            updated_at TEXT
        );
        """
    )
    conn.commit()


def get_sqlite_table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    except sqlite3.DatabaseError:
        return counts
    for row in rows:
        name = str(row["name"])
        try:
            counts[name] = int(conn.execute(f"SELECT COUNT(*) AS cnt FROM [{name}]").fetchone()["cnt"])
        except sqlite3.DatabaseError:
            counts[name] = 0
    return counts


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    except sqlite3.DatabaseError:
        return set()
    columns: set[str] = set()
    for row in rows:
        try:
            name = row["name"] if isinstance(row, Mapping) else row[1]
        except Exception:
            continue
        if name is not None:
            columns.add(str(name))
    return columns


def _row_to_event_id(row: Mapping[str, Any]) -> str:
    return str(
        row.get("event_id")
        or row.get("raw_event_id")
        or _stable_hash_id(
            "evt",
            [
                row.get("source_key", ""),
                row.get("sport", ""),
                row.get("league", ""),
                row.get("event_date", ""),
                row.get("home_team", ""),
                row.get("away_team", ""),
            ],
        )
    )


def _row_to_odds_id(row: Mapping[str, Any], event_id: str) -> str:
    return _stable_hash_id(
        "odds",
        [
            event_id,
            row.get("market", "") or row.get("market_type", ""),
            row.get("selection", ""),
            row.get("bookmaker", ""),
            row.get("raw_row_index", 0),
        ],
    )


def import_historical_odds_file_to_sqlite(*args: Any, source_file: str | None = None) -> dict[str, Any]:
    if not args:
        raise TypeError("import_historical_odds_file_to_sqlite requires arguments")
    if isinstance(args[0], sqlite3.Connection):
        conn = args[0]
        source_key = str(args[1] or "local") if len(args) > 1 else "local"
        path = Path(args[2]) if len(args) > 2 else Path()
    else:
        path = Path(args[0])
        conn = args[1]
        source_key = str(args[2] or "local") if len(args) > 2 else "local"
    initialize_historical_odds_db(conn)
    rows = import_historical_odds_file(source_key, path, source_file=source_file)
    seen = len(rows)
    inserted = 0
    rejected = 0
    warning_total = 0
    now = _utc_now_iso()
    for row in rows:
        validation = validate_canonical_historical_odds_row(row)
        warning_total += len(validation.get("warnings", []))
        if not validation["ok"]:
            rejected += 1
            continue
        payload = dict(validation.get("row") or row)
        event_id = _row_to_event_id(payload)
        odds_id = _row_to_odds_id(payload, event_id)
        conn.execute(
            """
            INSERT OR REPLACE INTO historical_events (
                event_id, source_key, source_file, sport, league, season,
                event_date, home_team, away_team, raw_event_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                payload.get("source_key"),
                payload.get("source_file"),
                payload.get("sport"),
                payload.get("league"),
                payload.get("season"),
                payload.get("event_date"),
                payload.get("home_team"),
                payload.get("away_team"),
                payload.get("raw_event_id"),
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO historical_odds (
                odds_id, event_id, source_key, source_file, source_name,
                sport, league, event_date, bookmaker, market, market_type,
                market_name, selection, odds, odds_at_decision_time,
                market_implied_probability, opening_odds, closing_odds,
                closing_line, collected_at, raw_market_name, raw_selection_name,
                raw_row_index, final_result, home_score, away_score, winner,
                profit_loss, features_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                odds_id,
                event_id,
                payload.get("source_key"),
                payload.get("source_file"),
                payload.get("source_name"),
                payload.get("sport"),
                payload.get("league"),
                payload.get("event_date"),
                payload.get("bookmaker"),
                payload.get("market"),
                payload.get("market_type"),
                payload.get("market_name"),
                payload.get("selection"),
                payload.get("odds"),
                payload.get("odds_at_decision_time"),
                payload.get("market_implied_probability"),
                payload.get("opening_odds"),
                payload.get("closing_odds"),
                payload.get("closing_line"),
                payload.get("collected_at"),
                payload.get("raw_market_name"),
                payload.get("raw_selection_name"),
                payload.get("raw_row_index"),
                payload.get("final_result"),
                payload.get("home_score"),
                payload.get("away_score"),
                payload.get("winner"),
                payload.get("profit_loss"),
                json.dumps(payload.get("features") or payload.get("features_known_at_decision_time") or {}, sort_keys=True),
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO historical_results (
                event_id, final_result, home_score, away_score, winner,
                profit_loss, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                payload.get("final_result"),
                payload.get("home_score"),
                payload.get("away_score"),
                payload.get("winner"),
                payload.get("profit_loss"),
                now,
                now,
            ),
        )
        inserted += 1
    projection_ready = bool(inserted > 0 and rejected == 0)
    import_id = uuid.uuid4().hex
    conn.execute(
        """
        INSERT OR REPLACE INTO source_imports (
            import_id, source_key, source_name, source_file, imported_at,
            rows_seen, rows_inserted, rows_rejected, warning_total,
            projection_ready, summary_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            import_id,
            source_key,
            source_key,
            source_file or str(path),
            now,
            seen,
            inserted,
            rejected,
            warning_total,
            int(projection_ready),
            json.dumps(
                {
                    "rows_seen": seen,
                    "rows_inserted": inserted,
                    "rows_rejected": rejected,
                    "warning_total": warning_total,
                    "projection_ready": projection_ready,
                },
                sort_keys=True,
            ),
        ),
    )
    conn.commit()
    return {
        "ok": rejected == 0,
        "rows_seen": seen,
        "rows_inserted": inserted,
        "rows_rejected": rejected,
        "warning_total": warning_total,
        "import_id": import_id,
        "projection_ready": projection_ready,
    }


def query_historical_odds_rows(
    conn: sqlite3.Connection | str | Path,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    if not isinstance(conn, sqlite3.Connection):
        handle = connect_historical_odds_db(conn)
        try:
            return query_historical_odds_rows(
                handle,
                sport=sport,
                league=league,
                market=market,
                source_key=source_key,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        finally:
            handle.close()
    conditions: list[str] = []
    params: list[Any] = []
    if sport is not None:
        conditions.append("LOWER(o.sport) = LOWER(?)")
        params.append(sport)
    if league is not None:
        conditions.append("LOWER(o.league) = LOWER(?)")
        params.append(league)
    if source_key is not None:
        conditions.append("LOWER(o.source_key) = LOWER(?)")
        params.append(source_key)
    if start_date is not None:
        conditions.append("o.event_date >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append("o.event_date <= ?")
        params.append(end_date)
    if market is not None:
        columns = _get_table_columns(conn, "historical_odds")
        if "market" in columns and "market_type" in columns:
            market_expr = "LOWER(COALESCE(o.market, o.market_type, o.market_name)) = LOWER(?)"
        elif "market" in columns:
            market_expr = "LOWER(o.market) = LOWER(?)"
        elif "market_type" in columns:
            market_expr = "LOWER(o.market_type) = LOWER(?)"
        elif "market_name" in columns:
            market_expr = "LOWER(o.market_name) = LOWER(?)"
        else:
            market_expr = "1=0"
        conditions.append(market_expr)
        params.append(market)
    where = " AND ".join(conditions) if conditions else "1=1"
    try:
        rows = conn.execute(
            f"""
            SELECT
                o.*,
                e.season,
                e.home_team,
                e.away_team,
                e.raw_event_id,
                r.final_result AS result_final_result,
                r.home_score AS result_home_score,
                r.away_score AS result_away_score,
                r.winner AS result_winner,
                r.profit_loss AS result_profit_loss
            FROM historical_odds o
            LEFT JOIN historical_events e ON e.event_id = o.event_id
            LEFT JOIN historical_results r ON r.event_id = o.event_id
            WHERE {where}
            ORDER BY o.event_date, o.odds_id
            LIMIT ?
            """,
            [*params, max(0, int(limit))],
        ).fetchall()
    except sqlite3.DatabaseError:
        return []
    result: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        features = payload.get("features_json")
        if isinstance(features, str):
            try:
                payload["features"] = json.loads(features)
            except json.JSONDecodeError:
                payload["features"] = {}
        payload.setdefault("market", payload.get("market_type"))
        payload.setdefault("market_type", payload.get("market"))
        payload.setdefault("market_name", payload.get("market"))
        payload.setdefault("odds_at_decision_time", payload.get("odds"))
        if payload.get("odds") in (None, ""):
            payload["odds"] = payload.get("odds_at_decision_time")
        if payload.get("final_result") in (None, ""):
            payload["final_result"] = payload.get("result_final_result")
        if payload.get("home_score") in (None, ""):
            payload["home_score"] = payload.get("result_home_score")
        if payload.get("away_score") in (None, ""):
            payload["away_score"] = payload.get("result_away_score")
        if payload.get("winner") in (None, ""):
            payload["winner"] = payload.get("result_winner")
        if payload.get("profit_loss") in (None, ""):
            payload["profit_loss"] = payload.get("result_profit_loss")
        result.append(payload)
    return result


def summarize_historical_odds_db(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    rows = query_historical_odds_rows(conn)
    if not isinstance(conn, sqlite3.Connection):
        conn = connect_historical_odds_db(conn)
    counts = get_sqlite_table_counts(conn)
    sports = sorted({str(row.get("sport") or "UNKNOWN") for row in rows if row.get("sport")})
    leagues = sorted({str(row.get("league") or "UNKNOWN") for row in rows if row.get("league")})
    markets = sorted({str(row.get("market") or "UNKNOWN") for row in rows if row.get("market")})
    sources = sorted({str(row.get("source_key") or "UNKNOWN") for row in rows if row.get("source_key")})
    projection_ready = bool(rows) and counts.get("source_imports", 0) >= 1
    return {
        "ok": True,
        "table_counts": counts,
        "total_odds": counts.get("historical_odds", len(rows)),
        "total_events": counts.get("historical_events", len({row.get("event_id") for row in rows})),
        "sports": sports,
        "leagues": leagues,
        "markets": markets,
        "sources": sources,
        "projection_ready": projection_ready,
    }


def validate_sqlite_store(conn: sqlite3.Connection | str | Path) -> dict[str, Any]:
    if not isinstance(conn, sqlite3.Connection):
        conn = connect_historical_odds_db(conn)
    try:
        counts = get_sqlite_table_counts(conn)
    except sqlite3.DatabaseError as exc:
        return {"ok": False, "errors": [str(exc)], "warnings": []}
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
        "row_count": counts.get("historical_odds", 0),
        "table_counts": counts,
    }


def import_historical_odds_file_to_sqlite_alias(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return import_historical_odds_file_to_sqlite(*args, **kwargs)


def make_arrow_safe_value(value: Any) -> Any:
    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple, set, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def make_arrow_safe_table_rows(rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    for row in rows:
        new_row: dict[str, Any] = {}
        for key, value in row.items():
            new_row[key] = make_arrow_safe_value(value)
        result.append(new_row)
    return result


def make_historical_projection_metric_rows(summary: dict) -> list[dict]:
    return [
        {
            "rows_loaded": summary.get("rows_loaded", 0),
            "rows_converted": summary.get("rows_converted", 0),
            "bets": summary.get("bets", 0),
            "no_bets": summary.get("no_bets", 0),
            "profit_loss": summary.get("profit_loss", 0.0),
            "roi_percent": summary.get("roi_percent", 0.0),
            "max_drawdown_percent": summary.get("max_drawdown_percent", 0.0),
            "projection_ready": summary.get("projection_ready", False),
            "reason": summary.get("reason", ""),
        }
    ]


def get_historical_import_source_options() -> list[dict[str, Any]]:
    from src.data.historical_sources import get_historical_data_source_rows

    all_sources = get_historical_data_source_rows(include_rejected=False)
    options: list[dict[str, Any]] = []
    for src in all_sources:
        if src["status"] in ("remove",):
            continue
        options.append(
            {
                "source_key": src["source_key"],
                "source": src["name"],
                "decision": src["status"],
                "sports": src["sport"] if src["sport"] != "*" else "any",
                "formats": src["format"],
                "next_action": (
                    "Ready" if src["projection_ready"] else "Importer not built yet"
                ),
            }
        )
    return options


def save_historical_upload_for_import(
    source_key: str,
    filename: str,
    content: bytes | str,
    upload_dir: Path = Path("data/historical/uploads"),
) -> dict[str, Any]:
    safe_name = "".join(c for c in filename if c.isalnum() or c in (".", "_", "-"))
    if not safe_name:
        safe_name = "upload"
    file_path = upload_dir / source_key / safe_name
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        file_path.write_text(content, encoding="utf-8")
    else:
        file_path.write_bytes(content)

    return {
        "ok": True,
        "path": str(file_path),
        "source_key": source_key,
        "filename": safe_name,
        "size_bytes": file_path.stat().st_size,
    }


def import_historical_file_to_sqlite_for_dashboard(
    db_path: str | Path,
    source_key: str,
    file_path: str | Path,
    source_file: str | None = None,
) -> dict[str, Any]:
    from src.data.line_movement import initialize_line_movement_schema, upsert_line_snapshots_for_canonical_rows

    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)
    result = import_historical_odds_file_to_sqlite(conn, source_key, file_path, source_file=source_file)
    initialize_line_movement_schema(conn)
    lm_warnings: list[str] = []
    try:
        inserted_rows = result.get("rows_inserted", 0)
        if inserted_rows > 0:
            snap_rows = query_historical_odds_rows(conn, limit=inserted_rows + 100)
            if snap_rows:
                lm_result = upsert_line_snapshots_for_canonical_rows(conn, snap_rows)
                if lm_result.get("warnings"):
                    lm_warnings = list(lm_result["warnings"])
    except Exception as exc:
        lm_warnings.append(str(exc))

    conn.close()
    return {
        "ok": bool(result.get("ok")),
        "rows_seen": result.get("rows_seen", 0),
        "rows_inserted": result.get("rows_inserted", 0),
        "rows_rejected": result.get("rows_rejected", 0),
        "warning_total": result.get("warning_total", 0),
        "import_id": result.get("import_id", ""),
        "line_movement_warnings": lm_warnings,
    }


def get_historical_sqlite_snapshot_for_dashboard(db_path: str | Path) -> dict[str, Any]:
    from src.backtesting.historical_bridge import get_sqlite_backtest_filter_options

    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)
    counts: dict[str, int] = {}
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        name = row["name"]
        cnt = conn.execute(f"SELECT COUNT(*) AS c FROM [{name}]").fetchone()["c"]
        counts[name] = cnt

    db_summary = summarize_historical_odds_db(conn)
    filter_options = get_sqlite_backtest_filter_options(conn)
    validation = validate_sqlite_store(conn)
    conn.close()

    return {
        "ok": True,
        "db_path": str(db_path),
        "table_counts": counts,
        "db_summary": db_summary,
        "filter_options": filter_options,
        "validation": validation,
    }


def run_sqlite_projection_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
    model_probability: float | None = None,
    strategy_config: dict | None = None,
) -> dict[str, Any]:
    from src.backtesting.historical_bridge import run_sqlite_historical_backtest, summarize_sqlite_historical_backtest, get_sqlite_backtest_filter_options

    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)

    bridge_result = run_sqlite_historical_backtest(
        conn,
        sport=sport,
        league=league,
        market=market,
        source_key=source_key,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        model_probability=model_probability,
        strategy_config=strategy_config,
    )
    summary = summarize_sqlite_historical_backtest(bridge_result)
    filter_opts = get_sqlite_backtest_filter_options(conn)
    conn.close()

    return {
        "ok": bool(bridge_result.get("ok")),
        "summary": summary,
        "result": bridge_result,
        "filter_options": filter_opts,
    }


def get_sqlite_data_explorer_snapshot_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    from src.data.field_catalog import build_market_readiness_report, calculate_field_coverage, classify_market_family, get_required_field_groups_for_market, REQUIRED_FIELD_GROUPS

    result: dict[str, Any] = {
        "ok": False,
        "db_path": str(db_path),
        "filters": {
            "sport": sport,
            "league": league,
            "market": market,
            "source_key": source_key,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        },
        "total_rows": 0,
        "filter_options": {},
        "sports": [],
        "leagues": [],
        "markets": [],
        "source_keys": [],
        "market_families": {},
        "sample_rows": [],
        "field_coverage": {},
        "missing_field_groups": [],
        "readiness": {},
        "warnings": [],
    }
    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
        raw_rows = query_historical_odds_rows(
            conn,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        result["total_rows"] = len(raw_rows)
    except Exception as exc:
        result["warnings"].append(f"Could not open database: {exc}")
        return result

    rows = raw_rows
    sports = sorted({r.get("sport") for r in rows if r.get("sport")})
    leagues = sorted({r.get("league") for r in rows if r.get("league")})
    markets = sorted({r.get("market") for r in rows if r.get("market")})
    source_keys = sorted({r.get("source_key") for r in rows if r.get("source_key")})
    result["sports"] = sports
    result["leagues"] = leagues
    result["markets"] = markets
    result["source_keys"] = source_keys

    families: dict[str, int] = {}
    for row in rows:
        family = classify_market_family(row.get("market"), row.get("selection"))
        families[family] = families.get(family, 0) + 1
    result["market_families"] = {k: v for k, v in sorted(families.items(), key=lambda x: -x[1])}

    result["sample_rows"] = make_arrow_safe_table_rows(rows[: min(limit, 20)])
    all_groups = dict(REQUIRED_FIELD_GROUPS)
    coverage = calculate_field_coverage(rows, all_groups)
    result["field_coverage"] = coverage

    missing_groups: list[str] = []
    for group_name, fields in all_groups.items():
        for field in fields:
            entry = coverage.get(field)
            if entry and entry["status"] == "missing":
                missing_groups.append(f"{group_name} / {field}")
    result["missing_field_groups"] = missing_groups
    readiness = build_market_readiness_report(rows)
    result["readiness"] = readiness
    result["filter_options"] = {
        "sports": sports,
        "leagues": leagues,
        "markets": markets,
        "source_keys": source_keys,
    }
    result["ok"] = True
    if readiness.get("warnings"):
        result["warnings"].extend(readiness["warnings"])
    if missing_groups:
        result["warnings"].append(
            f"Missing field groups: {missing_groups[0]}"
            + (f" (+{len(missing_groups)-1} more)" if len(missing_groups) > 1 else "")
        )
    conn.close()
    return result


__all__ = [
    "CANONICAL_HISTORICAL_ODDS_OPTIONAL_FIELDS",
    "CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS",
    "SUPPORTED_IMPORTER_KEYS",
    "connect_historical_odds_db",
    "import_historical_odds_file",
    "import_historical_odds_file_to_sqlite",
    "import_historical_odds_file_to_sqlite_alias",
    "initialize_historical_odds_db",
    "normalize_market_name",
    "normalize_selection_name",
    "normalize_team_name",
    "odds_to_implied_probability",
    "get_historical_import_source_options",
    "get_historical_sqlite_snapshot_for_dashboard",
    "get_sqlite_data_explorer_snapshot_for_dashboard",
    "query_historical_odds_rows",
    "make_arrow_safe_table_rows",
    "make_arrow_safe_value",
    "make_historical_projection_metric_rows",
    "summarize_historical_odds_db",
    "validate_canonical_historical_odds_row",
    "validate_sqlite_store",
    "get_sqlite_table_counts",
    "import_historical_file_to_sqlite_for_dashboard",
    "run_sqlite_projection_for_dashboard",
    "save_historical_upload_for_import",
]
