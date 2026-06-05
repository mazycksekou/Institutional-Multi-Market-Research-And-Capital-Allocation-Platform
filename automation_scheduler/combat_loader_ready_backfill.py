from __future__ import annotations

from pathlib import Path
from typing import Any

from .combat_free_data_loader import load_combat_lane_records
from .combat_free_vs_paid_readiness import default_combat_loader_lanes
from .combat_oxylabs_common import current_utc, data_session_root, lane_final_state, write_json, write_md
from .combat_source_policy_review import build_combat_source_policy_matrix


REPORT_ROOT = Path("reports")


def _write_lane_backfill_file(session_root: Path, lane: dict[str, Any], payload: dict[str, Any]) -> str:
    path = session_root / f"{lane['lane_name']}.json"
    write_json(path, payload)
    return str(path).replace("\\", "/")


def build_combat_loader_ready_backfill_report(*, policy_matrix: dict[str, Any] | None = None) -> dict[str, Any]:
    policy_matrix = policy_matrix or build_combat_source_policy_matrix()
    lanes = default_combat_loader_lanes()
    session_id, session_root = data_session_root("combat_loader")
    cache: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    total_records = 0
    for lane in lanes:
        result = load_combat_lane_records(lane, policy_matrix=policy_matrix, cache=cache)
        records = list(result.get("normalized_records") or [])
        backfill_written = bool(result.get("ok") and records)
        persisted_path = _write_lane_backfill_file(
            session_root,
            lane,
            {
                "ok": bool(result.get("ok")),
                "status": result.get("status"),
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "source_name": result.get("source_name") or lane["candidate_source_name"],
                "source_url_hash": lane["source_url_hash"],
                "normalized_records": records,
                "normalized_record_count": len(records),
                "written_at": current_utc(),
                "raw_payload_included": False,
                "raw_html_persisted": False,
                "secrets_included": False,
            },
        )
        total_records += len(records)
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane["field_or_feature_group"],
                "source_name": result.get("source_name") or lane["candidate_source_name"],
                "source_url_hash": lane["source_url_hash"],
                "oxylabs_used": bool(result.get("oxylabs_used")),
                "oxylabs_transport_used": result.get("oxylabs_transport_used"),
                "oxylabs_calls_attempted": int(result.get("oxylabs_calls_attempted", 0) or 0),
                "oxylabs_calls_successful": int(result.get("oxylabs_calls_successful", 0) or 0),
                "oxylabs_calls_failed": int(result.get("oxylabs_calls_failed", 0) or 0),
                "normalized_records_found": len(records),
                "normalized_records_added": len(records),
                "backfill_written": backfill_written,
                "backfill_scope": "approved_sample_scope",
                "final_actionable_state": lane_final_state(lane, backfill_written=backfill_written, hard_blocked=not backfill_written),
                "hard_block_reason": None if backfill_written else str(result.get("blocked_reason") or "hard_blocked_source"),
                "persisted_path": persisted_path,
            }
        )
    report = {
        "ok": True,
        "status": "ok",
        "report_name": "COMBAT_LOADER_READY_BACKFILL_REPORT",
        "schema_version": "combat_loader_ready_backfill_v1",
        "created_at": current_utc(),
        "session_id": session_id,
        "sport": "combat",
        "backfill_rows": rows,
        "backfill_row_count": len(rows),
        "loader_ready_lanes_before": len(lanes),
        "loader_ready_lanes_backfilled": sum(1 for row in rows if row["backfill_written"]),
        "loader_ready_lanes_hard_blocked": sum(1 for row in rows if row["final_actionable_state"] == "free_open_loader_ready_hard_blocked_from_backfill"),
        "loader_ready_lanes_backfill_written": sum(1 for row in rows if row["backfill_written"]),
        "loader_ready_lanes_hard_blocked_from_backfill": sum(1 for row in rows if row["final_actionable_state"] == "free_open_loader_ready_hard_blocked_from_backfill"),
        "records_added_by_combat": total_records,
        "backfill_records_written_total": total_records,
        "fields_closed_this_pass": total_records,
        "fields_partially_closed_this_pass": 0,
        "fields_reclassified_this_pass": 0,
        "oxylabs_residential_proxy_used": any(row["oxylabs_transport_used"] == "residential_proxy" for row in rows),
        "oxylabs_web_scraper_api_used": any(row["oxylabs_transport_used"] == "web_scraper_api" for row in rows),
        "oxylabs_total_calls_attempted": sum(int(row["oxylabs_calls_attempted"]) for row in rows),
        "oxylabs_total_calls_successful": sum(int(row["oxylabs_calls_successful"]) for row in rows),
        "oxylabs_total_calls_failed": sum(int(row["oxylabs_calls_failed"]) for row in rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
        "paths": {"session_root": str(session_root).replace("\\", "/"), "latest_json_path": str(session_root / "latest.json").replace("\\", "/")},
    }
    write_json(session_root / "latest.json", report)
    return report


def write_combat_loader_ready_backfill_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMBAT_LOADER_READY_BACKFILL_REPORT.json"
    md_path = root / "COMBAT_LOADER_READY_BACKFILL_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Combat Loader Ready Backfill Report",
        "",
        f"1. loader_ready_lanes_before: {report.get('loader_ready_lanes_before')}",
        f"2. loader_ready_lanes_backfilled: {report.get('loader_ready_lanes_backfilled')}",
        f"3. loader_ready_lanes_hard_blocked: {report.get('loader_ready_lanes_hard_blocked')}",
        f"4. records_added_by_combat: {report.get('records_added_by_combat')}",
        f"5. oxylabs_total_calls_attempted: {report.get('oxylabs_total_calls_attempted')}",
        "",
        "## Lanes",
    ]
    for row in report.get("backfill_rows") or []:
        lines.append(
            f"- {row.get('lane_name')} backfill={row.get('backfill_written')} records_added={row.get('normalized_records_added')} hard_block={row.get('hard_block_reason')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
