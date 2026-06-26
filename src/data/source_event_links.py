from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


def normalize_event_link_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), sort_keys=True)
    if isinstance(value, Mapping):
        return json.dumps(dict(value), sort_keys=True)
    text = str(value).strip()
    return text


def normalize_event_link_token(value: Any) -> str:
    text = normalize_event_link_value(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def normalize_event_link_date(value: Any) -> str:
    text = normalize_event_link_value(value)
    if not text:
        return ""
    candidate = text
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return normalize_event_link_token(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.date().isoformat()


def build_event_link_key(row: Mapping[str, Any]) -> str:
    payload = dict(row)
    return "|".join(
        [
            normalize_event_link_token(payload.get("sport")),
            normalize_event_link_token(payload.get("league")),
            normalize_event_link_date(payload.get("event_date")),
            normalize_event_link_token(payload.get("home_team")),
            normalize_event_link_token(payload.get("away_team")),
        ]
    )


def build_reversed_event_link_key(row: Mapping[str, Any]) -> str:
    payload = dict(row)
    return "|".join(
        [
            normalize_event_link_token(payload.get("sport")),
            normalize_event_link_token(payload.get("league")),
            normalize_event_link_date(payload.get("event_date")),
            normalize_event_link_token(payload.get("away_team")),
            normalize_event_link_token(payload.get("home_team")),
        ]
    )


def score_event_link_candidate(
    source_row: Mapping[str, Any],
    candidate_row: Mapping[str, Any],
) -> dict[str, Any]:
    source = dict(source_row)
    cand = dict(candidate_row)
    reasons: list[str] = []
    score = 0
    source_key = build_event_link_key(source)
    cand_key = build_event_link_key(cand)
    reversed_key = build_reversed_event_link_key(cand)
    if source_key == cand_key:
        score = 100
        reasons.append("exact_event_key")
        reversed_home_away = False
    elif source_key == reversed_key:
        score = 90
        reasons.append("reversed_home_away")
        reversed_home_away = True
    else:
        if normalize_event_link_token(source.get("sport")) == normalize_event_link_token(cand.get("sport")):
            score += 25
        if normalize_event_link_token(source.get("league")) == normalize_event_link_token(cand.get("league")):
            score += 5
        if normalize_event_link_date(source.get("event_date")) and normalize_event_link_date(source.get("event_date")) == normalize_event_link_date(cand.get("event_date")):
            score += 30
        if normalize_event_link_token(source.get("home_team")) == normalize_event_link_token(cand.get("home_team")) and normalize_event_link_token(source.get("away_team")) == normalize_event_link_token(cand.get("away_team")):
            score += 40
        elif normalize_event_link_token(source.get("home_team")) == normalize_event_link_token(cand.get("away_team")) and normalize_event_link_token(source.get("away_team")) == normalize_event_link_token(cand.get("home_team")):
            score += 30
            reasons.append("reversed_home_away")
            reversed_home_away = True
        else:
            reversed_home_away = False
        if not source.get("event_date"):
            reasons.append("missing source event_date")
    return {
        "score": score,
        "reasons": reasons,
        "reversed_home_away": reversed_home_away,
    }


def build_event_link_index(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    index: dict[str, list[str]] = {}
    total = 0
    warnings: list[str] = []
    for row in rows:
        payload = dict(row)
        event_id = payload.get("event_id")
        if not event_id:
            warnings.append("missing_event_id")
            continue
        total += 1
        key = build_event_link_key(payload)
        index.setdefault(key, []).append(str(event_id))
    return {
        "ok": True,
        "status": "indexed",
        "total_events": total,
        "event_key_index": index,
        "warnings": warnings,
    }


def resolve_source_event_link(
    source_row: Mapping[str, Any],
    *,
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: Mapping[str, Any] | None = None,
    min_score: int = 80,
) -> dict[str, Any]:
    source = dict(source_row)
    if source.get("event_id"):
        return {
            "resolved": True,
            "event_id": source.get("event_id"),
            "match_method": "existing_event_id",
            "score": 100,
            "match_score": 100,
            "warnings": [],
        }
    candidates = [dict(row) for row in (canonical_event_rows or [])]
    if not candidates and event_index:
        event_key_index = event_index.get("event_key_index") if isinstance(event_index, Mapping) else None
        if isinstance(event_key_index, Mapping):
            for event_ids in event_key_index.values():
                if isinstance(event_ids, Sequence):
                    for event_id in event_ids:
                        candidates.append({"event_id": event_id})
    if source.get("source_event_id") and source.get("source_key"):
        for candidate in candidates:
            if candidate.get("source_event_id") == source.get("source_event_id") and candidate.get("source_key") == source.get("source_key"):
                return {
                    "resolved": True,
                    "event_id": candidate.get("event_id"),
                    "match_method": "source_event_id",
                    "score": 100,
                    "match_score": 100,
                    "warnings": [],
                }
    scores = [score_event_link_candidate(source, candidate) | {"event_id": candidate.get("event_id"), "candidate": candidate} for candidate in candidates]
    if not scores:
        return {"resolved": False, "event_id": None, "match_method": "no_candidates", "score": 0, "match_score": 0, "warnings": ["no_candidates"], "reasons": ["no_candidates"]}
    scores.sort(key=lambda item: (item["score"], item["event_id"] or ""), reverse=True)
    top = scores[0]
    if len(scores) > 1 and scores[0]["score"] == scores[1]["score"]:
        return {"resolved": False, "event_id": None, "match_method": "ambiguous", "score": top["score"], "match_score": top["score"], "warnings": ["ambiguous_candidates"], "reasons": ["ambiguous_candidates"]}
    if top["score"] >= min_score:
        return {
            "resolved": True,
            "event_id": top["event_id"],
            "match_method": "reversed_home_away" if top["reversed_home_away"] else "exact_event_key" if top["score"] == 100 else "scored_match",
            "score": top["score"],
            "match_score": top["score"],
            "warnings": [],
            "reasons": top.get("reasons", []),
        }
    return {"resolved": False, "event_id": None, "match_method": "below_min_score", "score": top["score"], "match_score": top["score"], "warnings": ["below_min_score"], "reasons": ["below_min_score"]}


def resolve_source_event_links(
    source_rows: Sequence[Mapping[str, Any]],
    *,
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: Mapping[str, Any] | None = None,
    min_score: int = 80,
    limit: int | None = None,
) -> dict[str, Any]:
    rows = list(source_rows or [])
    if limit is not None:
        rows = rows[: max(0, int(limit))]
    if not rows:
        return {"ok": True, "warnings": ["no_rows"], "total_rows": 0, "resolved_rows": 0, "unresolved_rows": 0, "rows": []}
    results = []
    resolved = 0
    for row in rows:
        result = resolve_source_event_link(row, canonical_event_rows=canonical_event_rows, event_index=event_index, min_score=min_score)
        if result.get("resolved"):
            resolved += 1
        results.append(result)
    return {
        "ok": True,
        "warnings": [],
        "total_rows": len(rows),
        "resolved_rows": resolved,
        "unresolved_rows": len(rows) - resolved,
        "rows": results,
    }


def apply_resolved_event_id_to_snapshot_row(
    snapshot_row: Mapping[str, Any],
    resolution: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(snapshot_row)
    if resolution.get("resolved") and resolution.get("event_id"):
        payload["event_id"] = resolution.get("event_id")
    return payload


def load_canonical_events_from_sqlite(conn_or_path: str | Path | sqlite3.Connection) -> dict[str, Any]:
    if isinstance(conn_or_path, sqlite3.Connection):
        conn = conn_or_path
        should_close = False
    else:
        path = Path(conn_or_path)
        if not path.exists():
            return {"ok": False, "warnings": ["missing_db"], "events": [], "total_events": 0}
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        should_close = True
    try:
        try:
            rows = conn.execute("SELECT * FROM historical_events").fetchall()
        except sqlite3.DatabaseError:
            rows = []
        events = [dict(row) for row in rows]
    finally:
        if should_close:
            conn.close()
    return {"ok": True, "warnings": [], "events": events, "total_events": len(events)}


def build_source_event_link_resolver_snapshot(
    *,
    source_rows: Sequence[Mapping[str, Any]] | None = None,
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    db_path: str | Path | None = None,
    min_score: int = 80,
    limit: int | None = None,
) -> dict[str, Any]:
    sources = list(source_rows or [])
    if not sources and db_path is not None:
        loaded = load_canonical_events_from_sqlite(db_path)
        if loaded.get("ok"):
            canonical_event_rows = loaded.get("events", [])
    resolution = resolve_source_event_links(
        sources,
        canonical_event_rows=canonical_event_rows,
        min_score=min_score,
        limit=limit,
    )
    return {
        "ok": True,
        "event_index": build_event_link_index(canonical_event_rows or []),
        "resolution": resolution if sources else None,
        "snapshot_count": len(sources),
    }


def describe_source_event_link_resolver() -> list[str]:
    return [
        "Source event link resolver is local-only.",
        "It does not connect to vendors.",
        "Phase 10H22 canonical resolver.",
    ]


__all__ = [
    "apply_resolved_event_id_to_snapshot_row",
    "build_event_link_index",
    "build_event_link_key",
    "build_reversed_event_link_key",
    "build_source_event_link_resolver_snapshot",
    "describe_source_event_link_resolver",
    "load_canonical_events_from_sqlite",
    "normalize_event_link_date",
    "normalize_event_link_token",
    "normalize_event_link_value",
    "resolve_source_event_link",
    "resolve_source_event_links",
    "score_event_link_candidate",
]
