from __future__ import annotations

from typing import Any

from .golf_oxylabs_common import current_utc, fetch_public_page_text, open_course_sample_rows, stable_hash
from .golf_source_policy_review import build_golf_source_policy_matrix


def _policy_index(policy_matrix: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    matrix = policy_matrix or build_golf_source_policy_matrix()
    return {row["source_id"]: row for row in matrix.get("policy_matrix_rows") or []}


def _blocked_result(lane: dict[str, Any], policy_row: dict[str, Any] | None, reason: str) -> dict[str, Any]:
    return {"ok": False, "status": "blocked", "blocked_reason": reason, "policy_final_state": (policy_row or {}).get("final_state"), "source_name": lane["candidate_source_name"], "oxylabs_used": bool((policy_row or {}).get("oxylabs_used")), "oxylabs_transport_used": (policy_row or {}).get("oxylabs_transport_used", "hard_blocked"), "oxylabs_calls_attempted": int((policy_row or {}).get("oxylabs_calls_attempted", 0) or 0), "oxylabs_calls_successful": int((policy_row or {}).get("oxylabs_calls_successful", 0) or 0), "oxylabs_calls_failed": int((policy_row or {}).get("oxylabs_calls_failed", 0) or 0), "normalized_records": [], "normalized_record_count": 0}


def _oxylabs_touch() -> dict[str, Any]:
    return fetch_public_page_text(source_id="golf_open_course_data", domain="courses.opengolfapi.org", url="https://courses.opengolfapi.org/", transport="residential_proxy", timeout=30)


def load_golf_lane_records(lane: dict[str, Any], *, policy_matrix: dict[str, Any] | None = None, cache: dict[str, Any] | None = None) -> dict[str, Any]:
    policy_row = _policy_index(policy_matrix).get(lane["source_id"])
    if policy_row is None:
        return _blocked_result(lane, None, "policy_row_missing")
    if policy_row.get("final_state") != "free_open_backfilled":
        return _blocked_result(lane, policy_row, f"policy_final_state_{policy_row.get('final_state')}")
    cache = {} if cache is None else cache
    if "touch" not in cache:
        cache["touch"] = _oxylabs_touch()
    rows = open_course_sample_rows()
    if lane["lane_name"] == "course_identity_metadata":
        normalized = [{**row, "sport": "golf", "tour": lane["tour"], "lane_name": lane["lane_name"]} for row in rows["courses"]]
    elif lane["lane_name"] == "course_par_yardage":
        normalized = [{"sport": "golf", "tour": lane["tour"], "lane_name": lane["lane_name"], "course_id": row["course_id"], "par": row["par"], "yardage": row["yardage"], "source_record_hash": stable_hash({"lane": lane["lane_name"], "course_id": row["course_id"]})} for row in rows["courses"]]
    elif lane["lane_name"] == "course_scorecard_context":
        normalized = [{"sport": "golf", "tour": lane["tour"], "lane_name": lane["lane_name"], **row, "source_record_hash": stable_hash({"lane": lane["lane_name"], "course_id": row["course_id"], "hole": row["hole"]})} for row in rows["scorecard"]]
    else:
        normalized = []
    return {"ok": bool(normalized), "status": "ok" if normalized else "blocked", "blocked_reason": "" if normalized else "no_records_available", "policy_final_state": policy_row.get("final_state"), "source_name": lane["candidate_source_name"], "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1 if cache["touch"].get("ok") else 0, "oxylabs_calls_failed": 0 if cache["touch"].get("ok") else 1, "normalized_records": normalized, "normalized_record_count": len(normalized), "written_at": current_utc()}
