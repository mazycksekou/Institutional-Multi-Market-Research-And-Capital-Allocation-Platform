from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, File, Form, HTTPException, Header, Path, Query, Request, Response, UploadFile

from src.api.schemas.automation import (
    AutomationDeepSeekRedTeamRequest,
    AutomationDeepSeekReviewRequest,
)

def register_automation_deepseek_routes(
    app: Any,
    *,
    automation_scheduler_dep: Any,
    compact_deepseek_review_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation DeepSeek review/report routes.

    Canonical owner: src/api/automation_deepseek_routes.py
    """
    automation_scheduler = automation_scheduler_dep
    compact_deepseek_review_response = compact_deepseek_review_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.post("/api/automation/deepseek-review", operation_id="reviewAutomationWithDeepSeek")
    async def automation_deepseek_review_endpoint(payload: AutomationDeepSeekReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.run_automation_deepseek_review(
            collector_cycle_report=payload.collector_cycle_report,
            daily_report=payload.daily_report,
            calibration_report=payload.calibration_report,
            sampled_contracts=payload.sampled_contracts,
            candidate=payload.candidate or None,
            candidates=payload.candidates or None,
            core_model_action=payload.core_model_action,
            enabled=payload.enabled,
            review_queue_summary=payload.review_queue_summary,
            outcome_summary=payload.outcome_summary,
            provider_health_summary=payload.provider_health_summary,
            manifold_cluster_summary=payload.manifold_cluster_summary,
            markov_hmm_summary=payload.markov_hmm_summary,
            sportsbook_full_board_summary=payload.sportsbook_full_board_summary,
            stock_crypto_pattern_summary=payload.stock_crypto_pattern_summary,
            kalshi_prediction_market_summary=payload.kalshi_prediction_market_summary,
            small_account_summary=payload.small_account_summary,
            security_readiness_summary=payload.security_readiness_summary,
            strategy_readiness_summary=payload.strategy_readiness_summary,
            trap_no_bet_summary=payload.trap_no_bet_summary,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_deepseek_review_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/automation/deepseek-red-team", operation_id="redTeamAutomationWithDeepSeek")
    async def automation_deepseek_red_team_endpoint(payload: AutomationDeepSeekRedTeamRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.run_automation_deepseek_red_team(
            candidate=payload.candidate or None,
            candidates=payload.candidates or None,
            enabled=payload.enabled,
            review_queue_summary=payload.review_queue_summary,
            calibration_summary=payload.calibration_summary,
            outcome_summary=payload.outcome_summary,
            provider_health_summary=payload.provider_health_summary,
            manifold_cluster_summary=payload.manifold_cluster_summary,
            markov_hmm_summary=payload.markov_hmm_summary,
            sportsbook_full_board_summary=payload.sportsbook_full_board_summary,
            stock_crypto_pattern_summary=payload.stock_crypto_pattern_summary,
            kalshi_prediction_market_summary=payload.kalshi_prediction_market_summary,
            small_account_summary=payload.small_account_summary,
            security_readiness_summary=payload.security_readiness_summary,
            strategy_readiness_summary=payload.strategy_readiness_summary,
            trap_no_bet_summary=payload.trap_no_bet_summary,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_deepseek_review_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/deepseek-disagreements", operation_id="getDeepSeekDisagreements")
    async def automation_deepseek_disagreements_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=100)):
        cap = min(max(int(limit), 1), 500 if verbose else 100)
        result = automation_scheduler.get_deepseek_disagreements(limit=cap)
        compact = compact_deepseek_review_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/deepseek-daily-report", operation_id="getDeepSeekDailyReport")
    async def automation_deepseek_daily_report_endpoint(report_date: Optional[str] = Query(default=None), enabled: Optional[bool] = Query(default=None), persist_report: bool = Query(default=True), verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.get_deepseek_daily_report(
            report_date=report_date,
            enabled=enabled,
            persist_report=persist_report,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_deepseek_review_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact
