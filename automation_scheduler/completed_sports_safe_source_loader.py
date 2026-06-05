from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scheduler_config import sanitize_filename
from .source_policy_review_common import COMPLETED_SPORTS_DATA_ROOT, current_utc, stable_hash, write_json


def build_completed_sports_policy_backfill_final_state_report(
    *,
    policy_matrix: dict[str, Any],
    sample_report: dict[str, Any],
) -> dict[str, Any]:
    session_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_id = sanitize_filename(f"completed_sports_policy_{session_stamp}_{stable_hash({'sport_group': 'completed'})[:8]}")
    session_root = COMPLETED_SPORTS_DATA_ROOT / "backfill_sessions" / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    sample_index = {row["source_path_hash"]: row for row in sample_report.get("sample_rows") or []}
    rows: list[dict[str, Any]] = []
    for matrix_row in policy_matrix.get("policy_matrix_rows") or []:
        sample_row = sample_index.get(stable_hash(matrix_row.get("source_path") or ""))
        persisted_path = session_root / f"{sanitize_filename(matrix_row['source_id'])}.json"
        payload = {
            "sport": matrix_row["sport"],
            "source_id": matrix_row["source_id"],
            "source_name": matrix_row["source_name"],
            "policy_decision": matrix_row["path_level_decision"],
            "final_state": matrix_row["final_state"],
            "sample_rows": (sample_row or {}).get("sample_rows") or [],
            "normalized_records_added": int((sample_row or {}).get("normalized_records_added", 0) or 0),
            "written_at": current_utc(),
            "raw_payload_included": False,
            "raw_html_persisted": False,
            "secrets_included": False,
        }
        write_json(persisted_path, payload)
        rows.append(
            {
                "sport": matrix_row["sport"],
                "source_id": matrix_row["source_id"],
                "source_name": matrix_row["source_name"],
                "final_state": matrix_row["final_state"],
                "normalized_records_added": int((sample_row or {}).get("normalized_records_added", 0) or 0),
                "metadata_only": matrix_row["final_state"] == "free_open_metadata_only",
                "postmatch_training_only": matrix_row["final_state"] == "free_open_postmatch_training_only",
                "persisted_path": str(persisted_path).replace("\\", "/"),
                "exact_blocker_or_allowance": matrix_row.get("exact_blocker_or_allowance"),
            }
        )
    report = {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_POLICY_BACKFILL_FINAL_STATE_REPORT",
        "schema_version": "completed_sports_policy_backfill_final_state_report_v1",
        "created_at": current_utc(),
        "session_id": session_id,
        "final_state_rows": rows,
        "final_state_row_count": len(rows),
        "normalized_records_added": sum(int(row["normalized_records_added"]) for row in rows if row["final_state"] == "free_open_backfilled"),
        "postmatch_training_records_added": sum(int(row["normalized_records_added"]) for row in rows if row["postmatch_training_only"]),
        "metadata_only_records_added": sum(int(row["normalized_records_added"]) for row in rows if row["metadata_only"]),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
        "paths": {"session_root": str(session_root).replace("\\", "/")},
    }
    write_json(session_root / "latest.json", report)
    return report

