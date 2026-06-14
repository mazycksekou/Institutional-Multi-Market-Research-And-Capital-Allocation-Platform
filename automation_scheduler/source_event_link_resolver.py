
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

SOURCE_EVENT_LINK_RESOLVER_VERSION = "10H21"

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def normalize_event_link_value(value: Any) -> str:
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


def normalize_event_link_token(value: Any) -> str:
    """Lowercase, trim, replace punctuation with single spaces, collapse."""
    s = normalize_event_link_value(value)
    if not s:
        return ""
    s = s.lower().strip()
    # replace punctuation/separators with space
    s = re.sub(r"[\W_]+", " ", s)
    # collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_event_link_date(value: Any) -> str:
    """Return YYYY-MM-DD when parseable, else normalized string."""
    s = normalize_event_link_value(value)
    if not s:
        return ""
    # try ISO date (10 characters YYYY-MM-DD)
    if len(s) >= 10 and s[4] == '-' and s[7] == '-':
        candidate = s[:10]
        try:
            datetime.strptime(candidate, "%Y-%m-%d")
            return candidate
        except ValueError:
            pass
    # try full ISO datetime
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    # fallback: return normalized token
    return normalize_event_link_token(s)


# ---------------------------------------------------------------------------
# Link key builders
# ---------------------------------------------------------------------------

def build_event_link_key(row: Mapping[str, Any]) -> str:
    """Deterministic key from sport, league, event_date, home_team, away_team."""
    sport = normalize_event_link_token(row.get("sport"))
    league = normalize_event_link_token(row.get("league"))
    date = normalize_event_link_date(row.get("event_date"))
    home = normalize_event_link_token(row.get("home_team"))
    away = normalize_event_link_token(row.get("away_team"))
    key = f"{sport}|{league}|{date}|{home}|{away}"
    return key


def build_reversed_event_link_key(row: Mapping[str, Any]) -> str:
    """Same as build_event_link_key but home/away swapped."""
    sport = normalize_event_link_token(row.get("sport"))
    league = normalize_event_link_token(row.get("league"))
    date = normalize_event_link_date(row.get("event_date"))
    home = normalize_event_link_token(row.get("away_team"))
    away = normalize_event_link_token(row.get("home_team"))
    key = f"{sport}|{league}|{date}|{home}|{away}"
    return key


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_event_link_candidate(
    source_row: Mapping[str, Any],
    candidate_row: Mapping[str, Any],
) -> dict[str, Any]:
    """Return score and reasons for a candidate match."""
    score = 0
    reasons: list[str] = []
    source_key = build_event_link_key(source_row)
    candidate_key = build_event_link_key(candidate_row)
    reversed_key = build_reversed_event_link_key(source_row)
    reversed_home_away = False

    # exact sport compare
    source_sport = normalize_event_link_token(source_row.get("sport"))
    candidate_sport = normalize_event_link_token(candidate_row.get("sport"))
    if source_sport and candidate_sport and source_sport == candidate_sport:
        score += 25
    else:
        if source_sport and candidate_sport:
            reasons.append("sport mismatch")
        else:
            reasons.append("missing sport")

    # league compare (optional, less weight)
    source_league = normalize_event_link_token(source_row.get("league"))
    candidate_league = normalize_event_link_token(candidate_row.get("league"))
    if source_league and candidate_league and source_league == candidate_league:
        score += 5
    elif source_league and candidate_league:
        reasons.append("league mismatch")
    # else neutral

    # date compare
    source_date = normalize_event_link_date(source_row.get("event_date"))
    candidate_date = normalize_event_link_date(candidate_row.get("event_date"))
    if source_date and candidate_date and source_date == candidate_date:
        score += 30
    else:
        if source_date and candidate_date:
            reasons.append("date mismatch")
        elif not source_date:
            reasons.append("missing source event_date")
        elif not candidate_date:
            reasons.append("missing candidate event_date")

    # team matching
    source_home = normalize_event_link_token(source_row.get("home_team"))
    source_away = normalize_event_link_token(source_row.get("away_team"))
    cand_home = normalize_event_link_token(candidate_row.get("home_team"))
    cand_away = normalize_event_link_token(candidate_row.get("away_team"))

    home_match = source_home and cand_home and source_home == cand_home
    away_match = source_away and cand_away and source_away == cand_away

    if home_match and away_match:
        score += 40
    elif (source_home and cand_away and source_home == cand_away and
          source_away and cand_home and source_away == cand_home):
        # reversed home/away
        score += 30
        reversed_home_away = True
        reasons.append("reversed_home_away")
    else:
        # partial matches
        if home_match:
            score += 15
            reasons.append("home_team_match_only")
        elif away_match:
            score += 15
            reasons.append("away_team_match_only")
        else:
            # try one team matching the other row's same side
            if source_home and cand_home and source_home == cand_home:
                score += 15
            else:
                reasons.append("no team match")
            if source_away and cand_away and source_away == cand_away:
                score += 15
            else:
                reasons.append("no team match")

    # ensure score between 0 and 100
    score = max(0, min(100, score))

    return {
        "score": score,
        "reasons": reasons,
        "source_key": source_key,
        "candidate_key": candidate_key,
        "reversed_home_away": reversed_home_away,
    }


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------

def build_event_link_index(
    canonical_event_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build an index from canonical event rows."""
    event_key_index: dict[str, list[str]] = {}
    source_event_id_index: dict[str, str] = {}
    total_events = 0
    warnings: list[str] = []

    for row in canonical_event_rows:
        if not isinstance(row, Mapping):
            continue
        event_id = row.get("event_id")
        if not event_id:
            warnings.append("missing_event_id")
            continue
        total_events += 1

        key = build_event_link_key(row)
        event_key_index.setdefault(key, []).append(str(event_id))

        # source_event_id index
        source_key = row.get("source_key")
        source_event_id = row.get("source_event_id")
        idx_key = f"{source_key}|{source_event_id}" if source_key and source_event_id else None
        if idx_key:
            source_event_id_index[idx_key] = str(event_id)

    return {
        "ok": True,
        "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
        "total_events": total_events,
        "event_key_index": event_key_index,
        "source_event_id_index": source_event_id_index,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Row‐level resolver
# ---------------------------------------------------------------------------

def resolve_source_event_link(
    source_row: Mapping[str, Any],
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: dict[str, Any] | None = None,
    min_score: int = 95,
) -> dict[str, Any]:
    """Resolve one source row against canonical events."""
    version = SOURCE_EVENT_LINK_RESOLVER_VERSION
    warnings: list[str] = []

    # Validate source row
    if not isinstance(source_row, Mapping):
        return {
            "ok": False,
            "version": version,
            "resolved": False,
            "event_id": None,
            "match_score": 0,
            "score": 0,
            "match_method": "",
            "reasons": ["invalid_source_row"],
            "warnings": [],
            "candidate_count": 0,
            "source_event_id": None,
            "source_key": None,
        }

    source_event_id = source_row.get("source_event_id")
    source_key = source_row.get("source_key")

    # Priority 1: existing nonblank event_id on source row
    existing_event_id = source_row.get("event_id")
    if existing_event_id and str(existing_event_id).strip():
        return {
            "ok": True,
            "version": version,
            "resolved": True,
            "event_id": str(existing_event_id),
            "match_score": 100,
            "score": 100,
            "match_method": "existing_event_id",
            "reasons": [],
            "warnings": [],
            "candidate_count": 1,
            "source_event_id": normalize_event_link_value(source_event_id),
            "source_key": normalize_event_link_value(source_key),
        }

    # Build index if not provided
    idx = event_index
    if idx is None and canonical_event_rows is not None:
        idx = build_event_link_index(canonical_event_rows)
    if idx is None:
        # No index available
        return {
            "ok": True,
            "version": version,
            "resolved": False,
            "event_id": None,
            "match_score": 0,
            "score": 0,
            "match_method": "",
            "reasons": ["no_canonical_events"],
            "warnings": [],
            "candidate_count": 0,
            "source_event_id": normalize_event_link_value(source_event_id),
            "source_key": normalize_event_link_value(source_key),
        }

    # Priority 2: source_key + source_event_id exact match
    src_idx_key = f"{source_key}|{source_event_id}" if source_key and source_event_id else ""
    if src_idx_key and src_idx_key in idx.get("source_event_id_index", {}):
        return {
            "ok": True,
            "version": version,
            "resolved": True,
            "event_id": idx["source_event_id_index"][src_idx_key],
            "match_score": 100,
            "score": 100,
            "match_method": "source_event_id",
            "reasons": [],
            "warnings": [],
            "candidate_count": 1,
            "source_event_id": normalize_event_link_value(source_event_id),
            "source_key": normalize_event_link_value(source_key),
        }

    # Build candidate list via event_key_index
    candidates: list[tuple[int, str, str, bool]] = []  # (score, event_id, method, reversed)
    key = build_event_link_key(source_row)
    reversed_key = build_reversed_event_link_key(source_row)

    if key in idx.get("event_key_index", {}):
        for eid in idx["event_key_index"][key]:
            candidates.append((100, eid, "exact_event_key", False))
        # If multiple exact, still same score => ambiguous unless only one
        if len(candidates) == 1:
            return {
                "ok": True,
                "version": version,
                "resolved": True,
                "event_id": candidates[0][1],
                "match_score": 100,
                "score": 100,
                "match_method": "exact_event_key",
                "reasons": [],
                "warnings": [],
                "candidate_count": 1,
                "source_event_id": normalize_event_link_value(source_event_id),
                "source_key": normalize_event_link_value(source_key),
            }

    # If multiple exact, ambiguous
    if len(candidates) > 1:
        # all have score 100
        warning_msg = (
            f"ambiguous: {len(candidates)} exact event_key matches "
            f"({[(c[1]) for c in candidates]})"
        )
        warnings.append(warning_msg)
        return {
            "ok": True,
            "version": version,
            "resolved": False,
            "event_id": None,
            "match_score": 100,
            "score": 100,
            "match_method": "ambiguous",
            "reasons": [warning_msg],
            "warnings": warnings,
            "candidate_count": len(candidates),
            "source_event_id": normalize_event_link_value(source_event_id),
            "source_key": normalize_event_link_value(source_key),
        }

    # Priority 4: reversed key match with score 90
    if reversed_key in idx.get("event_key_index", {}):
        rev_events = idx["event_key_index"][reversed_key]
        if len(rev_events) == 1:
            if min_score <= 90:
                return {
                    "ok": True,
                    "version": version,
                    "resolved": True,
                    "event_id": rev_events[0],
                    "match_score": 90,
                    "score": 90,
                    "match_method": "reversed_home_away",
                    "reasons": ["reversed_home_away"],
                    "warnings": [],
                    "candidate_count": 1,
                    "source_event_id": normalize_event_link_value(source_event_id),
                    "source_key": normalize_event_link_value(source_key),
                }
            else:
                warnings.append(
                    f"reversed match found but score 90 below min_score {min_score}"
                )

    # Priority 5: scored candidates over all events
    best_score = 0
    best_candidates: list[tuple[int, str, str, bool]] = []
    if canonical_event_rows is not None:
        for cand in canonical_event_rows:
            if not isinstance(cand, Mapping):
                continue
            cand_id = cand.get("event_id")
            if not cand_id:
                continue
            info = score_event_link_candidate(source_row, cand)
            s = info["score"]
            rev = info["reversed_home_away"]
            if s > best_score:
                best_score = s
                best_candidates = [(s, str(cand_id), "scored", rev)]
            elif s == best_score:
                best_candidates.append((s, str(cand_id), "scored", rev))

    if best_candidates and best_score >= min_score:
        # if only one unique candidate
        unique_ids = list({c[1] for c in best_candidates})
        if len(unique_ids) == 1:
            return {
                "ok": True,
                "version": version,
                "resolved": True,
                "event_id": unique_ids[0],
                "match_score": best_score,
                "score": best_score,
                "match_method": "scored",
                "reasons": [],
                "warnings": [],
                "candidate_count": len(best_candidates),
                "source_event_id": normalize_event_link_value(source_event_id),
                "source_key": normalize_event_link_value(source_key),
            }
        else:
            warnings.append(
                f"ambiguous: {len(unique_ids)} scored candidates at score {best_score}: "
                f"{unique_ids}"
            )
            return {
                "ok": True,
                "version": version,
                "resolved": False,
                "event_id": None,
                "match_score": best_score,
                "score": best_score,
                "match_method": "ambiguous",
                "reasons": warnings,
                "warnings": warnings,
                "candidate_count": len(best_candidates),
                "source_event_id": normalize_event_link_value(source_event_id),
                "source_key": normalize_event_link_value(source_key),
            }

    # No match
    return {
        "ok": True,
        "version": version,
        "resolved": False,
        "event_id": None,
        "match_score": 0,
        "score": 0,
        "match_method": "",
        "reasons": ["no_match"],
        "warnings": warnings,
        "candidate_count": 0,
        "source_event_id": normalize_event_link_value(source_event_id),
        "source_key": normalize_event_link_value(source_key),
    }


# ---------------------------------------------------------------------------
# Multi‐row resolver
# ---------------------------------------------------------------------------

def resolve_source_event_links(
    source_rows: Sequence[Mapping[str, Any]],
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: dict[str, Any] | None = None,
    min_score: int = 95,
    limit: int = 100,
) -> dict[str, Any]:
    """Resolve many source rows."""
    if not isinstance(source_rows, list):
        source_rows = list(source_rows) if isinstance(source_rows, Sequence) else []

    if not source_rows:
        return {
            "ok": True,
            "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
            "total_rows": 0,
            "resolved_rows": 0,
            "unresolved_rows": 0,
            "ambiguous_rows": 0,
            "preview_rows": [],
            "warnings": ["no_rows"],
            "unresolved_reasons": [],
        }

    # Compute index if needed
    idx = event_index
    if idx is None and canonical_event_rows is not None:
        idx = build_event_link_index(canonical_event_rows)

    resolved_rows = 0
    unresolved_rows = 0
    ambiguous_rows = 0
    unresolved_reasons: list[str] = []
    preview_rows: list[dict[str, Any]] = []

    for i, row in enumerate(source_rows[:limit]):
        resolution = resolve_source_event_link(
            row,
            canonical_event_rows=canonical_event_rows,
            event_index=idx,
            min_score=min_score,
        )
        res = resolution.get("resolved", False)
        method = resolution.get("match_method", "")
        if res:
            resolved_rows += 1
        elif method == "ambiguous":
            ambiguous_rows += 1
        else:
            unresolved_rows += 1

        preview = {
            "row_index": i,
            "resolved": res,
            "event_id": resolution.get("event_id"),
            "match_score": resolution.get("match_score", 0),
            "match_method": method,
            "source_event_id": resolution.get("source_event_id"),
            "source_key": resolution.get("source_key"),
            "sport": normalize_event_link_token(row.get("sport")),
            "league": normalize_event_link_token(row.get("league")),
            "event_date": normalize_event_link_date(row.get("event_date")),
            "home_team": normalize_event_link_token(row.get("home_team")),
            "away_team": normalize_event_link_token(row.get("away_team")),
            "reasons": resolution.get("reasons", []),
            "warnings": resolution.get("warnings", []),
        }
        preview_rows.append(preview)
        if not res and resolution.get("reasons"):
            for r in resolution["reasons"]:
                if r not in unresolved_reasons:
                    unresolved_reasons.append(r)

    return {
        "ok": True,
        "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
        "total_rows": len(source_rows),
        "resolved_rows": resolved_rows,
        "unresolved_rows": unresolved_rows,
        "ambiguous_rows": ambiguous_rows,
        "preview_rows": preview_rows,
        "warnings": [],
        "unresolved_reasons": unresolved_reasons,
    }


# ---------------------------------------------------------------------------
# Apply resolution to snapshot row
# ---------------------------------------------------------------------------

def apply_resolved_event_id_to_snapshot_row(
    snapshot_row: Mapping[str, Any],
    resolution: dict[str, Any],
) -> dict[str, Any]:
    """Return copy of snapshot_row with event_id updated if resolution resolved."""
    row = dict(snapshot_row)
    if resolution.get("resolved") and resolution.get("event_id"):
        row["event_id"] = resolution["event_id"]
    return row


# ---------------------------------------------------------------------------
# Load canonical events from SQLite (read‐only)
# ---------------------------------------------------------------------------

def load_canonical_events_from_sqlite(
    db_path: str | Path,
    limit: int | None = None,
) -> dict[str, Any]:
    """Read canonical events from historical_events table."""
    try:
        from automation_scheduler.historical_odds_sqlite import (
            connect_historical_odds_db,
            initialize_historical_odds_db,
        )
    except ImportError:
        return {
            "ok": False,
            "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
            "total_events": 0,
            "events": [],
            "warnings": ["cannot import historical_odds_sqlite"],
        }

    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
    except Exception as exc:
        return {
            "ok": False,
            "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
            "total_events": 0,
            "events": [],
            "warnings": [f"cannot open database: {exc}"],
        }

    try:
        # Check table existence
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='historical_events'"
        ).fetchall()
        if not tables:
            conn.close()
            return {
                "ok": False,
                "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
                "total_events": 0,
                "events": [],
                "warnings": ["historical_events table does not exist"],
            }

        query = "SELECT * FROM historical_events"
        params: list[Any] = []
        if limit is not None and limit >= 0:
            query += " LIMIT ?"
            params.append(limit)
        rows = conn.execute(query, params).fetchall() if params else conn.execute(query).fetchall()
        events = [dict(row) for row in rows]
        conn.close()
        return {
            "ok": True,
            "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
            "total_events": len(events),
            "events": events,
            "warnings": [],
        }
    except Exception as exc:
        conn.close()
        return {
            "ok": False,
            "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
            "total_events": 0,
            "events": [],
            "warnings": [f"database error: {exc}"],
        }


# ---------------------------------------------------------------------------
# Dashboard‐friendly snapshot
# ---------------------------------------------------------------------------

def build_source_event_link_resolver_snapshot(
    source_rows: Sequence[Mapping[str, Any]] | None = None,
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    db_path: str | Path | None = None,
    min_score: int = 95,
    limit: int = 100,
) -> dict[str, Any]:
    """Dashboard wrapper for resolver."""
    messages = describe_source_event_link_resolver()
    warnings: list[str] = []

    # Load canonical events if not provided
    if canonical_event_rows is None and db_path is not None:
        loaded = load_canonical_events_from_sqlite(db_path)
        if loaded.get("ok"):
            canonical_event_rows = loaded["events"]
        else:
            warnings.extend(loaded.get("warnings", []))
            canonical_event_rows = []

    if canonical_event_rows is None:
        canonical_event_rows = []

    idx = build_event_link_index(canonical_event_rows)
    warnings.extend(idx.get("warnings", []))

    resolution = None
    if source_rows:
        resolution = resolve_source_event_links(
            source_rows,
            canonical_event_rows=canonical_event_rows,
            event_index=idx,
            min_score=min_score,
            limit=limit,
        )
        if resolution:
            warnings.extend(resolution.get("warnings", []))

    return {
        "ok": True,
        "version": SOURCE_EVENT_LINK_RESOLVER_VERSION,
        "event_index": idx,
        "resolution": resolution,
        "messages": messages,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Operator messages
# ---------------------------------------------------------------------------

def describe_source_event_link_resolver() -> list[str]:
    """Return operator messages."""
    return [
        "Source Event Link Resolver maps future source rows to canonical "
        "event_id values before line movement features are used.",
        "It does not connect to vendors, import paid data, or scrape.",
        "Ambiguous matches are not auto-linked.",
        "Phase 10H22 will use resolved event_id plus snapshot_time for "
        "as-of line movement queries.",
        "Future as-of queries must filter snapshot_time <= hypothetical_bet_time "
        "to prevent look-ahead bias.",
    ]
