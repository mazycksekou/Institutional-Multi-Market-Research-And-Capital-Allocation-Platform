"""
Phase 10H20 – Vendor‑Neutral Line Movement Import Contract.

Defines the standard shape future line‑movement sources must provide.
No vendor connectors, no paid data, no scraping, no external API calls.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Phase marker
# ---------------------------------------------------------------------------

LINE_MOVEMENT_IMPORT_CONTRACT_VERSION: str = "10H20"

# ---------------------------------------------------------------------------
# Canonical input fields (vendor‑neutral)
# ---------------------------------------------------------------------------

VENDOR_NEUTRAL_INPUT_FIELDS: list[str] = [
    "source_name",
    "source_key",
    "source_file",
    "source_event_id",
    "source_snapshot_id",
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
    "raw_payload",
]

# ---------------------------------------------------------------------------
# Required input fields (must not be blank)
# ---------------------------------------------------------------------------

REQUIRED_VENDOR_INPUT_FIELDS: list[str] = [
    "source_name",
    "source_key",
    "sport",
    "event_date",
    "home_team",
    "away_team",
    "bookmaker",
    "market",
    "selection",
    "snapshot_time",
]

# ---------------------------------------------------------------------------
# Target schema fields (historical_line_snapshots)
# ---------------------------------------------------------------------------

HISTORICAL_LINE_SNAPSHOT_TARGET_FIELDS: list[str] = [
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
# Helper: safe JSON string
# ---------------------------------------------------------------------------


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
            return json.dumps(value, sort_keys=True, default=str)
        return str(value)
    except Exception:
        return str(value)


normalize_line_movement_import_value = _safe_str

# ---------------------------------------------------------------------------
# Market family normalizer
# ---------------------------------------------------------------------------


def normalize_line_movement_market_family(value: Any) -> str:
    """Normalise the market family without vendor‑specific logic.

    Returns two_way_moneyline, three_way_moneyline,
    spread_or_handicap, game_total, team_total, player_prop,
    or a lowercase snake_case fallback.
    Never returns moneyline_or_1x2 as preferred output.
    """
    if not value:
        return "general_market"

    v = (
        str(value)
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )

    if v in ("moneyline", "ml", "2-way", "2way", "two-way", "two_way"):
        return "two_way_moneyline"
    if v in ("1x2", "threeway", "three-way", "three_way", "3-way"):
        return "three_way_moneyline"
    if v in ("spread", "handicap", "pointspread", "runline"):
        return "spread_or_handicap"
    if v in ("total", "overunder", "o/u", "ou", "game_total", "gametotal", "totalpoints"):
        return "game_total"
    if v in ("team_total", "teamtotal"):
        return "team_total"
    if v in ("player_prop", "playerprop", "player props", "playerpoints"):
        return "player_prop"

    # fallback: lowercase snake_case
    return v


# ---------------------------------------------------------------------------
# Snapshot label normalizer
# ---------------------------------------------------------------------------


def normalize_line_movement_snapshot_label(value: Any) -> str:
    """Normalise a snapshot label to one of the allowed canonical values."""
    if value is None:
        return "unknown"
    v = str(value).strip().lower()
    allowed = {"opening", "current", "decision", "closing", "unknown"}
    if v in allowed:
        return v
    if v in ("open", "start"):
        return "opening"
    if v in ("live", "now"):
        return "current"
    if v in ("bet", "bet_time", "dec"):
        return "decision"
    if v in ("close", "end", "final"):
        return "closing"
    return v


# ---------------------------------------------------------------------------
# Contract description
# ---------------------------------------------------------------------------


def build_vendor_neutral_line_movement_contract() -> dict[str, Any]:
    """Return the contract shape as a stable dict.

    Required input fields, optional input fields, target fields, and a warning.
    """
    optional_input_fields = sorted(
        set(VENDOR_NEUTRAL_INPUT_FIELDS) - set(REQUIRED_VENDOR_INPUT_FIELDS)
    )
    return {
        "ok": True,
        "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
        "input_fields": list(VENDOR_NEUTRAL_INPUT_FIELDS),
        "target_fields": list(HISTORICAL_LINE_SNAPSHOT_TARGET_FIELDS),
        "required_input_fields": list(REQUIRED_VENDOR_INPUT_FIELDS),
        "optional_input_fields": optional_input_fields,
        "warnings": [
            "This contract does not connect to vendors, import paid data, or scrape.",
        ],
    }


# ---------------------------------------------------------------------------
# Validate a single row
# ---------------------------------------------------------------------------


def validate_line_movement_import_row(row: Any) -> dict[str, Any]:
    """Validate a vendor‑neutral input row.

    Returns ``ok``, ``version``, ``normalized_row``,
    ``missing_required_fields``, ``warnings``.
    """
    if not isinstance(row, dict):
        return {
            "ok": False,
            "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
            "normalized_row": {},
            "missing_required_fields": list(REQUIRED_VENDOR_INPUT_FIELDS),
            "warnings": ["invalid_row_type"],
        }

    normalized: dict[str, Any] = {}
    missing: list[str] = []
    warnings: list[str] = []

    for field in VENDOR_NEUTRAL_INPUT_FIELDS:
        val = row.get(field)
        normalized[field] = _safe_str(val)

    for field in REQUIRED_VENDOR_INPUT_FIELDS:
        raw = row.get(field)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            missing.append(field)

    # Apply normalisers
    if "market_family" in row:
        normalized["market_family"] = normalize_line_movement_market_family(
            row["market_family"]
        )
    if "snapshot_label" in row:
        normalized["snapshot_label"] = normalize_line_movement_snapshot_label(
            row["snapshot_label"]
        )
    else:
        normalized["snapshot_label"] = "unknown"

    return {
        "ok": len(missing) == 0,
        "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
        "normalized_row": normalized,
        "missing_required_fields": missing,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Deterministic snapshot‑ID maker
# ---------------------------------------------------------------------------


def make_line_movement_snapshot_id(row: dict[str, Any]) -> str:
    """Return a deterministic snapshot ID.

    If ``source_snapshot_id`` is present, prefix it with ``lms_<source_name>_``.
    Otherwise build a SHA‑256 hash of the core identifying fields.
    """
    source_name = _safe_str(row.get("source_name", "")).lower().replace(" ", "_")
    source_snapshot_id = row.get("source_snapshot_id")
    if source_snapshot_id:
        raw = f"lms_{source_name}_{_safe_str(source_snapshot_id)}"
        # keep only safe chars
        safe = "".join(c for c in raw if c.isalnum() or c in ("_", "-"))
        return safe

    parts: list[str] = [
        _safe_str(row.get("source_name", "")),
        _safe_str(row.get("source_key", "")),
        _safe_str(row.get("source_event_id", "")),
        _safe_str(row.get("sport", "")),
        _safe_str(row.get("event_date", "")),
        _safe_str(row.get("home_team", "")),
        _safe_str(row.get("away_team", "")),
        _safe_str(row.get("bookmaker", "")),
        _safe_str(row.get("market", "")),
        _safe_str(row.get("selection", "")),
        _safe_str(row.get("snapshot_time", "")),
    ]
    raw = "lms_" + hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]
    # keep only safe chars
    return "".join(c for c in raw if c.isalnum() or c in ("_", "-"))


# ---------------------------------------------------------------------------
# Build canonical snapshot row
# ---------------------------------------------------------------------------


def build_canonical_line_movement_snapshot_row(row: dict[str, Any]) -> dict[str, Any]:
    """Accept one vendor‑neutral row and return a validated canonical snapshot.

    Does **not** insert into SQLite.

    Returns keys: ok, version, snapshot_row, missing_required_fields, warnings.
    """
    validation = validate_line_movement_import_row(row)
    if not validation["ok"]:
        return {
            "ok": False,
            "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
            "snapshot_row": {},
            "missing_required_fields": validation["missing_required_fields"],
            "warnings": validation["warnings"],
        }

    normalized = validation["normalized_row"]
    now_iso = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    snapshot_row: dict[str, Any] = {
        "snapshot_id": make_line_movement_snapshot_id(row),
        "event_id": row.get("event_id", ""),          # Phase 10H21 will resolve
        "odds_id": row.get("odds_id", ""),            # Phase 10H21 may fill
        "source_key": normalized.get("source_key", ""),
        "source_file": normalized.get("source_file", ""),
        "sport": normalized.get("sport", ""),
        "league": normalized.get("league", ""),
        "event_date": normalized.get("event_date", ""),
        "home_team": normalized.get("home_team", ""),
        "away_team": normalized.get("away_team", ""),
        "bookmaker": normalized.get("bookmaker", ""),
        "market": normalized.get("market", ""),
        "market_family": normalized.get("market_family", ""),
        "selection": normalized.get("selection", ""),
        "player_name": normalized.get("player_name", ""),
        "team_name": normalized.get("team_name", ""),
        "line_value": normalized.get("line_value", ""),
        "odds_value": normalized.get("odds_value", ""),
        "implied_probability": normalized.get("implied_probability", ""),
        "snapshot_label": normalized.get("snapshot_label", "unknown"),
        "snapshot_time": normalized.get("snapshot_time", ""),
        "raw_market_name": normalized.get("raw_market_name", ""),
        "raw_selection_name": normalized.get("raw_selection_name", ""),
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    return {
        "ok": True,
        "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
        "snapshot_row": snapshot_row,
        "missing_required_fields": [],
        "warnings": validation["warnings"],
    }


# ---------------------------------------------------------------------------
# Preview a batch of rows
# ---------------------------------------------------------------------------


def build_line_movement_import_preview(
    rows: list[dict[str, Any]], limit: int = 100
) -> dict[str, Any]:
    """Accept an iterable of vendor‑neutral rows and return a validation preview.

    Does **not** insert into SQLite.
    """
    if not isinstance(rows, list):
        return {
            "ok": False,
            "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": [],
            "preview_rows": [],
            "missing_required_field_counts": {},
            "warnings": ["non_list_input"],
        }

    if not rows:
        return {
            "ok": True,
            "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": [],
            "preview_rows": [],
            "missing_required_field_counts": {},
            "warnings": ["no_rows"],
        }

    valid_list: list[dict[str, Any]] = []
    invalid_list: list[dict[str, Any]] = []
    missing_counts: dict[str, int] = {}

    for idx, r in enumerate(rows):
        if not isinstance(r, dict):
            invalid_list.append(
                {
                    "row_index": idx,
                    "missing_required_fields": list(REQUIRED_VENDOR_INPUT_FIELDS),
                    "warnings": ["invalid_row_type"],
                }
            )
            continue

        result = build_canonical_line_movement_snapshot_row(r)
        if result["ok"]:
            valid_list.append(result["snapshot_row"])
        else:
            invalid_info = {
                "row_index": idx,
                "missing_required_fields": result["missing_required_fields"],
                "warnings": result["warnings"],
            }
            invalid_list.append(invalid_info)
            for field in result["missing_required_fields"]:
                missing_counts[field] = missing_counts.get(field, 0) + 1

    preview_rows = valid_list[: min(limit, len(valid_list))]

    return {
        "ok": True,
        "version": LINE_MOVEMENT_IMPORT_CONTRACT_VERSION,
        "total_rows": len(rows),
        "valid_rows": len(valid_list),
        "invalid_rows": invalid_list,
        "preview_rows": preview_rows,
        "missing_required_field_counts": missing_counts,
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Human‑readable contract description
# ---------------------------------------------------------------------------


def describe_line_movement_import_contract() -> list[str]:
    """Return operator‑friendly messages about the contract."""
    return [
        "Vendor‑Neutral Line Movement Import Contract defines the shape future "
        "data must match.",
        "This phase does not connect to vendors, import paid data, or scrape.",
        "Phase 10H21 will resolve source_event_id to canonical event_id.",
        "Future as‑of queries must filter snapshot_time <= hypothetical_bet_time "
        "to prevent look‑ahead bias.",
    ]
