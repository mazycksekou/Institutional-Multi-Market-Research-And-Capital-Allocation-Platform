from __future__ import annotations

from pathlib import Path
from typing import Any

from .combat_free_data_loader import load_combat_lane_records
from .combat_free_vs_paid_readiness import RUN_MODE, _new_fields_for_lane, combat_lane_catalog
from .combat_oxylabs_common import current_utc, lane_final_state, write_json, write_md
from .combat_safe_source_sampler import build_combat_safe_source_sample_report
from .combat_source_policy_review import build_combat_source_policy_matrix, combat_candidate_source_catalog


REPORT_ROOT = Path("reports")


def _policy_index(policy_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in policy_matrix.get("policy_matrix_rows") or []}


def _sample_index(sample_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in sample_report.get("sample_rows") or []}


def _sample_lane(
    lane: dict[str, Any],
    *,
    policy_matrix: dict[str, Any],
    sample_report: dict[str, Any],
    cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_row = _policy_index(policy_matrix).get(lane["source_id"], {})
    sample_row = _sample_index(sample_report).get(lane["source_id"], {})
    final_state = str(policy_row.get("final_state") or "")
    if final_state == "free_open_metadata_only" and lane["lane_name"] in {"fighter_metadata_entities", "promotion_roster_metadata"}:
        fields_found = sorted({key for row in sample_row.get("sample_rows") or [] for key in row.keys()})
        missing = [field for field in lane["fields"] if field not in fields_found]
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "sample_type": "one_structured_entity",
            "sample_scope": "metadata_only_source",
            "source_used": lane["candidate_source_name"],
            "oxylabs_used": bool(policy_row.get("oxylabs_used")),
            "oxylabs_transport_used": policy_row.get("oxylabs_transport_used"),
            "policy_status": lane["policy_status"],
            "records_tested": int(sample_row.get("records_tested", 0) or 0),
            "fields_expected": list(lane["fields"]),
            "fields_found": fields_found,
            "fields_missing": missing,
            "repo_fields_mapped": list(lane["fields"]),
            "new_fields_recommended": _new_fields_for_lane(lane),
            "validation_status": "sample_verified" if not missing else "validation_failed",
            "loader_recommendation": "metadata_only",
            "backfill_recommendation": "metadata_only",
            "final_actionable_state": "free_open_metadata_only",
            "sample_attempted": True,
            "hard_blocker": False,
            "blocked_reason": None,
        }
    if not lane.get("loader_exists"):
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "sample_type": "hard_blocker",
            "sample_scope": "",
            "source_used": lane["candidate_source_name"],
            "oxylabs_used": bool(policy_row.get("oxylabs_used")),
            "oxylabs_transport_used": policy_row.get("oxylabs_transport_used", "hard_blocked"),
            "policy_status": lane["policy_status"],
            "records_tested": 0,
            "fields_expected": list(lane["fields"]),
            "fields_found": [],
            "fields_missing": list(lane["fields"]),
            "repo_fields_mapped": list(lane["fields"]),
            "new_fields_recommended": [],
            "validation_status": "hard_blocked",
            "loader_recommendation": lane["next_action"],
            "backfill_recommendation": lane["next_action"],
            "final_actionable_state": final_state or lane_final_state(lane, backfill_written=False, hard_blocked=True),
            "sample_attempted": False,
            "hard_blocker": True,
            "blocked_reason": policy_row.get("exact_blocker_or_allowance") or lane["final_reason"],
        }
    if final_state != "free_open_backfilled":
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "sample_type": "hard_blocker",
            "sample_scope": "",
            "source_used": lane["candidate_source_name"],
            "oxylabs_used": bool(policy_row.get("oxylabs_used")),
            "oxylabs_transport_used": policy_row.get("oxylabs_transport_used", "hard_blocked"),
            "policy_status": lane["policy_status"],
            "records_tested": 0,
            "fields_expected": list(lane["fields"]),
            "fields_found": [],
            "fields_missing": list(lane["fields"]),
            "repo_fields_mapped": list(lane["fields"]),
            "new_fields_recommended": _new_fields_for_lane(lane),
            "validation_status": "hard_blocked",
            "loader_recommendation": "hard_blocked",
            "backfill_recommendation": "hard_blocked",
            "final_actionable_state": "free_open_loader_ready_hard_blocked_from_backfill",
            "sample_attempted": False,
            "hard_blocker": True,
            "blocked_reason": policy_row.get("exact_blocker_or_allowance") or str(policy_row.get("final_state") or "policy_blocked"),
        }
    result = load_combat_lane_records(lane, policy_matrix=policy_matrix, cache=cache)
    records = list(result.get("normalized_records") or [])
    fields_found = sorted({key for row in records[:10] for key in row.keys()})
    missing = [field for field in lane["fields"] if field not in fields_found]
    validation_status = "sample_verified" if result.get("ok") and not missing else "validation_failed"
    return {
        "sport": lane["sport"],
        "lane_name": lane["lane_name"],
        "sample_type": "one_bout_or_entity",
        "sample_scope": "approved_sample_scope",
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
        "loader_recommendation": "loader_ready" if validation_status == "sample_verified" else "validation_failed",
        "backfill_recommendation": lane["next_action"] if validation_status == "sample_verified" else "validation_failed",
        "final_actionable_state": lane_final_state(lane, backfill_written=bool(result.get("ok"))),
        "sample_attempted": True,
        "hard_blocker": False,
        "blocked_reason": result.get("blocked_reason"),
    }


def build_combat_targeted_sample_verification_results(
    *,
    policy_matrix: dict[str, Any] | None = None,
    sample_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_matrix = policy_matrix or build_combat_source_policy_matrix()
    sample_report = sample_report or build_combat_safe_source_sample_report(
        policy_matrix=policy_matrix,
        candidate_rows=combat_candidate_source_catalog(),
    )
    cache: dict[str, Any] = {}
    rows = [_sample_lane(lane, policy_matrix=policy_matrix, sample_report=sample_report, cache=cache) for lane in combat_lane_catalog()]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMBAT_TARGETED_SAMPLE_VERIFICATION_RESULTS",
        "schema_version": "combat_targeted_sample_verification_v1",
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


def write_combat_targeted_sample_verification_results(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMBAT_TARGETED_SAMPLE_VERIFICATION_RESULTS.json"
    md_path = root / "COMBAT_TARGETED_SAMPLE_VERIFICATION_RESULTS.md"
    write_json(json_path, report)
    lines = [
        "# Combat Targeted Sample Verification Results",
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
