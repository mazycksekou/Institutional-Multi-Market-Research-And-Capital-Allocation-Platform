from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, File, Form, HTTPException, Header, Path, Query, Request, Response, UploadFile

from src.api.automation_security import validate_cron_token

from src.api.schemas.automation import (
    AutomationCalibrationCollectorRunRequest,
    AutomationCalibrationCollectorScheduledRunRequest,
    AutomationOutcomeIngestRequest,
    AutomationOutcomeLocalSettlementImportRequest,
    AutomationSettlementDiscoveryRequest,
)

def register_automation_review_outcomes_routes(
    app: Any,
    *,
    automation_scheduler_dep: Any,
    compact_calibration_collector_response_dep: Any,
    compact_calibration_response_dep: Any,
    compact_outcome_import_response_dep: Any,
    compact_outcome_ingest_response_dep: Any,
    compact_outcomes_response_dep: Any,
    compact_review_queue_response_dep: Any,
    compact_settlement_discovery_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation review queue, outcomes, and calibration collector routes.

    Canonical owner: src/api/automation_review_outcomes_routes.py
    """
    automation_scheduler = automation_scheduler_dep
    compact_calibration_collector_response = compact_calibration_collector_response_dep
    compact_calibration_response = compact_calibration_response_dep
    compact_outcome_import_response = compact_outcome_import_response_dep
    compact_outcome_ingest_response = compact_outcome_ingest_response_dep
    compact_outcomes_response = compact_outcomes_response_dep
    compact_review_queue_response = compact_review_queue_response_dep
    compact_settlement_discovery_response = compact_settlement_discovery_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/automation/review-queue", operation_id="getAutomationSchedulerReviewQueue")
    async def get_automation_scheduler_review_queue(
        provider: str = Query(default="all"),
        market_type: str = Query(default="all"),
        reason: Optional[str] = Query(default=None),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        queue = automation_scheduler.get_scheduler_review_queue(
            provider=provider,
            market_type=market_type,
            reason=reason,
            limit=min(max(int(limit), 1), 100 if verbose else 10),
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_review_queue_response(queue, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(queue, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/calibration", operation_id="getAutomationCalibration")
    async def get_automation_calibration_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_automation_calibration_report()
        compact = compact_calibration_response(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/outcomes/ingest", operation_id="ingestAutomationOutcomes")
    async def ingest_automation_outcomes_endpoint(payload: AutomationOutcomeIngestRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.ingest_automation_outcomes(
            payload.records,
            source=payload.source,
            dry_run=payload.dry_run,
            persist=payload.persist,
        )
        compact = compact_outcome_ingest_response(result)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/outcomes/import-local-settlements", operation_id="importLocalKalshiSettlements")
    async def import_local_kalshi_settlements_endpoint(
        payload: AutomationOutcomeLocalSettlementImportRequest,
        x_collector_token: Optional[str] = Header(default=None, alias="X-Collector-Token"),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.persist and not payload.dry_run:
            from automation_scheduler.collector_scheduled_runner import validate_cron_token

            ok, status_code, rejection = validate_cron_token(x_collector_token)
            if not ok:
                raise HTTPException(status_code=status_code, detail=compact_outcome_import_response(rejection or {}))
        result = automation_scheduler.import_local_settlement_outcomes(
            payload.records,
            supporting_paper_decisions=payload.supporting_paper_decisions,
            source=payload.source,
            migration_version=payload.migration_version,
            dry_run=payload.dry_run,
            persist=payload.persist,
        )
        compact = compact_outcome_import_response(result)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/outcomes", operation_id="getAutomationOutcomes")
    async def get_automation_outcomes_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = automation_scheduler.get_automation_outcomes(limit=cap)
        compact = compact_outcomes_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/outcomes/discover-settlements", operation_id="discoverAutomationOutcomeSettlements")
    async def discover_automation_outcome_settlements_endpoint(payload: AutomationSettlementDiscoveryRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="settlement discovery only supports dry_run=true")
        result = automation_scheduler.discover_automation_outcome_completions(
            pending_rows=payload.pending_rows or None,
            imported_rows=payload.imported_rows or None,
            use_kalshi_snapshot=payload.use_kalshi_snapshot,
            write_local_report=payload.write_local_report,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_settlement_discovery_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/calibration-collector/run", operation_id="runAutomationCalibrationCollector")
    async def run_automation_calibration_collector_endpoint(payload: AutomationCalibrationCollectorRunRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.run_automation_calibration_collector(
            dry_run=payload.dry_run,
            persist_outcomes=payload.persist_outcomes,
            max_new_contracts=payload.max_new_contracts,
            target_daily_new_contracts=payload.target_daily_new_contracts,
            hard_cap_daily_new_contracts=payload.hard_cap_daily_new_contracts,
            max_markets_scanned=payload.max_markets_scanned,
            include_short_term=payload.include_short_term,
            include_medium_term=payload.include_medium_term,
            include_long_term=payload.include_long_term,
            adaptive_throttle=payload.adaptive_throttle,
            deepseek_review=payload.deepseek_review,
        )
        if not bool(result.get("ok", True)) and result.get("status") == "invalid_request":
            raise HTTPException(status_code=400, detail=compact_calibration_collector_response(result, limit=limit))
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_calibration_collector_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/calibration-collector/scheduled-run", operation_id="runScheduledAutomationCalibrationCollector")
    async def run_automation_calibration_collector_scheduled_endpoint(
        payload: AutomationCalibrationCollectorScheduledRunRequest,
        x_collector_token: Optional[str] = Header(default=None, alias="X-Collector-Token"),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        from automation_scheduler.collector_scheduled_runner import validate_cron_token

        ok, status_code, rejection = validate_cron_token(x_collector_token)
        if not ok:
            raise HTTPException(status_code=status_code, detail=compact_calibration_collector_response(rejection or {}, limit=limit))
        request_payload = payload.model_dump()
        result = automation_scheduler.run_automation_calibration_collector_scheduled(request_payload)
        if not bool(result.get("ok", True)) and result.get("status") == "invalid_request":
            raise HTTPException(status_code=400, detail=compact_calibration_collector_response(result, limit=limit))
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_calibration_collector_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact
