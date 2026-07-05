from __future__ import annotations

from typing import Any

from fastapi import Query


def register_automation_core_routes(
    app: Any,
    *,
    dashboard_facade_dep: Any,
    compact_health_response_dep: Any,
    compact_intelligence_readiness_response_dep: Any,
    compact_strategy_readiness_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register core automation health and readiness routes.

    Canonical owner: src/api/automation_core_routes.py
    """
    dashboard_facade = dashboard_facade_dep
    compact_health_response = compact_health_response_dep
    compact_intelligence_readiness_response = compact_intelligence_readiness_response_dep
    compact_strategy_readiness_response = compact_strategy_readiness_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/automation/health", operation_id="getAutomationSchedulerHealth")
    async def get_automation_scheduler_health():
        health = dashboard_facade.get_scheduler_health()
        return compact_health_response(health)

    @app.get("/api/automation/security-readiness", operation_id="getAutomationSecurityReadiness")
    async def get_automation_security_readiness_endpoint():
        return dashboard_facade.get_security_readiness()

    @app.get("/api/automation/intelligence-readiness", operation_id="getAutomationIntelligenceReadiness")
    async def get_automation_intelligence_readiness_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = dashboard_facade.get_intelligence_readiness()
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_intelligence_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/strategy-readiness", operation_id="getAutomationStrategyReadiness")
    async def get_automation_strategy_readiness_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=50)):
        cap = min(max(int(limit), 1), 100 if verbose else 50)
        payload = dashboard_facade.get_strategy_readiness()
        compact = compact_strategy_readiness_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

