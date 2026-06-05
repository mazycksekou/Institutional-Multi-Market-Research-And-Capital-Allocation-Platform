from __future__ import annotations

from typing import Any

from .source_policy_review_common import parse_csv_rows
from .combat_oxylabs_common import (
    OPEN_BOXING_BOUTS_URL,
    OPEN_BOXING_CHAMPIONS_URL,
    OPEN_BOXING_LOCATIONS_URL,
    OPEN_BOXING_REIGNS_URL,
    OPEN_BOXING_TITLES_URL,
    current_utc,
    fetch_public_page_text,
    stable_bout_key,
    stable_hash,
)
from .combat_source_policy_review import build_combat_source_policy_matrix


def _policy_index(policy_matrix: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    matrix = policy_matrix or build_combat_source_policy_matrix()
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


def _fetch_csv_bundle(cache: dict[str, Any], key: str, url: str) -> dict[str, Any]:
    if key in cache:
        return dict(cache[key])
    bundle = {"response": {}, "rows": []}
    for _ in range(2):
        response = fetch_public_page_text(
            source_id="combat_open_boxing_data_repo",
            domain="raw.githubusercontent.com",
            url=url,
            transport="residential_proxy",
            headers={"Accept": "text/csv,text/plain,*/*"},
            timeout=45,
        )
        bundle = {"response": response, "rows": parse_csv_rows(response.get("text") or "", max_records=50)}
        if bundle["rows"]:
            break
    cache[key] = bundle
    return dict(bundle)


def _boxing_bout_rows(cache: dict[str, Any]) -> list[dict[str, str]]:
    return list(_fetch_csv_bundle(cache, "bouts", OPEN_BOXING_BOUTS_URL)["rows"])


def _boxing_champion_rows(cache: dict[str, Any]) -> list[dict[str, str]]:
    return list(_fetch_csv_bundle(cache, "champions", OPEN_BOXING_CHAMPIONS_URL)["rows"])


def _boxing_title_rows(cache: dict[str, Any]) -> list[dict[str, str]]:
    return list(_fetch_csv_bundle(cache, "titles", OPEN_BOXING_TITLES_URL)["rows"])


def _boxing_reign_rows(cache: dict[str, Any]) -> list[dict[str, str]]:
    return list(_fetch_csv_bundle(cache, "reigns", OPEN_BOXING_REIGNS_URL)["rows"])


def _boxing_location_rows(cache: dict[str, Any]) -> list[dict[str, str]]:
    return list(_fetch_csv_bundle(cache, "locations", OPEN_BOXING_LOCATIONS_URL)["rows"])


def _boxing_bout_result_rows(lane: dict[str, Any], cache: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _boxing_bout_rows(cache)[:5]:
        rows.append(
            {
                "sport": "combat",
                "combat_type": lane["combat_type"],
                "lane_name": lane["lane_name"],
                "stable_bout_key": stable_bout_key(row),
                "bout_id": int(row.get("bout_id") or 0),
                "date": row.get("date") or "",
                "boxer_a_name": row.get("boxer_a_name") or "",
                "boxer_b_name": row.get("boxer_b_name") or "",
                "status": row.get("status") or "",
                "winner": row.get("winner") or "",
                "method_of_victory": row.get("method_of_victory") or "",
                "total_rounds": int(row.get("total_rounds") or 0),
                "scheduled_rounds": int(row.get("scheduled_rounds") or 0),
                "weight_class": row.get("weight_class") or "",
                "source_record_hash": stable_hash({"lane": lane["lane_name"], "bout_id": row.get("bout_id")}),
            }
        )
    return rows


def _boxing_fighter_rows(lane: dict[str, Any], cache: dict[str, Any]) -> list[dict[str, Any]]:
    bouts = _boxing_bout_rows(cache)[:5]
    champion_ids = []
    for row in bouts:
        champion_ids.extend([row.get("boxer_a_champion_id"), row.get("boxer_b_champion_id")])
    wanted = {str(value or "").strip() for value in champion_ids if str(value or "").strip()}
    champions = {str(row.get("champion_id") or "").strip(): row for row in _boxing_champion_rows(cache)}
    rows = []
    for champion_id in sorted(wanted)[:5]:
        champion = champions.get(champion_id)
        if not champion:
            continue
        rows.append(
            {
                "sport": "combat",
                "combat_type": lane["combat_type"],
                "lane_name": lane["lane_name"],
                "champion_id": int(champion.get("champion_id") or 0),
                "first_name": champion.get("first_name") or "",
                "last_name": champion.get("last_name") or "",
                "short_name": champion.get("short_name") or "",
                "born": champion.get("born") or "",
                "source_record_hash": stable_hash({"lane": lane["lane_name"], "champion_id": champion.get("champion_id")}),
            }
        )
    return rows


def _boxing_finish_rows(lane: dict[str, Any], cache: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _boxing_bout_rows(cache)[:5]:
        method = row.get("method_of_victory") or ""
        status = row.get("status") or ""
        rows.append(
            {
                "sport": "combat",
                "combat_type": lane["combat_type"],
                "lane_name": lane["lane_name"],
                "stable_bout_key": stable_bout_key(row),
                "method_of_victory": method,
                "winner": row.get("winner") or "",
                "status": status,
                "total_rounds": int(row.get("total_rounds") or 0),
                "scheduled_rounds": int(row.get("scheduled_rounds") or 0),
                "weight_class": row.get("weight_class") or "",
                "titles": row.get("titles") or "",
                "inside_distance_flag": method not in {"PTS", "UD", "MD", "SD"},
                "decision_flag": method in {"PTS", "UD", "MD", "SD"},
                "stoppage_flag": method not in {"PTS", "UD", "MD", "SD"},
                "source_record_hash": stable_hash({"lane": lane["lane_name"], "bout_id": row.get("bout_id")}),
            }
        )
    return rows


def _boxing_title_rows_normalized(lane: dict[str, Any], cache: dict[str, Any]) -> list[dict[str, Any]]:
    titles = _boxing_title_rows(cache)
    title_lookup = {
        f"{row.get('org_abbreviation')}-{row.get('weight_class')}-{row.get('weight_lb')}": row
        for row in titles
    }
    rows = []
    for reign in _boxing_reign_rows(cache)[:5]:
        title = title_lookup.get(reign.get("title") or "", {})
        rows.append(
            {
                "sport": "combat",
                "combat_type": lane["combat_type"],
                "lane_name": lane["lane_name"],
                "reign_id": int(reign.get("reign_id") or 0),
                "begins": reign.get("begins") or "",
                "ends": reign.get("ends") or "",
                "champion_id": int(reign.get("champion_id") or 0),
                "name": reign.get("name") or "",
                "current": str(reign.get("current") or "0") == "1",
                "title": reign.get("title") or "",
                "org_abbreviation": title.get("org_abbreviation") or "",
                "source_record_hash": stable_hash({"lane": lane["lane_name"], "reign_id": reign.get("reign_id")}),
            }
        )
    return rows


def _boxing_location_rows_normalized(lane: dict[str, Any], cache: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for location in _boxing_location_rows(cache)[:5]:
        rows.append(
            {
                "sport": "combat",
                "combat_type": lane["combat_type"],
                "lane_name": lane["lane_name"],
                "location_id": int(location.get("location_id") or 0),
                "venue": location.get("venue") or "",
                "locality": location.get("locality") or "",
                "country": location.get("country") or "",
                "latitude": float(location.get("latitude") or 0.0),
                "longitude": float(location.get("longitude") or 0.0),
                "source_record_hash": stable_hash({"lane": lane["lane_name"], "location_id": location.get("location_id")}),
            }
        )
    return rows


def load_combat_lane_records(
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
    if lane["lane_name"] == "boxing_bout_results":
        rows = _boxing_bout_result_rows(lane, cache)
        calls = 1
    elif lane["lane_name"] == "boxing_fighter_identity_birthdates":
        rows = _boxing_fighter_rows(lane, cache)
        calls = 2
    elif lane["lane_name"] == "boxing_finish_round_context":
        rows = _boxing_finish_rows(lane, cache)
        calls = 1
    elif lane["lane_name"] == "boxing_title_reign_context":
        rows = _boxing_title_rows_normalized(lane, cache)
        calls = 2
    elif lane["lane_name"] == "boxing_location_context":
        rows = _boxing_location_rows_normalized(lane, cache)
        calls = 2
    else:
        rows = []
        calls = 0
    return {
        "ok": bool(rows),
        "status": "ok" if rows else "blocked",
        "blocked_reason": "" if rows else "no_records_available",
        "policy_final_state": policy_row.get("final_state"),
        "source_name": lane["candidate_source_name"],
        "oxylabs_used": True,
        "oxylabs_transport_used": "residential_proxy",
        "oxylabs_calls_attempted": calls,
        "oxylabs_calls_successful": calls if rows else 0,
        "oxylabs_calls_failed": 0 if rows else max(1, calls),
        "normalized_records": rows,
        "normalized_record_count": len(rows),
        "written_at": current_utc(),
    }


def build_combat_source_bundle() -> dict[str, Any]:
    cache: dict[str, Any] = {}
    bouts = _boxing_bout_rows(cache)
    champions = _boxing_champion_rows(cache)
    return {
        "ok": bool(bouts and champions),
        "status": "ok" if bouts and champions else "blocked",
        "bouts": len(bouts),
        "champions": len(champions),
    }
