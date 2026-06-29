"""
Phase 10H5 – Canonical Historical Odds Importers.

Convert raw historical odds/results files (CSV/JSON) into canonical
historical‑odds rows, ready for later SQLite storage (Phase 10H6).

Uses only stdlib modules: csv, json, pathlib.
No downloads, scraping, network calls, or database writes.
"""

from __future__ import annotations

import csv
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Canonical row field names
# ---------------------------------------------------------------------------

CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS: list[str] = [
    "source_name",
    "source_key",
    "source_file",
    "sport",
    "league",
    "event_date",
    "home_team",
    "away_team",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
    "final_result",
]

CANONICAL_HISTORICAL_ODDS_OPTIONAL_FIELDS: list[str] = [
    "season",
    "bookmaker",
    "opening_odds",
    "closing_odds",
    "home_score",
    "away_score",
    "winner",
    "profit_loss",
    "collected_at",
    "raw_event_id",
    "raw_row_index",
    "raw_market_name",
    "raw_selection_name",
    "validation_warnings",
    "features_known_at_decision_time",
]

SUPPORTED_IMPORTER_KEYS: list[str] = [
    "football_data_uk",
    "arnav_mlb_odds_scraper",
    "sportsbookreview_scraper",
]


def _normalize_football_data_event_date(raw: str) -> str:
    """Convert Football-Data date (dd/mm/YYYY) to ISO (YYYY-MM-DD)."""
    if not raw:
        return raw
    if "/" in raw:
        try:
            return datetime.strptime(raw, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return raw

# ---------------------------------------------------------------------------
# Odds conversion helpers
# ---------------------------------------------------------------------------


def american_to_implied_probability(odds: int | float) -> float:
    """Convert American odds to implied probability.

    Positive odds: 100 / (odds + 100)
    Negative odds: -odds / (-odds + 100)
    """
    if odds is None:
        raise TypeError("odds cannot be None")
    o = float(odds)
    if o > 0:
        return 100.0 / (o + 100.0)
    if o < 0:
        return -o / (-o + 100.0)
    return 0.0  # odds == 0 is degenerate


def decimal_to_implied_probability(odds: int | float) -> float:
    """Convert decimal odds to implied probability (1 / odds)."""
    if odds is None:
        raise TypeError("odds cannot be None")
    o = float(odds)
    if o <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {o}")
    return 1.0 / o


def odds_to_implied_probability(
    odds: int | float,
    odds_format: str = "auto",
) -> float:
    """Convert odds of various formats to implied probability.

    When *odds_format* is ``"auto"``, the function tries to guess the
    format: values > 1 are treated as decimal odds, everything else is
    treated as American odds (including negative values).
    """
    if odds_format == "decimal":
        return decimal_to_implied_probability(odds)
    if odds_format == "american":
        return american_to_implied_probability(odds)
    # auto‑detection
    if float(odds) > 1.0:
        return decimal_to_implied_probability(odds)
    return american_to_implied_probability(odds)


# ---------------------------------------------------------------------------
# Simple string normalisers (basic cleaning, no look‑up table)
# ---------------------------------------------------------------------------


def normalize_team_name(value: Any) -> str:
    """Return a trimmed, lower‑cased team name string."""
    return str(value).strip().lower()


def normalize_market_name(value: Any) -> str:
    """Return a trimmed, lower‑cased market name string."""
    return str(value).strip().lower()


def normalize_selection_name(value: Any) -> str:
    """Return a trimmed, lower‑cased selection name string."""
    return str(value).strip().lower()


# ---------------------------------------------------------------------------
# Core canonical row builder
# ---------------------------------------------------------------------------


def build_canonical_historical_odds_row(**kwargs: Any) -> dict[str, Any]:
    """Build a canonical historical‑odds row from keyword arguments.

    The returned dict always contains every required field (some may be
    ``None``).  The caller must call :func:`validate_canonical_historical_odds_row`
    afterwards.
    """
    row: dict[str, Any] = {}
    for field in CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS:
        row[field] = kwargs.get(field)
    for field in CANONICAL_HISTORICAL_ODDS_OPTIONAL_FIELDS:
        row[field] = kwargs.get(field)

    # compute implied probability from odds if not already provided
    odds = row.get("odds_at_decision_time")
    prob = row.get("market_implied_probability")
    if odds is not None and prob is None:
        try:
            row["market_implied_probability"] = odds_to_implied_probability(
                odds, kwargs.get("odds_format", "auto")
            )
        except (TypeError, ValueError, ZeroDivisionError):
            row["market_implied_probability"] = None
    return row


# ---------------------------------------------------------------------------
# Row validation
# ---------------------------------------------------------------------------


def validate_canonical_historical_odds_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Check whether *row* satisfies the canonical schema.

    Returns a dict with keys ``ok``, ``missing_required_fields``,
    and ``warnings``.
    """
    missing: list[str] = []
    warnings: list[str] = []
    for field in CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS:
        if row.get(field) is None:
            missing.append(field)

    # numeric checks
    odds = row.get("odds_at_decision_time")
    if odds is not None:
        try:
            float(odds)
        except (TypeError, ValueError):
            warnings.append("odds_at_decision_time is not numeric")
    prob = row.get("market_implied_probability")
    if prob is not None:
        try:
            p = float(prob)
            if not 0.0 <= p <= 1.0:
                warnings.append(
                    f"market_implied_probability {p} outside [0,1]"
                )
        except (TypeError, ValueError):
            warnings.append("market_implied_probability is not numeric")

    # leakage: features_known_at_decision_time must not contain prohibited
    # fields
    forbidden = {
        "final_result",
        "profit_loss",
        "closing_line",
        "closing_odds",
        "clv",
    }
    feat = row.get("features_known_at_decision_time")
    if isinstance(feat, (list, tuple)):
        for f in feat:
            if f in forbidden:
                warnings.append(
                    f"features_known_at_decision_time contains leaking field {f!r}"
                )

    ok = len(missing) == 0
    return {
        "ok": bool(ok),
        "missing_required_fields": missing,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Football‑Data.co.uk CSV importer
# ---------------------------------------------------------------------------

FOOTBALL_DATA_ODDS_COLUMN_GROUPS: list[tuple[str, str, str]] = [
    ("B365H", "B365D", "B365A"),
    ("AvgH", "AvgD", "AvgA"),
    ("MaxH", "MaxD", "MaxA"),
]


def _detect_odds_columns(
    header: list[str],
) -> tuple[str, str, str] | None:
    for h, d, a in FOOTBALL_DATA_ODDS_COLUMN_GROUPS:
        if h in header and d in header and a in header:
            return (h, d, a)
    return None


def import_football_data_csv(
    path: str | Path,
    source_file: str | None = None,
) -> list[dict[str, Any]]:
    """Read a Football‑Data.co.uk CSV and return canonical historical‑odds rows."""
    rows: list[dict[str, Any]] = []
    path_obj = Path(path)
    source_file_str = source_file or path_obj.name

    with open(path_obj, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return rows
        header = reader.fieldnames
        odds_cols = _detect_odds_columns(header)
        if odds_cols is None:
            # no odds columns → nothing to import
            return rows
        oh, od, oa = odds_cols

        for raw_idx, raw in enumerate(reader):
            league = raw.get("Div", "").strip()
            event_date = _normalize_football_data_event_date(raw.get("Date", "").strip())
            home_team = normalize_team_name(raw.get("HomeTeam", ""))
            away_team = normalize_team_name(raw.get("AwayTeam", ""))
            try:
                home_score = int(raw.get("FTHG", 0)) if raw.get("FTHG") else None
            except (ValueError, TypeError):
                home_score = None
            try:
                away_score = int(raw.get("FTAG", 0)) if raw.get("FTAG") else None
            except (ValueError, TypeError):
                away_score = None
            final_result = raw.get("FTR", "").strip()
            winner: str | None = None
            if final_result == "H":
                winner = home_team
            elif final_result == "A":
                winner = away_team

            for outcome, col_name, selection_label in [
                ("home", oh, "home"),
                ("draw", od, "draw"),
                ("away", oa, "away"),
            ]:
                odds_str = raw.get(col_name, "").strip()
                if not odds_str:
                    continue
                try:
                    decimal_odds = float(odds_str)
                except (ValueError, TypeError):
                    continue
                if decimal_odds <= 1.0:
                    continue

                row = build_canonical_historical_odds_row(
                    source_name="Football-Data.co.uk",
                    source_key="football_data_uk",
                    source_file=source_file_str,
                    sport="soccer",
                    league=league or "unknown",
                    event_date=event_date,
                    home_team=home_team,
                    away_team=away_team,
                    market="1x2",
                    selection=selection_label,
                    odds_at_decision_time=decimal_odds,
                    odds_format="decimal",
                    home_score=home_score,
                    away_score=away_score,
                    winner=winner,
                    final_result=final_result,
                    raw_row_index=raw_idx,
                )
                rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# MLB odds JSON importer (ArnavSaraogi style, flexible)
# ---------------------------------------------------------------------------


def _extract_events_from_json(data: Any) -> list[dict[str, Any]]:
    """Try to extract a list of event dicts from a JSON payload."""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("events", "items", "data", "rows"):
        val = data.get(key)
        if isinstance(val, list):
            return val
    # fallback: treat the whole dict as a single event
    return [data]


def _extract_bookmakers_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("bookmakers", "books", "sportsbooks"):
        val = event.get(key)
        if isinstance(val, list):
            return val
    return []


def _extract_markets_from_bookmaker(
    bookmaker: dict[str, Any],
) -> list[dict[str, Any]]:
    for key in ("markets", "market"):
        val = bookmaker.get(key)
        if isinstance(val, list):
            return val
    return []


def _extract_outcomes_from_market(market: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("outcomes", "outcome", "selections"):
        val = market.get(key)
        if isinstance(val, list):
            return val
    return []


def import_mlb_odds_json(
    path: str | Path,
    source_file: str | None = None,
) -> list[dict[str, Any]]:
    """Read an MLB odds JSON file and return canonical historical‑odds rows."""
    rows: list[dict[str, Any]] = []
    path_obj = Path(path)
    source_file_str = source_file or path_obj.name

    with open(path_obj, encoding="utf-8") as f:
        data = json.load(f)

    events = _extract_events_from_json(data)
    for raw_idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        league = (
            event.get("league")
            or event.get("sport")
            or "mlb"
        )
        home_team = normalize_team_name(
            event.get("home_team")
            or event.get("homeTeam")
            or event.get("home")
            or ""
        )
        away_team = normalize_team_name(
            event.get("away_team")
            or event.get("awayTeam")
            or event.get("away")
            or ""
        )
        event_date = (
            event.get("event_date")
            or event.get("commence_time")
            or event.get("date")
            or event.get("start_time")
            or ""
        )
        raw_event_id = event.get("raw_event_id") or event.get("event_id")
        bookmakers = _extract_bookmakers_from_event(event)
        if not bookmakers:
            # no bookmaker structure → treat event itself as market?
            continue
        for bookmaker in bookmakers:
            bm_name = bookmaker.get("name") or bookmaker.get("title") or ""
            markets = _extract_markets_from_bookmaker(bookmaker)
            for market in markets:
                market_key = market.get("key") or market.get("name") or ""
                outcomes = _extract_outcomes_from_market(market)
                for outcome in outcomes:
                    selection = (
                        outcome.get("name")
                        or outcome.get("selection")
                        or ""
                    )
                    price = outcome.get("price") or outcome.get("odds")
                    if price is None:
                        continue
                    try:
                        price_f = float(price)
                    except (ValueError, TypeError):
                        continue
                    row = build_canonical_historical_odds_row(
                        source_name="ArnavSaraogi MLB Odds Scraper",
                        source_key="arnav_mlb_odds_scraper",
                        source_file=source_file_str,
                        sport="baseball",
                        league=league,
                        event_date=event_date,
                        home_team=home_team,
                        away_team=away_team,
                        market=normalize_market_name(market_key),
                        selection=normalize_selection_name(selection),
                        odds_at_decision_time=price_f,
                        odds_format="auto",
                        bookmaker=bm_name,
                        raw_event_id=str(raw_event_id) if raw_event_id else None,
                        raw_row_index=raw_idx,
                    )
                    rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# SportsbookReview‑style file importer
# ---------------------------------------------------------------------------


def _parse_sbr_json(
    path: Path,
    source_file_str: str,
) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    events = _extract_events_from_json(data)
    rows: list[dict[str, Any]] = []
    for raw_idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        sport = event.get("sport") or "*"
        league = event.get("league") or ""
        home_team = normalize_team_name(
            event.get("home_team") or event.get("homeTeam") or event.get("home") or ""
        )
        away_team = normalize_team_name(
            event.get("away_team") or event.get("awayTeam") or event.get("away") or ""
        )
        event_date = (
            event.get("event_date")
            or event.get("date")
            or event.get("commence_time")
            or ""
        )
        market = normalize_market_name(event.get("market") or "")
        selection = normalize_selection_name(event.get("selection") or "")
        odds_raw = event.get("odds") or event.get("price")
        if odds_raw is None:
            continue
        try:
            odds_f = float(odds_raw)
        except (ValueError, TypeError):
            continue
        row = build_canonical_historical_odds_row(
            source_name="SportsbookReview Scraper Dataset",
            source_key="sportsbookreview_scraper",
            source_file=source_file_str,
            sport=sport,
            league=league,
            event_date=event_date,
            home_team=home_team,
            away_team=away_team,
            market=market,
            selection=selection,
            odds_at_decision_time=odds_f,
            odds_format="auto",
            raw_row_index=raw_idx,
        )
        rows.append(row)
    return rows


def _parse_sbr_csv(
    path: Path,
    source_file_str: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return rows
        for raw_idx, raw in enumerate(reader):
            sport = raw.get("sport", "*").strip()
            league = raw.get("league", "").strip()
            home_team = normalize_team_name(raw.get("home_team") or "")
            away_team = normalize_team_name(raw.get("away_team") or "")
            event_date = raw.get("date") or raw.get("event_date") or ""
            market = normalize_market_name(raw.get("market") or "")
            selection = normalize_selection_name(raw.get("selection") or "")
            odds_str = raw.get("odds") or raw.get("price") or ""
            if not odds_str:
                continue
            try:
                odds_f = float(odds_str)
            except (ValueError, TypeError):
                continue
            row = build_canonical_historical_odds_row(
                source_name="SportsbookReview Scraper Dataset",
                source_key="sportsbookreview_scraper",
                source_file=source_file_str,
                sport=sport,
                league=league,
                event_date=event_date,
                home_team=home_team,
                away_team=away_team,
                market=market,
                selection=selection,
                odds_at_decision_time=odds_f,
                odds_format="auto",
                raw_row_index=raw_idx,
            )
            rows.append(row)
    return rows


def import_sbr_odds_file(
    path: str | Path,
    source_file: str | None = None,
) -> list[dict[str, Any]]:
    """Read a SportsbookReview‑style odds file (CSV or JSON) and return canonical rows."""
    path_obj = Path(path)
    source_file_str = source_file or path_obj.name
    if path_obj.suffix.lower() in (".json",):
        return _parse_sbr_json(path_obj, source_file_str)
    # default to CSV
    return _parse_sbr_csv(path_obj, source_file_str)


# ---------------------------------------------------------------------------
# Router function
# ---------------------------------------------------------------------------


def import_historical_odds_file(
    source_key: str,
    path: str | Path,
    source_file: str | None = None,
) -> list[dict[str, Any]]:
    """Import an odds file whose source is identified by *source_key*.

    Supported keys: ``football_data_uk``, ``arnav_mlb_odds_scraper``,
    ``sportsbookreview_scraper``.

    Raises :exc:`ValueError` for unknown keys.
    """
    if source_key == "football_data_uk":
        return import_football_data_csv(path, source_file=source_file)
    if source_key == "arnav_mlb_odds_scraper":
        return import_mlb_odds_json(path, source_file=source_file)
    if source_key == "sportsbookreview_scraper":
        return import_sbr_odds_file(path, source_file=source_file)
    msg = f"Unsupported source_key {source_key!r}. Supported: {SUPPORTED_IMPORTER_KEYS}"
    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Summary / helper functions
# ---------------------------------------------------------------------------


def summarize_imported_historical_rows(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a summary dictionary for the imported *rows*."""
    if not rows:
        return {
            "ok": False,
            "rows": 0,
            "sports": [],
            "leagues": [],
            "markets": [],
            "sources": [],
            "missing_required_total": 0,
            "warning_total": 0,
            "projection_ready": False,
            "reason": "no rows",
        }
    sports: set[str] = set()
    leagues: set[str] = set()
    markets: set[str] = set()
    sources: set[str] = set()
    missing_total = 0
    warning_total = 0
    for r in rows:
        if r.get("sport"):
            sports.add(r["sport"])
        if r.get("league"):
            leagues.add(r["league"])
        if r.get("market"):
            markets.add(r["market"])
        if r.get("source_name"):
            sources.add(r["source_name"])
        val = validate_canonical_historical_odds_row(r)
        if not val["ok"]:
            missing_total += len(val["missing_required_fields"])
        warning_total += len(val["warnings"])
    projection_ready = bool(rows) and missing_total == 0
    reason = ""
    if not projection_ready:
        reason = (
            f"missing_required_total={missing_total} "
            f"(across {len(rows)} rows)"
        )
    return {
        "ok": True,
        "rows": len(rows),
        "sports": sorted(sports),
        "leagues": sorted(leagues),
        "markets": sorted(markets),
        "sources": sorted(sources),
        "missing_required_total": missing_total,
        "warning_total": warning_total,
        "projection_ready": projection_ready,
        "reason": reason,
    }


def get_supported_importer_keys() -> list[str]:
    """Return the list of supported source keys."""
    return list(SUPPORTED_IMPORTER_KEYS)
