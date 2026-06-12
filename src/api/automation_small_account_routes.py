from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from src.api.schemas.automation import (
    AutomationPatternDetectRequest,
    AutomationSmallAccountReviewRequest,
)


def register_automation_small_account_routes(
    app: FastAPI,
    *,
    automation_scheduler_dep: Any,
    compact_balance_sheet_risk_response_dep: Any,
    compact_broker_quality_response_dep: Any,
    compact_micro_outcome_calibration_response_dep: Any,
    compact_pattern_calibration_response_dep: Any,
    compact_pattern_detection_response_dep: Any,
    compact_pattern_review_queue_response_dep: Any,
    compact_small_account_review_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation small-account pattern and risk routes.

    Canonical owner: src/api/automation_small_account_routes.py
    """
    automation_scheduler = automation_scheduler_dep
    compact_balance_sheet_risk_response = compact_balance_sheet_risk_response_dep
    compact_broker_quality_response = compact_broker_quality_response_dep
    compact_micro_outcome_calibration_response = compact_micro_outcome_calibration_response_dep
    compact_pattern_calibration_response = compact_pattern_calibration_response_dep
    compact_pattern_detection_response = compact_pattern_detection_response_dep
    compact_pattern_review_queue_response = compact_pattern_review_queue_response_dep
    compact_small_account_review_response = compact_small_account_review_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.post("/api/automation/pattern-detect", operation_id="detectSmallAccountPatterns")
    async def detect_small_account_patterns_endpoint(payload: AutomationPatternDetectRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="pattern detection only supports dry_run=true")
        result = automation_scheduler.run_small_account_pattern_detection(payload.items)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_pattern_detection_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

    @app.post("/api/automation/small-account-review", operation_id="runSmallAccountReview")
    async def run_small_account_review_endpoint(payload: AutomationSmallAccountReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="small-account review only supports dry_run=true")
        result = automation_scheduler.run_small_account_review_cycle(
            payload.items,
            session_state=payload.session_state,
            persist_queue=payload.persist_queue,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_small_account_review_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/pattern-review-queue", operation_id="getSmallAccountPatternReviewQueue")
    async def get_small_account_pattern_review_queue_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        payload = automation_scheduler.get_small_account_pattern_review_queue(limit=cap)
        compact = compact_pattern_review_queue_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/pattern-calibration", operation_id="getSmallAccountPatternCalibration")
    async def get_small_account_pattern_calibration_endpoint(limit: int = Query(default=10)):
        cap = min(max(int(limit), 1), 100)
        payload = automation_scheduler.get_small_account_pattern_calibration()
        return compact_pattern_calibration_response(payload, limit=cap)

    @app.get("/api/automation/micro-outcome-calibration", operation_id="getSmallAccountMicroOutcomeCalibration")
    async def get_small_account_micro_outcome_calibration_endpoint(limit: int = Query(default=10)):
        cap = min(max(int(limit), 1), 100)
        payload = automation_scheduler.get_small_account_micro_outcome_calibration()
        return compact_micro_outcome_calibration_response(payload, limit=cap)

    @app.get("/api/automation/broker-quality", operation_id="getSmallAccountBrokerQuality")
    async def get_small_account_broker_quality_endpoint(limit: int = Query(default=10)):
        cap = min(max(int(limit), 1), 100)
        payload = automation_scheduler.get_broker_quality()
        return compact_broker_quality_response(payload, limit=cap)

    @app.get("/api/automation/balance-sheet-risk/{symbol}", operation_id="getSmallAccountBalanceSheetRisk")
    async def get_small_account_balance_sheet_risk_endpoint(symbol: str):
        payload = automation_scheduler.get_balance_sheet_risk(symbol)
        return compact_balance_sheet_risk_response(payload)
