"""Phase 10H23A – Synthetic Line Movement Sandbox.

Synthetic demo rows allow operators to preview the Phase 10H20‑10H23
line‑movement pipeline without any real vendor, API, scraper or paid‑data
connector, and without writing to production SQLite tables.

All rows are clearly marked as synthetic and must never be used as model
evidence.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Phase marker
# ---------------------------------------------------------------------------

SYNTHETIC_LINE_MOVEMENT_SANDBOX_VERSION: str = "10H23A"

# ---------------------------------------------------------------------------
# Supported demo sports
# ---------------------------------------------------------------------------

_SUPPORTED_SPORTS: list[str] = ["mlb", "nba", "nfl", "nhl", "soccer"]


def get_supported_synthetic_sports() -> list[str]:
    """Return stable sorted list of supported demo sports."""
    return sorted(_SUPPORTED_SPORTS)


# ---------------------------------------------------------------------------
# Synthetic row marker constants
# ---------------------------------------------------------------------------

_SYNTHETIC_SOURCE_KEY = "synthetic_demo"
_SYNTHETIC_SOURCE_NAME = "Synthetic Demo"
_SYNTHETIC_SOURCE_FILE = "synthetic_demo_in_memory"
_SYNTHETIC_IS_SYNTHETIC = "Yes"

# ---------------------------------------------------------------------------
# Value normalizer
# ---------------------------------------------------------------------------


def normalize_synthetic_line_movement_value(value: Any) -> str:
    """Convert *value* to a stable JSON-safe string, never raising."""
    try:
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
    except Exception:
        return str(value)


# ---------------------------------------------------------------------------
# Synthetic event rows
# ---------------------------------------------------------------------------


def build_synthetic_event_rows(sport: str = "nba", event_count: int = 2) -> list[dict[str, Any]]:
    """Return deterministic fake canonical event rows for the given sport.

    *event_count* is capped between 1 and 10.  Invalid sport falls back to
    ``nba`` and emits a warning via the caller payload function.
    """
    sport_lower = sport.strip().lower() if isinstance(sport, str) else "nba"
    if sport_lower not in _SUPPORTED_SPORTS:
        # caller will detect and warn; fallback to nba
        sport_lower = "nba"

    count = max(1, min(10, int(event_count) if event_count else 2))

    # Map sport to league value
    league_map = {
        "nba": "NBA",
        "nfl": "NFL",
        "mlb": "MLB",
        "nhl": "NHL",
        "soccer": "EPL",
    }
    league = league_map.get(sport_lower, "Demo League")

    rows: list[dict[str, Any]] = []
    for i in range(1, count + 1):
        event_id = f"synthetic_event_{sport_lower}_{i}"
        source_event_id = f"synthetic_source_event_{sport_lower}_{i}"
        month = ((i - 1) // 28) + 1
        day = ((i - 1) % 28) + 1
        date_str = f"2024-{month:02d}-{day:02d}"  # deterministic dates
        home = f"Synthetic {sport_lower.title()} Home {i}"
        away = f"Synthetic {sport_lower.title()} Away {i}"
        rows.append(
            {
                "event_id": event_id,
                "source_key": _SYNTHETIC_SOURCE_KEY,
                "source_event_id": source_event_id,
                "sport": sport_lower,
                "league": league,
                "event_date": date_str,
                "home_team": home,
                "away_team": away,
                "is_synthetic_demo": _SYNTHETIC_IS_SYNTHETIC,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Synthetic line-movement snapshot rows
# ---------------------------------------------------------------------------

_BOOKMAKERS: list[str] = ["DemoBookA", "DemoBookB"]
_SPORTS_MARKET_MAP: dict[str, list[tuple[str, str, str]]] = {
    # (market, market_family, selection) ; use 2-Way/3-Way wording as appropriate
    "nba": [
        ("Game Total", "game_total", "Over"),
        ("Game Total", "game_total", "Under"),
        ("Spread", "spread_or_handicap", "Home"),
        ("Spread", "spread_or_handicap", "Away"),
        ("2-Way Moneyline", "two_way_moneyline", "Home"),
        ("2-Way Moneyline", "two_way_moneyline", "Away"),
    ],
    "nfl": [
        ("Game Total", "game_total", "Over"),
        ("Game Total", "game_total", "Under"),
        ("Spread", "spread_or_handicap", "Home"),
        ("Spread", "spread_or_handicap", "Away"),
        ("2-Way Moneyline", "two_way_moneyline", "Home"),
        ("2-Way Moneyline", "two_way_moneyline", "Away"),
    ],
    "nhl": [
        ("Game Total", "game_total", "Over"),
        ("Game Total", "game_total", "Under"),
        ("Puck Line", "spread_or_handicap", "Home"),
        ("Puck Line", "spread_or_handicap", "Away"),
        ("2-Way Moneyline", "two_way_moneyline", "Home"),
        ("2-Way Moneyline", "two_way_moneyline", "Away"),
    ],
    "mlb": [
        ("Game Total", "game_total", "Over"),
        ("Game Total", "game_total", "Under"),
        ("Run Line", "spread_or_handicap", "Home"),
        ("Run Line", "spread_or_handicap", "Away"),
        ("2-Way Moneyline", "two_way_moneyline", "Home"),
        ("2-Way Moneyline", "two_way_moneyline", "Away"),
    ],
    "soccer": [
        ("3-Way Moneyline", "three_way_moneyline", "Home"),
        ("3-Way Moneyline", "three_way_moneyline", "Draw"),
        ("3-Way Moneyline", "three_way_moneyline", "Away"),
        ("Game Total", "game_total", "Over"),
        ("Game Total", "game_total", "Under"),
        ("Spread", "spread_or_handicap", "Home"),
        ("Spread", "spread_or_handicap", "Away"),
    ],
}

_SNAPSHOT_LABELS: list[str] = ["opening", "decision", "closing"]


def build_synthetic_line_movement_rows(
    sport: str = "nba",
    event_count: int = 2,
    snapshots_per_event: int = 3,
    include_missing_link: bool = False,
    include_duplicate: bool = False,
    include_future_snapshot: bool = False,
) -> list[dict[str, Any]]:
    """Return deterministic synthetic line‑movement snapshot rows.

    All caps enforced.  No randomness.
    """
    sport_lower = sport.strip().lower() if isinstance(sport, str) else "nba"
    if sport_lower not in _SUPPORTED_SPORTS:
        sport_lower = "nba"

    count = max(1, min(10, int(event_count) if event_count else 2))
    snaps = max(1, min(10, int(snapshots_per_event) if snapshots_per_event else 3))

    markets = _SPORTS_MARKET_MAP.get(sport_lower, _SPORTS_MARKET_MAP["nba"])
    bookmakers = _BOOKMAKERS

    league_map = {
        "nba": "NBA",
        "nfl": "NFL",
        "mlb": "MLB",
        "nhl": "NHL",
        "soccer": "EPL",
    }
    league = league_map.get(sport_lower, "Demo League")

    base_time = "2024-01-01T12:00:00Z"
    snapshot_delta_hours = 1

    rows: list[dict[str, Any]] = []

    # Keep track of whether we've injected missing link / duplicate / future
    inserted_missing = False
    inserted_duplicate = False
    inserted_future = False

    future_time = "2024-06-15T10:00:00Z"  # well after hypothetical_bet_time

    for ev_idx in range(1, count + 1):
        event_id = f"synthetic_event_{sport_lower}_{ev_idx}"
        source_event_id = f"synthetic_source_event_{sport_lower}_{ev_idx}"
        home = f"Synthetic {sport_lower.title()} Home {ev_idx}"
        away = f"Synthetic {sport_lower.title()} Away {ev_idx}"
        event_month = ((ev_idx - 1) // 28) + 1
        event_day = ((ev_idx - 1) % 28) + 1
        date_str = f"2024-{event_month:02d}-{event_day:02d}"

        for mkt_idx, (market, market_family, selection) in enumerate(markets):
            for snap_idx in range(snaps):
                label = _SNAPSHOT_LABELS[snap_idx % len(_SNAPSHOT_LABELS)]
                # deterministic time
                hours = snap_idx * snapshot_delta_hours
                if hours == 0:
                    snap_time = base_time
                elif hours == 1:
                    snap_time = "2024-01-01T13:00:00Z"
                else:
                    snap_time = "2024-01-01T14:00:00Z"

                # line / odds values deterministic
                line_base = 200 - (ev_idx * 10 + mkt_idx * 5 + snap_idx * 2)
                odds_base = -110 - (ev_idx * 5 + mkt_idx * 2 + snap_idx * 1)
                implied_prob = round(0.5 + (ev_idx * 0.01 + mkt_idx * 0.005 + snap_idx * 0.002), 4)

                snapshot_id = (
                    f"synthetic_snapshot_{sport_lower}_{ev_idx}_{mkt_idx}_{snap_idx}"
                )

                row: dict[str, Any] = {
                    "source_name": _SYNTHETIC_SOURCE_NAME,
                    "source_key": _SYNTHETIC_SOURCE_KEY,
                    "source_file": _SYNTHETIC_SOURCE_FILE,
                    "source_event_id": source_event_id,
                    "source_snapshot_id": snapshot_id,
                    "snapshot_id": snapshot_id,
                    "event_id": event_id,
                    "sport": sport_lower,
                    "league": league,
                    "event_date": date_str,
                    "home_team": home,
                    "away_team": away,
                    "bookmaker": bookmakers[(ev_idx + mkt_idx + snap_idx) % len(bookmakers)],
                    "market": market,
                    "market_family": market_family,
                    "selection": selection,
                    "line_value": line_base,
                    "odds_value": odds_base,
                    "implied_probability": implied_prob,
                    "snapshot_label": label,
                    "snapshot_time": snap_time,
                    "raw_market_name": market,
                    "raw_selection_name": selection,
                    "is_synthetic_demo": _SYNTHETIC_IS_SYNTHETIC,
                }

                # missing link injection
                if include_missing_link and not inserted_missing and ev_idx == 1 and mkt_idx == 0 and snap_idx == 0:
                    row["event_id"] = ""
                    inserted_missing = True

                # duplicate injection
                if include_duplicate and not inserted_duplicate and ev_idx == 1 and mkt_idx == 0 and snap_idx == snaps - 1:
                    # duplicate the previous snapshot (snap_idx == 0)
                    dup_row = dict(row)
                    dup_row["snapshot_id"] = f"synthetic_snapshot_{sport_lower}_{ev_idx}_{mkt_idx}_{0}"
                    dup_row["source_snapshot_id"] = dup_row["snapshot_id"]
                    # keep other fields same, creating duplicate key
                    rows.append(dup_row)
                    inserted_duplicate = True

                # future injection (make snapshot_time later)
                if include_future_snapshot and not inserted_future and ev_idx == 1 and mkt_idx == 0 and snap_idx == 0:
                    row["snapshot_time"] = future_time
                    inserted_future = True

                rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Demo payload builder
# ---------------------------------------------------------------------------


def build_synthetic_line_movement_demo_payload(
    sport: str = "nba",
    event_count: int = 2,
    snapshots_per_event: int = 3,
    include_missing_link: bool = False,
    include_duplicate: bool = False,
    include_future_snapshot: bool = False,
) -> dict[str, Any]:
    """Return a stable payload with synthetic event rows and snapshot rows.

    No SQL writes.  Invalid sport falls back to nba and emits warning.
    """
    warnings: list[str] = []
    sport_lower = sport.strip().lower() if isinstance(sport, str) else "nba"
    if sport_lower not in _SUPPORTED_SPORTS:
        warnings.append(f"unsupported_sport:{sport}. Falling back to nba.")
        sport_lower = "nba"

    event_rows = build_synthetic_event_rows(sport=sport_lower, event_count=event_count)
    snapshot_rows = build_synthetic_line_movement_rows(
        sport=sport_lower,
        event_count=event_count,
        snapshots_per_event=snapshots_per_event,
        include_missing_link=include_missing_link,
        include_duplicate=include_duplicate,
        include_future_snapshot=include_future_snapshot,
    )

    return {
        "ok": True,
        "version": SYNTHETIC_LINE_MOVEMENT_SANDBOX_VERSION,
        "sport": sport_lower,
        "event_rows": event_rows,
        "snapshot_rows": snapshot_rows,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Main sandbox runner
# ---------------------------------------------------------------------------



def _add_synthetic_asof_count_aliases(asof_query: dict) -> dict:
    """Add dashboard/test-friendly aliases without changing the as-of backend."""
    if not isinstance(asof_query, dict):
        return asof_query

    query = asof_query.get("query")
    if not isinstance(query, dict):
        return asof_query

    excluded = query.get("excluded_counts") or {}
    if not isinstance(excluded, dict):
        excluded = {}

    query.setdefault("future_snapshots", int(excluded.get("future_filtered") or 0))
    query.setdefault("invalid_time_snapshots", int(excluded.get("invalid_time_filtered") or 0))
    query.setdefault("unmatched_snapshots", int(excluded.get("unmatched_filtered") or 0))
    return asof_query


def run_synthetic_line_movement_sandbox(
    sport: str = "nba",
    event_count: int = 2,
    snapshots_per_event: int = 3,
    hypothetical_bet_time: str = "2024-01-01T13:00:00Z",
    include_missing_link: bool = False,
    include_duplicate: bool = False,
    include_future_snapshot: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    """Build synthetic rows and run them through the 10H20‑10H23 pipeline.

    All outputs are in‑memory.  No SQLite writes, no vendor connector,
    no paid data, no APIs.
    """
    warnings: list[str] = []

    try:
        from src.data.line_movement import (
            build_line_movement_import_preview,
        )
        from src.data.source_event_links import (
            resolve_source_event_links,
        )
        from src.data.line_movement import (
            build_asof_line_movement_query_snapshot,
        )
        from src.data.line_movement import (
            build_line_movement_data_quality_snapshot,
        )
    except ImportError as exc:
        return {
            "ok": False,
            "version": SYNTHETIC_LINE_MOVEMENT_SANDBOX_VERSION,
            "sport": sport,
            "synthetic_notice": "",
            "event_rows": [],
            "snapshot_rows": [],
            "import_preview": {},
            "event_link_resolution": {},
            "asof_query": {},
            "data_quality": {},
            "warnings": [f"sandbox_import_error:{exc}"],
            "messages": [],
        }

    # Build payload
    payload = build_synthetic_line_movement_demo_payload(
        sport=sport,
        event_count=event_count,
        snapshots_per_event=snapshots_per_event,
        include_missing_link=include_missing_link,
        include_duplicate=include_duplicate,
        include_future_snapshot=include_future_snapshot,
    )

    event_rows = payload.get("event_rows", [])
    snapshot_rows = payload.get("snapshot_rows", [])
    sport_used = payload.get("sport", "nba")
    for w in payload.get("warnings", []):
        warnings.append(w)

    # 1. Import preview (Phase 10H20)
    import_preview = build_line_movement_import_preview(snapshot_rows, limit=limit)

    # 2. Event link resolution (Phase 10H21)
    event_link_resolution = resolve_source_event_links(
        snapshot_rows,
        canonical_event_rows=event_rows,
        limit=limit,
    )

    # 3. As‑Of query (Phase 10H22)
    asof_query = build_asof_line_movement_query_snapshot(
        snapshots=snapshot_rows,
        hypothetical_bet_time=hypothetical_bet_time,
        limit=limit,
    )

    # 4. Data quality (Phase 10H23)
    asof_query = _add_synthetic_asof_count_aliases(asof_query)

    data_quality = build_line_movement_data_quality_snapshot(
        snapshot_rows=snapshot_rows,
        hypothetical_bet_time=hypothetical_bet_time,
        limit=limit,
    )

    synthetic_notice = (
        "Synthetic sandbox rows are fake demo data and must not be used "
        "as model evidence."
    )

    messages = describe_synthetic_line_movement_sandbox()

    return {
        "ok": True,
        "version": SYNTHETIC_LINE_MOVEMENT_SANDBOX_VERSION,
        "sport": sport_used,
        "synthetic_notice": synthetic_notice,
        "event_rows": event_rows,
        "snapshot_rows": snapshot_rows,
        "import_preview": import_preview,
        "event_link_resolution": event_link_resolution,
        "asof_query": asof_query,
        "data_quality": data_quality,
        "warnings": warnings,
        "messages": messages,
    }


# ---------------------------------------------------------------------------
# Clear function
# ---------------------------------------------------------------------------


def clear_synthetic_line_movement_sandbox() -> dict[str, Any]:
    """Since synthetic rows are in‑memory only, return a confirmation."""
    return {
        "ok": True,
        "version": SYNTHETIC_LINE_MOVEMENT_SANDBOX_VERSION,
        "cleared": True,
        "message": (
            "Synthetic rows are in‑memory only. No production data was written. "
            "No vendor connector, paid data, or scraper was used."
        ),
    }


# ---------------------------------------------------------------------------
# Description
# ---------------------------------------------------------------------------


def describe_synthetic_line_movement_sandbox() -> list[str]:
    """Return operator messages about this sandbox."""
    return [
        "Synthetic Line Movement Sandbox uses fake demo rows to preview the "
        "line movement pipeline.",
        "Synthetic rows are not real historical data and must not be used as "
        "model evidence.",
        "No vendor, API, scraper, paid data, or SQLite write is used.",
        "After review, synthetic rows should be cleared before Phase 10H24 "
        "real connector work.",
        "Phase 10H24 remains the first real data connector spike only after "
        "checkpoint review.",
    ]
