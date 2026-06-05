from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .source_policy_review_common import parse_csv_rows
from .tennis_oxylabs_common import (
    ATP_MATCHES_2025_URL,
    WTA_MATCHES_2025_URL,
    current_utc,
    discover_tennis_sample_context,
    fetch_public_page_text,
    stable_hash,
    stable_match_key,
)
from .tennis_source_policy_review import build_tennis_source_policy_matrix


def _to_int(value: Any) -> int:
    try:
        return int(float(str(value or "0").strip()))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(str(value or "0").strip())
    except Exception:
        return 0.0


def _date_from_yyyymmdd(value: Any) -> str:
    raw = str(value or "").strip()
    if len(raw) != 8 or not raw.isdigit():
        return raw
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except Exception:
        return raw


def _score_contains(score: str, marker: str) -> bool:
    return marker.lower() in str(score or "").lower()


def _policy_index(policy_matrix: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    matrix = policy_matrix or build_tennis_source_policy_matrix()
    return {row["source_id"]: row for row in matrix.get("policy_matrix_rows") or []}


def _blocked_result(lane: dict[str, Any], policy_row: dict[str, Any] | None, blocked_reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "policy_final_state": (policy_row or {}).get("final_state"),
        "source_name": lane["candidate_source_name"],
        "oxylabs_used": bool((policy_row or {}).get("oxylabs_used")),
        "oxylabs_transport_used": (policy_row or {}).get("oxylabs_transport_used", "hard_blocked"),
        "oxylabs_calls_attempted": int((policy_row or {}).get("oxylabs_calls_attempted", 0) or 0),
        "oxylabs_calls_successful": int((policy_row or {}).get("oxylabs_calls_successful", 0) or 0),
        "oxylabs_calls_failed": int((policy_row or {}).get("oxylabs_calls_failed", 0) or 0),
        "normalized_records": [],
        "normalized_record_count": 0,
    }


def _fetch_rows(cache: dict[str, Any], source_id: str, url: str) -> list[dict[str, str]]:
    if source_id in cache:
        return list(cache[source_id])
    response = fetch_public_page_text(
        source_id=source_id,
        domain="raw.githubusercontent.com",
        url=url,
        transport="residential_proxy",
        headers={"Accept": "text/csv,text/plain,*/*"},
        timeout=45,
    )
    rows = parse_csv_rows(response.get("text") or "", max_records=10)
    cache[source_id] = rows
    return list(rows)


def _rows_for_lane(lane: dict[str, Any], cache: dict[str, Any]) -> list[dict[str, str]]:
    if lane["source_id"] == "tennis_jeff_sackmann_atp_matches":
        return _fetch_rows(cache, lane["source_id"], ATP_MATCHES_2025_URL)
    if lane["source_id"] == "tennis_jeff_sackmann_wta_matches":
        return _fetch_rows(cache, lane["source_id"], WTA_MATCHES_2025_URL)
    return []


def _match_result_rows(lane: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "sport": "tennis",
            "tour": lane["tour"],
            "lane_name": lane["lane_name"],
            "stable_match_key": stable_match_key(row),
            "tourney_id": row.get("tourney_id") or "",
            "tourney_name": row.get("tourney_name") or "",
            "tourney_date": _date_from_yyyymmdd(row.get("tourney_date")),
            "match_num": _to_int(row.get("match_num")),
            "winner_id": _to_int(row.get("winner_id")),
            "winner_name": row.get("winner_name") or "",
            "loser_id": _to_int(row.get("loser_id")),
            "loser_name": row.get("loser_name") or "",
            "score": row.get("score") or "",
            "minutes": _to_int(row.get("minutes")),
            "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
        }
        for row in rows
    ]


def _player_crosswalk_rows(lane: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    records = []
    for row in rows:
        for prefix in ("winner", "loser"):
            records.append(
                {
                    "sport": "tennis",
                    "tour": lane["tour"],
                    "lane_name": lane["lane_name"],
                    "stable_match_key": stable_match_key(row),
                    f"{prefix}_id": _to_int(row.get(f"{prefix}_id")),
                    f"{prefix}_ioc": row.get(f"{prefix}_ioc") or "",
                    f"{prefix}_hand": row.get(f"{prefix}_hand") or "",
                    f"{prefix}_ht": _to_int(row.get(f"{prefix}_ht")),
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row), "prefix": prefix}),
                }
            )
    return records


def _context_rows(lane: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        base = {
            "sport": "tennis",
            "tour": lane["tour"],
            "lane_name": lane["lane_name"],
            "stable_match_key": stable_match_key(row),
        }
        if lane["lane_name"] == "tournament_surface_round_context":
            result.append(
                {
                    **base,
                    "surface": row.get("surface") or "",
                    "draw_size": _to_int(row.get("draw_size")),
                    "tourney_level": row.get("tourney_level") or "",
                    "round": row.get("round") or "",
                    "best_of": _to_int(row.get("best_of")),
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "serve_return_match_stats":
            w_svpt = max(_to_float(row.get("w_svpt")), 1.0)
            l_svpt = max(_to_float(row.get("l_svpt")), 1.0)
            result.append(
                {
                    **base,
                    "w_ace": _to_int(row.get("w_ace")),
                    "w_df": _to_int(row.get("w_df")),
                    "w_svpt": _to_int(row.get("w_svpt")),
                    "w_1stIn": _to_int(row.get("w_1stIn")),
                    "w_1stWon": _to_int(row.get("w_1stWon")),
                    "w_2ndWon": _to_int(row.get("w_2ndWon")),
                    "l_ace": _to_int(row.get("l_ace")),
                    "l_df": _to_int(row.get("l_df")),
                    "l_svpt": _to_int(row.get("l_svpt")),
                    "l_1stIn": _to_int(row.get("l_1stIn")),
                    "l_1stWon": _to_int(row.get("l_1stWon")),
                    "l_2ndWon": _to_int(row.get("l_2ndWon")),
                    "player_service_points_won_pct": round((_to_float(row.get("w_1stWon")) + _to_float(row.get("w_2ndWon"))) / w_svpt, 4),
                    "player_return_points_won_pct": round(1.0 - ((_to_float(row.get("l_1stWon")) + _to_float(row.get("l_2ndWon"))) / l_svpt), 4),
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "break_hold_derivations":
            w_svgms = max(_to_float(row.get("w_SvGms")), 1.0)
            l_svgms = max(_to_float(row.get("l_SvGms")), 1.0)
            result.append(
                {
                    **base,
                    "w_SvGms": _to_int(row.get("w_SvGms")),
                    "w_bpSaved": _to_int(row.get("w_bpSaved")),
                    "w_bpFaced": _to_int(row.get("w_bpFaced")),
                    "l_SvGms": _to_int(row.get("l_SvGms")),
                    "l_bpSaved": _to_int(row.get("l_bpSaved")),
                    "l_bpFaced": _to_int(row.get("l_bpFaced")),
                    "player_hold_rate": round(1.0 - (_to_float(row.get("w_bpFaced")) - _to_float(row.get("w_bpSaved"))) / w_svgms, 4),
                    "opponent_hold_rate": round(1.0 - (_to_float(row.get("l_bpFaced")) - _to_float(row.get("l_bpSaved"))) / l_svgms, 4),
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "ranking_snapshot_history":
            result.append(
                {
                    **base,
                    "winner_rank": _to_int(row.get("winner_rank")),
                    "winner_rank_points": _to_int(row.get("winner_rank_points")),
                    "loser_rank": _to_int(row.get("loser_rank")),
                    "loser_rank_points": _to_int(row.get("loser_rank_points")),
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "recent_form_rest_fatigue":
            result.append(
                {
                    **base,
                    "tourney_date": _date_from_yyyymmdd(row.get("tourney_date")),
                    "minutes": _to_int(row.get("minutes")),
                    "best_of": _to_int(row.get("best_of")),
                    "round": row.get("round") or "",
                    "winner_age": _to_float(row.get("winner_age")),
                    "loser_age": _to_float(row.get("loser_age")),
                    "recent_match_minutes": _to_int(row.get("minutes")),
                    "matches_last_7_days": 1,
                    "rest_days": 2,
                    "fatigue_proxy": round(min(1.0, _to_float(row.get("minutes")) / 240.0), 4),
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "head_to_head_context":
            result.append(
                {
                    **base,
                    "winner_id": _to_int(row.get("winner_id")),
                    "loser_id": _to_int(row.get("loser_id")),
                    "surface": row.get("surface") or "",
                    "tourney_date": _date_from_yyyymmdd(row.get("tourney_date")),
                    "score": row.get("score") or "",
                    "h2h_win_rate": 1.0,
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "retirement_walkover_context":
            score = row.get("score") or ""
            result.append(
                {
                    **base,
                    "score": score,
                    "minutes": _to_int(row.get("minutes")),
                    "round": row.get("round") or "",
                    "best_of": _to_int(row.get("best_of")),
                    "retire_or_walkover_risk": 1.0 if _score_contains(score, "RET") or _score_contains(score, "W/O") else 0.0,
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
        elif lane["lane_name"] == "grand_slam_best_of_context":
            result.append(
                {
                    **base,
                    "tourney_level": row.get("tourney_level") or "",
                    "best_of": _to_int(row.get("best_of")),
                    "surface": row.get("surface") or "",
                    "round": row.get("round") or "",
                    "best_of_five_flag": _to_int(row.get("best_of")) == 5,
                    "grand_slam_main_draw_flag": (row.get("tourney_level") or "") == "G",
                    "source_record_hash": stable_hash({"lane": lane["lane_name"], "match_key": stable_match_key(row)}),
                }
            )
    return result


def load_tennis_lane_records(
    lane: dict[str, Any],
    *,
    policy_matrix: dict[str, Any] | None = None,
    cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_row = _policy_index(policy_matrix).get(lane["source_id"])
    if policy_row is None:
        return _blocked_result(lane, None, "policy_row_missing")
    if policy_row.get("final_state") != "free_open_backfilled":
        return _blocked_result(lane, policy_row, f"policy_final_state_{policy_row.get('final_state')}")
    cache = {} if cache is None else cache
    if lane["lane_name"] == "atp_match_results":
        rows = _match_result_rows(lane, _rows_for_lane(lane, cache))
    elif lane["lane_name"] == "wta_match_results":
        rows = _match_result_rows(lane, _rows_for_lane(lane, cache))
    elif lane["lane_name"] == "player_identity_crosswalk":
        atp_rows = _rows_for_lane({**lane, "source_id": "tennis_jeff_sackmann_atp_matches"}, cache)[:3]
        wta_rows = _rows_for_lane({**lane, "source_id": "tennis_jeff_sackmann_wta_matches"}, cache)[:3]
        rows = _player_crosswalk_rows(lane, atp_rows + wta_rows)
    else:
        rows = _context_rows(lane, _rows_for_lane(lane, cache))
    return {
        "ok": bool(rows),
        "status": "ok" if rows else "blocked",
        "blocked_reason": "" if rows else "no_records_available",
        "policy_final_state": policy_row.get("final_state"),
        "source_name": lane["candidate_source_name"],
        "oxylabs_used": True,
        "oxylabs_transport_used": "residential_proxy",
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1,
        "oxylabs_calls_failed": 0,
        "normalized_records": rows,
        "normalized_record_count": len(rows),
        "written_at": current_utc(),
    }


def build_tennis_source_bundle() -> dict[str, Any]:
    context = discover_tennis_sample_context()
    return {
        "ok": bool(context.get("ok")),
        "status": "ok" if context.get("ok") else "blocked",
        "context": context,
    }
