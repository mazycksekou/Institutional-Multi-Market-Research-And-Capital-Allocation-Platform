"""
Phase 10H23 – Line Movement Data Quality Dashboard.

Summarizes whether local line movement data is ready for a real connector.
No vendor connector, no paid data, no scraping, no external API calls,
no writes to SQLite, no schema changes.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Phase marker
# ---------------------------------------------------------------------------

LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION: str = "10H23"

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

QUALITY_DUPLICATE_FIELDS: list[str] = [
    "event_id",
    "bookmaker",
    "market_family",
    "market",
    "selection",
    "snapshot_label",
    "snapshot_time",
]

QUALITY_GROUP_DEFAULT_FIELDS: list[str] = [
    "event_id",
    "sport",
    "league",
    "event_date",
    "home_team",
    "away_team",
    "bookmaker",
    "market_family",
    "market",
    "selection",
    "snapshot_label",
    "snapshot_time",
]


def normalize_line_movement_quality_value(value: Any) -> str:
    """Convert *value* to a stable JSON-safe string, never raising."""
    try:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (list, dict)):
            return json.dumps(value, sort_keys=True, default=str)
        s = str(value).strip()
        return s
    except Exception:
        return str(value)


def is_missing_quality_value(value: Any) -> bool:
    """Return True if *value* is None, blank, or whitespace-only after normalization."""
    s = normalize_line_movement_quality_value(value)
    return not s.strip()


def build_line_movement_quality_group_key(
    row: Any,
    fields: Sequence[str] | None = None,
) -> str:
    """Build a deterministic case-insensitive grouping key from *row*.

    Non-dict rows do not crash – an empty string is returned.
    """
    if not isinstance(row, dict):
        return ""

    use_fields = fields if fields is not None else QUALITY_GROUP_DEFAULT_FIELDS
    parts: list[str] = []
    for field in use_fields:
        raw = row.get(field, "")
        normalized = normalize_line_movement_quality_value(raw)
        # Collapse whitespace, lowercase
        cleaned = " ".join(normalized.lower().split())
        parts.append(cleaned)
    return "|".join(parts)


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

_COVERAGE_FIELDS: list[str] = [
    "event_id",
    "snapshot_time",
    "market_family",
    "bookmaker",
    "sport",
    "market",
    "selection",
]


def _count_missing(rows: list[dict], field: str) -> int:
    return sum(1 for r in rows if is_missing_quality_value(r.get(field)))


def _collect_nonblank(rows: list[dict], field: str) -> list[str]:
    seen: set[str] = set()
    for r in rows:
        v = normalize_line_movement_quality_value(r.get(field))
        if v and v.strip():
            seen.add(v.lower())
    return sorted(seen)


def summarize_line_movement_quality_coverage(
    snapshot_rows: Any,
) -> dict[str, Any]:
    """Return coverage metrics for a list of historical_line_snapshots-style dicts.

    Empty / non‑list input does not crash.
    """
    if not isinstance(snapshot_rows, list):
        snapshot_rows = []
        if snapshot_rows is not None:
            snapshot_rows = []

    total = len(snapshot_rows)

    # Ensure all items are dicts
    safe_rows: list[dict] = []
    for r in snapshot_rows:
        if isinstance(r, dict):
            safe_rows.append(r)

    result: dict[str, Any] = {
        "ok": True,
        "version": LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION,
        "total_snapshots": total,
        "linked_snapshots": 0,
        "unlinked_snapshots": total,
        "missing_event_id_count": _count_missing(safe_rows, "event_id"),
        "missing_snapshot_time_count": _count_missing(safe_rows, "snapshot_time"),
        "missing_market_family_count": _count_missing(safe_rows, "market_family"),
        "missing_bookmaker_count": _count_missing(safe_rows, "bookmaker"),
        "missing_sport_count": _count_missing(safe_rows, "sport"),
        "missing_market_count": _count_missing(safe_rows, "market"),
        "missing_selection_count": _count_missing(safe_rows, "selection"),
        "sports": _collect_nonblank(safe_rows, "sport"),
        "market_families": _collect_nonblank(safe_rows, "market_family"),
        "bookmakers": _collect_nonblank(safe_rows, "bookmaker"),
        "snapshot_labels": _collect_nonblank(safe_rows, "snapshot_label"),
        "warnings": [],
    }

    # linked/unlinked
    linked_count = sum(
        1 for r in safe_rows if not is_missing_quality_value(r.get("event_id"))
    )
    result["linked_snapshots"] = linked_count
    result["unlinked_snapshots"] = total - linked_count

    if total == 0:
        result["warnings"].append("no_snapshots")

    return result


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

_DUPLICATE_GROUP_LIMIT = 100


def detect_line_movement_duplicate_snapshots(
    snapshot_rows: Any,
) -> dict[str, Any]:
    """Detect groups of snapshots that share the same identifying key.

    Duplicate key fields: event_id, bookmaker, market_family, market,
    selection, snapshot_label, snapshot_time.
    """
    if not isinstance(snapshot_rows, list):
        snapshot_rows = []
        if snapshot_rows is not None:
            snapshot_rows = []

    groups: dict[str, list[dict]] = {}
    for r in snapshot_rows:
        if not isinstance(r, dict):
            continue
        key = build_line_movement_quality_group_key(r, fields=QUALITY_DUPLICATE_FIELDS)
        if key in groups:
            groups[key].append(r)
        else:
            groups[key] = [r]

    duplicate_groups: list[dict] = []
    duplicate_total = 0

    for key, grp in groups.items():
        if len(grp) >= 2:
            duplicate_total += len(grp)
            if len(duplicate_groups) < _DUPLICATE_GROUP_LIMIT:
                first = grp[0]
                duplicate_groups.append(
                    {
                        "duplicate_key": key,
                        "count": len(grp),
                        "snapshot_ids": [
                            normalize_line_movement_quality_value(r.get("snapshot_id", ""))
                            for r in grp
                        ],
                        "event_id": normalize_line_movement_quality_value(first.get("event_id", "")),
                        "bookmaker": normalize_line_movement_quality_value(first.get("bookmaker", "")),
                        "market_family": normalize_line_movement_quality_value(first.get("market_family", "")),
                        "market": normalize_line_movement_quality_value(first.get("market", "")),
                        "selection": normalize_line_movement_quality_value(first.get("selection", "")),
                        "snapshot_label": normalize_line_movement_quality_value(first.get("snapshot_label", "")),
                        "snapshot_time": normalize_line_movement_quality_value(first.get("snapshot_time", "")),
                    }
                )

    warnings: list[str] = []
    if duplicate_total > 0:
        warnings.append(f"Found {len(duplicate_groups)} duplicate group(s) "
                         f"with {duplicate_total} total duplicate snapshots.")

    return {
        "ok": True,
        "version": LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_snapshot_count": duplicate_total,
        "duplicate_groups": duplicate_groups,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Missing links
# ---------------------------------------------------------------------------

_MISSING_LINK_DISPLAY_LIMIT = 100


def summarize_line_movement_missing_links(
    snapshot_rows: Any,
) -> dict[str, Any]:
    """Count and list rows where event_id is blank/null/whitespace."""
    if not isinstance(snapshot_rows, list):
        snapshot_rows = []
        if snapshot_rows is not None:
            snapshot_rows = []

    total = len(snapshot_rows)
    safe_rows: list[dict] = [
        r for r in snapshot_rows if isinstance(r, dict)
    ]

    missing_rows: list[dict] = []
    missing_count = 0

    for idx, r in enumerate(safe_rows):
        if is_missing_quality_value(r.get("event_id")):
            missing_count += 1
            if len(missing_rows) < _MISSING_LINK_DISPLAY_LIMIT:
                missing_rows.append(
                    {
                        "row_index": idx,
                        "snapshot_id": normalize_line_movement_quality_value(
                            r.get("snapshot_id", "")
                        ),
                        "source_key": normalize_line_movement_quality_value(
                            r.get("source_key", "")
                        ),
                        "source_file": normalize_line_movement_quality_value(
                            r.get("source_file", "")
                        ),
                        "sport": normalize_line_movement_quality_value(
                            r.get("sport", "")
                        ),
                        "league": normalize_line_movement_quality_value(
                            r.get("league", "")
                        ),
                        "event_date": normalize_line_movement_quality_value(
                            r.get("event_date", "")
                        ),
                        "home_team": normalize_line_movement_quality_value(
                            r.get("home_team", "")
                        ),
                        "away_team": normalize_line_movement_quality_value(
                            r.get("away_team", "")
                        ),
                        "bookmaker": normalize_line_movement_quality_value(
                            r.get("bookmaker", "")
                        ),
                        "market_family": normalize_line_movement_quality_value(
                            r.get("market_family", "")
                        ),
                        "market": normalize_line_movement_quality_value(
                            r.get("market", "")
                        ),
                        "selection": normalize_line_movement_quality_value(
                            r.get("selection", "")
                        ),
                        "snapshot_time": normalize_line_movement_quality_value(
                            r.get("snapshot_time", "")
                        ),
                    }
                )

    warnings: list[str] = []
    if missing_count > 0:
        warnings.append(f"{missing_count} snapshot(s) have missing event_id.")
    if total == 0:
        warnings.append("no_snapshots")

    return {
        "ok": True,
        "version": LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION,
        "total_snapshots": total,
        "missing_link_count": missing_count,
        "linked_count": total - missing_count,
        "missing_link_rows": missing_rows,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Books, markets, sports summary
# ---------------------------------------------------------------------------


def summarize_line_movement_books_markets_sports(
    snapshot_rows: Any,
) -> dict[str, Any]:
    """Aggregate distinct values and counts of sports, market_families, bookmakers, markets.

    Excludes blank values.
    """
    if not isinstance(snapshot_rows, list):
        snapshot_rows = []
        if snapshot_rows is not None:
            snapshot_rows = []

    safe_rows: list[dict] = [
        r for r in snapshot_rows if isinstance(r, dict)
    ]

    sports_counter: Counter[str] = Counter()
    market_families_counter: Counter[str] = Counter()
    bookmakers_counter: Counter[str] = Counter()
    markets_counter: Counter[str] = Counter()

    for r in safe_rows:
        s = normalize_line_movement_quality_value(r.get("sport", ""))
        if s.strip():
            lower_s = s.lower()
            sports_counter[lower_s] += 1

        mf = normalize_line_movement_quality_value(r.get("market_family", ""))
        if mf.strip():
            lower_mf = mf.lower()
            market_families_counter[lower_mf] += 1

        bk = normalize_line_movement_quality_value(r.get("bookmaker", ""))
        if bk.strip():
            lower_bk = bk.lower()
            bookmakers_counter[lower_bk] += 1

        mk = normalize_line_movement_quality_value(r.get("market", ""))
        if mk.strip():
            lower_mk = mk.lower()
            markets_counter[lower_mk] += 1

    return {
        "ok": True,
        "version": LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION,
        "sports": sorted(sports_counter.keys()),
        "sport_count": len(sports_counter),
        "market_families": sorted(market_families_counter.keys()),
        "market_family_count": len(market_families_counter),
        "bookmakers": sorted(bookmakers_counter.keys()),
        "bookmaker_count": len(bookmakers_counter),
        "markets": sorted(markets_counter.keys()),
        "market_count": len(markets_counter),
        "sports_by_snapshot_count": dict(sports_counter.most_common()),
        "market_families_by_snapshot_count": dict(market_families_counter.most_common()),
        "bookmakers_by_snapshot_count": dict(bookmakers_counter.most_common()),
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


def build_line_movement_quality_readiness(
    coverage: dict[str, Any],
    duplicate_summary: dict[str, Any],
    missing_links: dict[str, Any],
    asof_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Determine overall readiness based on coverage, duplicates, missing links, and optional as-of summary."""
    reasons: list[str] = []
    warnings: list[str] = []

    total_snapshots = coverage.get("total_snapshots", 0)
    linked_snapshots = coverage.get("linked_snapshots", 0)
    missing_snapshot_time = coverage.get("missing_snapshot_time_count", 0)
    missing_market_family = coverage.get("missing_market_family_count", 0)
    missing_bookmaker = coverage.get("missing_bookmaker_count", 0)
    missing_sport = coverage.get("missing_sport_count", 0)
    missing_market = coverage.get("missing_market_count", 0)

    duplicate_snapshot_count = duplicate_summary.get("duplicate_snapshot_count", 0)

    if total_snapshots == 0:
        reasons.append("no_snapshots")
    if linked_snapshots == 0:
        reasons.append("missing_linked_events")
    if missing_snapshot_time > 0:
        reasons.append("missing_snapshot_time")
    if missing_market_family > 0:
        reasons.append("missing_market_family")
    if missing_bookmaker > 0:
        reasons.append("missing_bookmaker")
    if duplicate_snapshot_count > 0:
        reasons.append("duplicate_snapshots")
    if missing_sport > 0:
        reasons.append("missing_sports")
    if missing_market > 0:
        reasons.append("missing_markets")

    if asof_summary is not None:
        future_count = asof_summary.get("future_snapshots", 0)
        invalid_count = asof_summary.get("invalid_time_snapshots", 0)
        if future_count > 0:
            warnings.append(
                f"{future_count} future snapshot(s) filtered. "
                "They are not used unless hypothetical_bet_time is later."
            )
        if invalid_count > 0:
            warnings.append(
                f"{invalid_count} snapshot(s) had unparseable times and were excluded."
            )

    ready = bool(
        total_snapshots > 0
        and linked_snapshots > 0
        and missing_snapshot_time == 0
        and missing_market_family == 0
        and missing_bookmaker == 0
        and duplicate_snapshot_count == 0
    )

    if ready and not warnings:
        readiness_level = "strong"
        warnings.append("All checks passed.")
    elif ready:
        readiness_level = "usable"
    else:
        readiness_level = "blocked"

    return {
        "ready": ready,
        "readiness_level": readiness_level,
        "reasons": reasons,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Main in-memory dashboard snapshot
# ---------------------------------------------------------------------------


def build_line_movement_data_quality_snapshot(
    snapshot_rows: Any = None,
    hypothetical_bet_time: Any = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Return a complete data quality snapshot from in-memory rows.

    No SQL writes, no vendor connector, no paid data import.
    """
    version = LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION
    messages = describe_line_movement_data_quality_dashboard()
    warnings: list[str] = []

    if not isinstance(snapshot_rows, list):
        snapshot_rows = list(snapshot_rows) if snapshot_rows else []

    coverage = summarize_line_movement_quality_coverage(snapshot_rows)
    duplicates = detect_line_movement_duplicate_snapshots(snapshot_rows)
    missing_links = summarize_line_movement_missing_links(snapshot_rows)
    books_markets_sports = summarize_line_movement_books_markets_sports(snapshot_rows)

    # As‑of query preview (uses existing 10H22 engine)
    asof_snap: dict[str, Any] = {
        "ok": False,
        "total_snapshots": 0,
        "available_snapshots": 0,
        "future_snapshots": 0,
        "invalid_time_snapshots": 0,
        "snapshots": [],
        "warnings": [],
    }
    if hypothetical_bet_time is not None:
        from src.data.line_movement import (
            filter_line_movement_snapshots_as_of,
        )
        asof_snap = filter_line_movement_snapshots_as_of(
            snapshot_rows,
            event_id=event_id,
            hypothetical_bet_time=hypothetical_bet_time,
            bookmaker=bookmaker,
            market_family=market_family,
            market=market,
            selection=selection,
        )

    readiness = build_line_movement_quality_readiness(
        coverage, duplicates, missing_links, asof_summary=asof_snap
    )

    # Collect warnings
    warnings.extend(coverage.get("warnings", []))
    warnings.extend(duplicates.get("warnings", []))
    warnings.extend(missing_links.get("warnings", []))
    warnings.extend(books_markets_sports.get("warnings", []))
    warnings.extend(asof_snap.get("warnings", []))
    warnings.extend(readiness.get("warnings", []))

    return {
        "ok": True,
        "version": version,
        "coverage": coverage,
        "duplicates": duplicates,
        "missing_links": missing_links,
        "books_markets_sports": books_markets_sports,
        "asof_query": asof_snap,
        "readiness": readiness,
        "messages": messages,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# SQLite wrapper
# ---------------------------------------------------------------------------


def build_line_movement_data_quality_snapshot_from_sqlite(
    db_path: Any,
    hypothetical_bet_time: Any = None,
    event_id: str | None = None,
    bookmaker: str | None = None,
    market_family: str | None = None,
    market: str | None = None,
    selection: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Load snapshots from SQLite (read-only) and then build data quality snapshot.

    No SQL writes, no schema changes, no vendor connector.
    """
    from src.data.line_movement import (
        load_line_movement_snapshots_from_sqlite,
    )

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
    data_quality = build_line_movement_data_quality_snapshot(
        snapshot_rows=snapshots,
        hypothetical_bet_time=hypothetical_bet_time,
        event_id=event_id,
        bookmaker=bookmaker,
        market_family=market_family,
        market=market,
        selection=selection,
        limit=limit,
    )

    all_warnings: list[str] = []
    all_warnings.extend(load_result.get("warnings", []))
    all_warnings.extend(data_quality.get("warnings", []))

    return {
        "ok": load_result.get("ok", False) and data_quality.get("ok", False),
        "version": LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION,
        "load": load_result,
        "data_quality": data_quality,
        "messages": describe_line_movement_data_quality_dashboard(),
        "warnings": all_warnings,
    }


# ---------------------------------------------------------------------------
# Operator messages
# ---------------------------------------------------------------------------


def describe_line_movement_data_quality_dashboard() -> list[str]:
    """Return operator-friendly messages about this checkpoint dashboard."""
    return [
        "Line Movement Data Quality Dashboard shows coverage, missing links, "
        "duplicate snapshots, sports, markets, books, and readiness before "
        "any real connector is added.",
        "This checkpoint does not connect to vendors, import paid data, or scrape.",
        "Missing event_id links must be resolved before line movement features "
        "are trusted.",
        "As-of checks must filter snapshot_time <= hypothetical_bet_time to "
        "prevent look-ahead bias.",
        "After this checkpoint is reviewed, Phase 10H24 may begin the first "
        "real data connector spike.",
    ]
