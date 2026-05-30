from __future__ import annotations

from typing import Any


def _missing_inputs(lane: dict[str, Any]) -> list[str]:
    required = set(lane.get("required_model_inputs") or [])
    supported: set[str] = set()
    for source in list(lane.get("verified_sources") or []) + list(lane.get("source_candidates") or []):
        supported.update((source.get("model_mapping") or {}).get("model_inputs_supported") or [])
    return sorted(required - supported)


def build_module_coverage(lane: dict[str, Any], research_tasks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    lane_id = str(lane.get("lane_id") or lane.get("module") or "unknown")
    tasks = [task for task in (research_tasks or []) if task.get("lane_id") == lane_id]
    missing = _missing_inputs(lane)
    return {
        "module": lane.get("module", lane_id),
        "lane_id": lane_id,
        "lane_status": lane.get("lane_status", "needs_external_research"),
        "required_inputs": list(lane.get("required_model_inputs") or []),
        "optional_inputs": list(lane.get("optional_model_inputs") or []),
        "outcome_fields": list(lane.get("outcome_fields_required") or []),
        "historical_backfill_fields": list(lane.get("historical_backfill_fields_required") or []),
        "live_update_fields": list(lane.get("live_fields_desired") or []),
        "context_fields": list(lane.get("context_fields_desired") or []),
        "verified_sources": [source.get("source_id") for source in lane.get("verified_sources") or []],
        "candidate_sources": [source.get("source_id") for source in lane.get("source_candidates") or []],
        "future_source_candidates": [source.get("source_id") for source in lane.get("future_source_candidates") or []],
        "missing_inputs": missing,
        "external_research_tasks": [task.get("research_task_id") for task in tasks],
        "coverage_score": int(lane.get("coverage_score") or 0),
        "adapter_plan": lane.get("adapter_status", "blocked_pending_source"),
    }


def build_coverage_report(*, registry: dict[str, Any]) -> dict[str, Any]:
    from .data_source_research_lanes import build_research_tasks

    lanes = list(registry.get("lanes") or [])
    research = build_research_tasks(lanes)
    tasks = list(research.get("tasks") or [])
    modules = [build_module_coverage(lane, tasks) for lane in lanes]
    return {
        "ok": True,
        "status": "ok",
        "total_modules": len(modules),
        "modules_fully_covered": [row["module"] for row in modules if not row["missing_inputs"] and row["verified_sources"]],
        "modules_partially_covered": [row["module"] for row in modules if row["candidate_sources"] and not row["verified_sources"]],
        "modules_without_verified_source": [row["module"] for row in modules if not row["verified_sources"]],
        "modules": modules,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
    }
