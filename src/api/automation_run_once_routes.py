from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from src.api.schemas.automation import AutomationRunOnceRequest


def register_automation_run_once_routes(
    app: FastAPI,
    *,
    automation_scheduler_dep: Any,
    compact_run_once_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation scheduler run-once route.

    Canonical owner: src/api/automation_run_once_routes.py
    """
    automation_scheduler = automation_scheduler_dep
    compact_run_once_response = compact_run_once_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.post("/api/automation/run-once", operation_id="runAutomationSchedulerOnce")
    async def run_automation_scheduler_once(payload: AutomationRunOnceRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="automation scheduler run-once only supports dry_run=true")
        try:
            result = automation_scheduler.run_scheduler_once(
                injected_data=payload.injected_data,
                dry_run=payload.dry_run,
                run_key=payload.run_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        compact = compact_run_once_response(result)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact
