from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, Query

from src.api.schemas.automation import (
    DataSourceVerifyRequest,
    NcaafCfbdVerifyRequest,
)


def register_automation_data_source_routes(
    app: FastAPI,
    *,
    dashboard_facade_dep: Any,
    compact_cfbd_adapter_verification_response_dep: Any,
    compact_data_availability_tiers_response_dep: Any,
    compact_data_source_coverage_response_dep: Any,
    compact_data_source_env_vars_response_dep: Any,
    compact_data_source_health_response_dep: Any,
    compact_data_source_priorities_response_dep: Any,
    compact_data_source_registry_response_dep: Any,
    compact_data_source_research_lanes_response_dep: Any,
    compact_public_apis_expansion_report_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation data-source registry and verification routes.

    Canonical owner: src/api/automation_data_source_routes.py
    """
    dashboard_facade = dashboard_facade_dep
    compact_cfbd_adapter_verification_response = compact_cfbd_adapter_verification_response_dep
    compact_data_availability_tiers_response = compact_data_availability_tiers_response_dep
    compact_data_source_coverage_response = compact_data_source_coverage_response_dep
    compact_data_source_env_vars_response = compact_data_source_env_vars_response_dep
    compact_data_source_health_response = compact_data_source_health_response_dep
    compact_data_source_priorities_response = compact_data_source_priorities_response_dep
    compact_data_source_registry_response = compact_data_source_registry_response_dep
    compact_data_source_research_lanes_response = compact_data_source_research_lanes_response_dep
    compact_public_apis_expansion_report_response = compact_public_apis_expansion_report_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/automation/data-sources/registry", operation_id="getAutomationDataSourceRegistry")
    async def get_data_source_registry_endpoint(
        module: Optional[str] = Query(default=None),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=100),
    ):
        payload = dashboard_facade.get_data_source_registry_snapshot(module=module)
        cap = min(max(int(limit), 1), 100)
        compact = compact_data_source_registry_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/data-sources/coverage", operation_id="getAutomationDataSourceCoverage")
    async def get_data_source_coverage_endpoint(
        module: Optional[str] = Query(default=None),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=100),
    ):
        payload = dashboard_facade.get_data_source_coverage_snapshot(module=module)
        cap = min(max(int(limit), 1), 100)
        compact = compact_data_source_coverage_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/data-sources/research-lanes", operation_id="getAutomationDataSourceResearchLanes")
    async def get_data_source_research_lanes_endpoint(
        module: Optional[str] = Query(default=None),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=100),
    ):
        payload = dashboard_facade.get_data_source_research_lanes_snapshot(module=module)
        cap = min(max(int(limit), 1), 100)
        compact = compact_data_source_research_lanes_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/data-sources/env-vars", operation_id="getAutomationDataSourceEnvVars")
    async def get_data_source_env_vars_endpoint(
        module: Optional[str] = Query(default=None),
        limit: int = Query(default=500),
    ):
        payload = dashboard_facade.get_data_source_env_var_registry(module=module)
        cap = min(max(int(limit), 1), 500)
        return compact_data_source_env_vars_response(payload, limit=cap)

    @app.get("/api/automation/data-sources/priorities", operation_id="getAutomationDataSourcePriorities")
    async def get_data_source_priorities_endpoint(
        module: Optional[str] = Query(default=None),
        limit: int = Query(default=50),
    ):
        cap = min(max(int(limit), 1), 100)
        payload = dashboard_facade.get_data_source_priorities_snapshot(module=module, limit=cap)
        return compact_data_source_priorities_response(payload, limit=cap)

    @app.get("/api/automation/data-sources/public-apis-expansion-report", operation_id="getPublicApisExpansionReport")
    async def get_public_apis_expansion_report_endpoint(
        module: Optional[str] = Query(default=None),
        persist_report: bool = Query(default=False),
        limit: int = Query(default=100),
    ):
        cap = min(max(int(limit), 1), 100)
        payload = dashboard_facade.get_public_apis_expansion_report(module=module, persist_report=persist_report)
        return compact_public_apis_expansion_report_response(payload, limit=cap)

    @app.get("/api/automation/data-sources/data-availability/tiers", operation_id="getAutomationDataAvailabilityTiers")
    async def get_data_availability_tiers_endpoint(
        module: Optional[str] = Query(default=None),
        persist_report: bool = Query(default=False),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=100),
    ):
        cap = min(max(int(limit), 1), 100)
        payload = dashboard_facade.get_data_availability_tiers_report(module=module, persist_report=persist_report)
        compact = compact_data_availability_tiers_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    @app.get("/api/automation/data-sources/health", operation_id="getAutomationDataSourceHealth")
    async def get_data_source_health_endpoint():
        payload = dashboard_facade.get_data_source_registry_health()
        return compact_data_source_health_response(payload)

    @app.post(
        "/api/automation/data-sources/adapters/ncaaf/cfbd/verify",
        operation_id="verifyNcaafCfbdAdapter",
    )
    async def verify_ncaaf_cfbd_adapter_endpoint(
        payload: NcaafCfbdVerifyRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        result = dashboard_facade.verify_ncaaf_cfbd_adapter(
            dry_run=payload.dry_run,
            season=payload.season,
            week=payload.week,
            max_records=payload.max_records,
            fetch_live_sample=payload.fetch_live_sample,
            sample_profile=payload.sample_profile,
            max_provider_calls=payload.max_provider_calls,
            include_games=payload.include_games,
            include_team_stats=payload.include_team_stats,
            include_advanced_stats=payload.include_advanced_stats,
            include_rankings=payload.include_rankings,
            include_lines=payload.include_lines,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_cfbd_adapter_verification_response(result)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

    @app.post("/api/automation/data-sources/verify", operation_id="verifyAutomationDataSourceRegistry")
    async def verify_data_source_registry_endpoint(payload: DataSourceVerifyRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=100)):
        result = dashboard_facade.verify_data_source_registry(module=payload.module, persist_report=payload.persist_report)
        cap = min(max(int(limit), 1), 100)
        compact = compact_data_source_registry_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact

