from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query

from src.api.schemas.automation import (
    InstitutionalDeepSeekReviewRequest,
    InstitutionalExecutionSimulationRequest,
    InstitutionalLabRunRequest,
)


def register_automation_institutional_lab_routes(
    app: FastAPI,
    *,
    automation_scheduler_dep: Any,
    compact_deepseek_review_response_dep: Any,
    compact_institutional_execution_response_dep: Any,
    compact_institutional_lab_health_response_dep: Any,
    compact_institutional_lab_run_response_dep: Any,
    compact_institutional_report_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation institutional-lab routes.

    Canonical owner: src/api/automation_institutional_lab_routes.py
    """
    automation_scheduler = automation_scheduler_dep
    compact_deepseek_review_response = compact_deepseek_review_response_dep
    compact_institutional_execution_response = compact_institutional_execution_response_dep
    compact_institutional_lab_health_response = compact_institutional_lab_health_response_dep
    compact_institutional_lab_run_response = compact_institutional_lab_run_response_dep
    compact_institutional_report_response = compact_institutional_report_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/automation/institutional-lab/health", operation_id="getInstitutionalLabHealth")
    async def get_institutional_lab_health_endpoint():
        payload = automation_scheduler.get_institutional_lab_health()
        return compact_institutional_lab_health_response(payload)

    @app.post("/api/automation/institutional-lab/run", operation_id="runInstitutionalLab")
    async def run_institutional_lab_endpoint(payload: InstitutionalLabRunRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="institutional lab only supports dry_run=true")
        if payload.read_existing_outputs_only is not True:
            raise HTTPException(status_code=400, detail="institutional lab only supports read_existing_outputs_only=true")
        result = automation_scheduler.run_institutional_lab(
            dry_run=payload.dry_run,
            asset_classes=payload.asset_classes,
            read_existing_outputs_only=payload.read_existing_outputs_only,
            persist_lab_report=payload.persist_lab_report,
            persist_outcomes=payload.persist_outcomes,
            deepseek_review=payload.deepseek_review,
            execution_simulation=payload.execution_simulation,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_institutional_lab_run_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/institutional-lab/report", operation_id="getInstitutionalLabReport")
    async def get_institutional_lab_report_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_institutional_lab_report()
        compact = compact_institutional_report_response(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/institutional-lab/daily-report", operation_id="getInstitutionalLabDailyReport")
    async def get_institutional_lab_daily_report_endpoint(report_date: Optional[str] = Query(default=None), verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_institutional_lab_daily_report(report_date=report_date)
        compact = compact_institutional_report_response(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.post("/api/automation/institutional-lab/deepseek-review", operation_id="reviewInstitutionalLabWithDeepSeek")
    async def institutional_lab_deepseek_review_endpoint(payload: InstitutionalDeepSeekReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.run_institutional_deepseek_review(report=payload.report, enabled=payload.enabled)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_deepseek_review_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

    @app.post("/api/automation/institutional-lab/execution-desk/simulate", operation_id="simulateInstitutionalExecutionDesk")
    async def institutional_execution_desk_simulate_endpoint(payload: InstitutionalExecutionSimulationRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        request_payload = payload.model_dump()
        try:
            result = automation_scheduler.simulate_institutional_execution(request_payload)
        except ValueError as exc:
            from automation_scheduler.institutional_execution_desk import rejection_response

            result = rejection_response(str(exc))
            raise HTTPException(status_code=400, detail=compact_institutional_execution_response(result)) from exc
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_institutional_execution_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/institutional-lab/audit", operation_id="getInstitutionalLabAudit")
    async def get_institutional_lab_audit_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = automation_scheduler.get_institutional_lab_audit(limit=cap)
        compact = {
            "ok": bool(payload.get("ok", True)),
            "status": payload.get("status", "ok"),
            "total_count": int(payload.get("total_count", 0)),
            "count": int(payload.get("count", 0)),
            "items": list(payload.get("items", []))[:cap],
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "raw_payload_included": False,
        }
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact
