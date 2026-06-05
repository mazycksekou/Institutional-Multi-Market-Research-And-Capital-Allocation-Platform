from __future__ import annotations

from pathlib import Path
from typing import Any

from .soccer_free_data_loader import load_soccer_lane_records
from .soccer_free_vs_paid_readiness import RUN_MODE, _new_fields_for_lane, soccer_lane_catalog
from .soccer_oxylabs_common import current_utc, lane_final_state, write_json, write_md


REPORT_ROOT = Path("reports")


def _sample_lane(lane: dict[str, Any], *, cache: dict[str, Any] | None = None) -> dict[str, Any]:
    if not lane.get("loader_exists"):
        hard_blocker = lane["free_or_paid_category"] in {
            "free_open_manual_import_needed",
            "paid_data_subscription_required",
            "license_terms_unclear",
            "blocked_reference_or_restricted_source",
            "obsolete_or_duplicate",
        }
        return {
            "sport": lane["sport"],
            "league_or_competition": "Bundesliga",
            "lane_name": lane["lane_name"],
            "sample_type": "hard_blocker" if hard_blocker else "not_required",
            "sample_scope": "",
            "source_used": lane["candidate_source_name"],
            "oxylabs_used": not hard_blocker or lane["free_or_paid_category"] != "blocked_reference_or_restricted_source",
            "oxylabs_transport_used": "hard_blocked" if lane["free_or_paid_category"] == "blocked_reference_or_restricted_source" else lane["retrieval_method"],
            "policy_status": lane["policy_status"],
            "records_tested": 0,
            "fields_expected": list(lane["fields"]),
            "fields_found": [],
            "fields_missing": list(lane["fields"]),
            "repo_fields_mapped": list(lane["fields"]),
            "new_fields_recommended": [],
            "validation_status": "hard_blocked" if hard_blocker else "not_required",
            "loader_recommendation": lane["next_action"],
            "backfill_recommendation": lane["next_action"],
            "final_actionable_state": lane_final_state(
                lane,
                backfill_written=False,
                hard_blocked=lane["free_or_paid_category"] == "blocked_reference_or_restricted_source",
            ),
            "sample_attempted": False,
            "hard_blocker": hard_blocker,
            "blocked_reason": lane["final_reason"],
        }
    result = load_soccer_lane_records(lane, cache=cache)
    records = list(result.get("normalized_records") or [])
    fields_found = sorted({key for row in records[:10] for key in row.keys()})
    missing = [field for field in lane["fields"] if field not in fields_found]
    if result.get("ok") and not missing:
        validation_status = "sample_verified"
    elif not result.get("ok"):
        validation_status = "hard_blocked"
    else:
        validation_status = "validation_failed"
    sample_type = "one_match" if lane.get("entity_level", "match") in {"match", "team_match", "player_match", "event"} else "one_team"
    return {
        "sport": lane["sport"],
        "league_or_competition": "Bundesliga",
        "lane_name": lane["lane_name"],
        "sample_type": sample_type,
        "sample_scope": "bundesliga_2023_2024_public_sample_scope",
        "source_used": result.get("source_name") or lane["candidate_source_name"],
        "oxylabs_used": bool(result.get("oxylabs_used")),
        "oxylabs_transport_used": result.get("oxylabs_transport_used"),
        "policy_status": lane["policy_status"],
        "records_tested": int(result.get("normalized_record_count", 0) or 0),
        "fields_expected": list(lane["fields"]),
        "fields_found": fields_found,
        "fields_missing": missing,
        "repo_fields_mapped": list(lane["fields"]),
        "new_fields_recommended": _new_fields_for_lane(lane),
        "validation_status": validation_status,
        "loader_recommendation": "loader_ready" if validation_status == "sample_verified" else "hard_blocked" if validation_status == "hard_blocked" else "validation_failed",
        "backfill_recommendation": lane["next_action"] if validation_status == "sample_verified" else "hard_blocked" if validation_status == "hard_blocked" else "validation_failed",
        "final_actionable_state": lane_final_state(lane, backfill_written=bool(result.get("ok")), hard_blocked=not bool(result.get("ok"))),
        "sample_attempted": True,
        "hard_blocker": False,
        "blocked_reason": result.get("blocked_reason"),
    }


def build_soccer_targeted_sample_verification_results() -> dict[str, Any]:
    cache: dict[str, Any] = {}
    rows = [_sample_lane(lane, cache=cache) for lane in soccer_lane_catalog()]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "SOCCER_TARGETED_SAMPLE_VERIFICATION_RESULTS",
        "schema_version": "soccer_targeted_sample_verification_v1",
        "created_at": current_utc(),
        "run_mode": RUN_MODE,
        "sample_results": rows,
        "source_result_index": {f"{row['sport']}::{row['lane_name']}": row for row in rows},
        "sample_verified_count": sum(1 for row in rows if row["validation_status"] == "sample_verified"),
        "sample_blocked_count": sum(1 for row in rows if row["validation_status"] == "hard_blocked"),
        "sample_failed_count": sum(1 for row in rows if row["validation_status"] == "validation_failed"),
        "records_tested_total": sum(int(row.get("records_tested", 0) or 0) for row in rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_soccer_targeted_sample_verification_results(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "SOCCER_TARGETED_SAMPLE_VERIFICATION_RESULTS.json"
    md_path = root / "SOCCER_TARGETED_SAMPLE_VERIFICATION_RESULTS.md"
    write_json(json_path, report)
    lines = [
        "# Soccer Targeted Sample Verification Results",
        "",
        f"1. sample_verified_count: {report.get('sample_verified_count')}",
        f"2. sample_blocked_count: {report.get('sample_blocked_count')}",
        f"3. sample_failed_count: {report.get('sample_failed_count')}",
        f"4. records_tested_total: {report.get('records_tested_total')}",
        "",
        "## Lanes",
    ]
    for row in report.get("sample_results") or []:
        lines.append(
            f"- {row.get('lane_name')} status={row.get('validation_status')} records={row.get('records_tested')} transport={row.get('oxylabs_transport_used')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
