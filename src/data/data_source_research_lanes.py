from __future__ import annotations

from typing import Any


TASK_REQUIREMENTS = [
    "Find a source compatible with current access policy or classify as future candidate",
    "Document access requirements",
    "Document whether account/API key is required",
    "Document whether budget approval is required",
    "Document whether execution account is required",
    "Document license/terms",
    "Document rate limits",
    "Document update cadence",
    "Document stable join keys",
    "Document sample schema",
    "Map available fields to model inputs",
    "Map final outcome fields",
    "Map historical backfill fields",
]

TASK_ACCEPTANCE_CRITERIA = [
    "source name and URL documented",
    "source_access_type classified",
    "approval_status recommended",
    "terms reviewed or marked needs_terms_review",
    "sample response/schema captured without raw secrets",
    "model input mapping completed",
    "outcome mapping completed",
    "adapter feasibility rated",
]


def _task_priority(lane: dict[str, Any]) -> str:
    if lane.get("module_priority") == "highest":
        return "highest"
    if lane.get("module_priority") == "high":
        return "high"
    status = str(lane.get("lane_status") or "")
    if status in {"needs_external_research", "future_vendor_needed"}:
        return "high"
    if int(lane.get("terms_risk_score") or 0) >= 70:
        return "medium"
    return "low"


def _needs_task(lane: dict[str, Any]) -> bool:
    if lane.get("lane_status") in {"needs_external_research", "candidate_sources_available", "future_vendor_needed", "blocked_pending_source"}:
        return True
    for source in list(lane.get("source_candidates") or []) + list(lane.get("future_source_candidates") or []):
        if source.get("requires_terms_review") or source.get("approval_status") in {"needs_terms_review", "needs_review", "candidate", "future_candidate"}:
            return True
    return False


def build_research_task(lane: dict[str, Any]) -> dict[str, Any]:
    lane_id = str(lane.get("lane_id") or lane.get("module") or "unknown")
    return {
        "research_task_id": f"find_source_for_{lane_id}",
        "lane_id": lane_id,
        "module": lane.get("module", lane_id),
        "status": "open",
        "priority": _task_priority(lane),
        "developer_assignment": None,
        "requirements": list(TASK_REQUIREMENTS),
        "acceptance_criteria": list(TASK_ACCEPTANCE_CRITERIA),
        "adapter_status": lane.get("adapter_status", "blocked_pending_source"),
        "required_data": {
            "required_model_inputs": list(lane.get("required_model_inputs") or []),
            "outcome_fields_required": list(lane.get("outcome_fields_required") or []),
            "historical_backfill_fields_required": list(lane.get("historical_backfill_fields_required") or []),
            "live_fields_desired": list(lane.get("live_fields_desired") or []),
            "context_fields_desired": list(lane.get("context_fields_desired") or []),
        },
    }


def build_research_tasks(lanes: list[dict[str, Any]]) -> dict[str, Any]:
    tasks = [build_research_task(lane) for lane in lanes if _needs_task(lane)]
    priority_counts: dict[str, int] = {}
    for task in tasks:
        priority = str(task.get("priority") or "low")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    return {
        "ok": True,
        "status": "ok",
        "total_tasks": len(tasks),
        "open_tasks": len([task for task in tasks if task.get("status") == "open"]),
        "priority_counts": priority_counts,
        "tasks": tasks,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
    }
