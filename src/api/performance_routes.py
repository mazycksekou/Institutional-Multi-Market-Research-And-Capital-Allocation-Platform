from typing import Any, Optional

from fastapi import Body, Depends, HTTPException, Query
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from src.api.schemas.performance import PerformanceBacktestRequest


def register_performance_routes(
    app: Any,
    *,
    API_BASE_URL_dep: Any,
    dashboard_facade_dep: Any,
    compact_performance_health_dep: Any,
    compact_performance_report_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register performance routes.

    Canonical owner: src/api/performance_routes.py
    """
    API_BASE_URL = API_BASE_URL_dep
    dashboard_facade = dashboard_facade_dep
    compact_performance_health = compact_performance_health_dep
    compact_performance_report = compact_performance_report_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/performance/health", operation_id="getPerformanceHealth")
    async def get_performance_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = {"ok": True, **dashboard_facade.get_performance_health()}
        compact = compact_performance_health(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/performance/report", operation_id="getPerformanceReport")
    async def get_performance_report_endpoint(
        model_id: str = Query(default="default_model"),
        historical_rows_path: Optional[str] = Query(default=None),
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        compact_payload = dashboard_facade.get_performance_report(
            model_id=model_id,
            historical_rows_path=historical_rows_path,
        )
        compact = compact_performance_report(compact_payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(compact_payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/performance/backtest", operation_id="runPerformanceBacktest")
    async def run_performance_backtest_endpoint(
        payload: PerformanceBacktestRequest,
        verbose: bool = Query(default=False),
        include_debug: bool = Query(default=False),
        limit: int = Query(default=10),
    ):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="performance backtest only supports dry_run=true")
        result = dashboard_facade.run_performance_backtest(
            model_id=payload.model_id,
            historical_rows_path=payload.historical_rows_path,
            rows=payload.rows,
        )
        compact = compact_performance_report(result["compact_report"])
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/performance/paper-summary", operation_id="runPerformancePaperSummary")
    async def run_performance_paper_summary_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = dashboard_facade.get_paper_summary()
        compact = compact_performance_health({"ok": True, **dashboard_facade.get_performance_health()})
        compact["status"] = payload.get("status", "paper_tracking")
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact

    PUBLIC_OPENAPI_PATH_METHODS = frozenset({
        ("/", "get"),
        ("/health", "get"),
        ("/ping", "get"),
        ("/api/debug/auth-status", "get"),
        ("/api/automation/health", "get"),
        ("/api/automation/security-readiness", "get"),
        ("/api/automation/intelligence-readiness", "get"),
        ("/api/automation/strategy-readiness", "get"),
        ("/api/automation/basketball-player-impact-readiness", "get"),
        ("/api/automation/basketball-player-impact", "post"),
        ("/api/automation/football-impact-readiness", "get"),
        ("/api/automation/football-impact-diagnostics", "post"),
        ("/api/automation/soccer-impact-readiness", "get"),
        ("/api/automation/soccer-impact-diagnostics", "post"),
        ("/api/automation/hockey-impact-readiness", "get"),
        ("/api/automation/hockey-impact-diagnostics", "post"),
        ("/api/automation/baseball-impact-readiness", "get"),
        ("/api/automation/baseball-impact-diagnostics", "post"),
        ("/api/automation/golf-impact-readiness", "get"),
        ("/api/automation/golf-impact-diagnostics", "post"),
        ("/api/automation/combat-impact-readiness", "get"),
        ("/api/automation/combat-impact-diagnostics", "post"),
        ("/api/automation/tennis-impact-readiness", "get"),
        ("/api/automation/tennis-impact-diagnostics", "post"),
        ("/api/automation/advanced-red-team-report", "get"),
        ("/api/automation/extreme-randomness-report", "get"),
        ("/api/automation/extreme-signal-diagnostics", "post"),
        ("/api/automation/advanced-shape-diagnostics", "post"),
        ("/api/automation/review-queue", "get"),
        ("/api/automation/calibration", "get"),
        ("/api/automation/outcomes", "get"),
        ("/api/automation/outcomes/ingest", "post"),
        ("/api/automation/outcomes/import-local-settlements", "post"),
        ("/api/automation/outcomes/discover-settlements", "post"),
        ("/api/automation/calibration-collector/run", "post"),
        ("/api/automation/calibration-collector/scheduled-run", "post"),
        ("/api/automation/deepseek-review", "post"),
        ("/api/automation/deepseek-red-team", "post"),
        ("/api/automation/deepseek-disagreements", "get"),
        ("/api/automation/deepseek-daily-report", "get"),
        ("/api/automation/data-sources/registry", "get"),
        ("/api/automation/data-sources/coverage", "get"),
        ("/api/automation/data-sources/research-lanes", "get"),
        ("/api/automation/data-sources/env-vars", "get"),
        ("/api/automation/data-sources/priorities", "get"),
        ("/api/automation/data-sources/public-apis-expansion-report", "get"),
        ("/api/automation/data-sources/data-availability/tiers", "get"),
        ("/api/automation/data-sources/health", "get"),
        ("/api/automation/data-sources/adapters/ncaaf/cfbd/verify", "post"),
        ("/api/automation/data-sources/verify", "post"),
        ("/api/automation/institutional-lab/health", "get"),
        ("/api/automation/institutional-lab/run", "post"),
        ("/api/automation/institutional-lab/report", "get"),
        ("/api/automation/institutional-lab/daily-report", "get"),
        ("/api/automation/institutional-lab/deepseek-review", "post"),
        ("/api/automation/institutional-lab/execution-desk/simulate", "post"),
        ("/api/automation/institutional-lab/audit", "get"),
        ("/api/automation/run-once", "post"),
        ("/api/performance/health", "get"),
        ("/api/performance/report", "get"),
        ("/api/performance/backtest", "post"),
        ("/api/performance/paper-summary", "post"),
        ("/api/providers/health", "get"),
        ("/api/providers/registry", "get"),
        ("/api/providers/sharp/health", "get"),
        ("/api/providers/sharp/snapshot", "post"),
        ("/api/providers/kalshi/health", "get"),
        ("/api/providers/kalshi/snapshot", "post"),
    })


    def _live_openapi_paths() -> set[str]:
        return {
            route.path
            for route in app.routes
            if isinstance(route, APIRoute) and route.include_in_schema
        }


    def _attach_api_key_openapi_security(schema: dict[str, Any]) -> None:
        components = schema.setdefault("components", {})
        schemes = components.setdefault("securitySchemes", {})
        schemes["ApiKeyAuth"] = {"type": "apiKey", "in": "header", "name": "X-API-Key"}
        requirement = [{"ApiKeyAuth": []}]
        for path_key, path_item in schema.get("paths", {}).items():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                    continue
                if not isinstance(operation, dict):
                    continue
                if (path_key, method) in PUBLIC_OPENAPI_PATH_METHODS:
                    continue
                operation.setdefault("security", requirement)


    def custom_openapi():
        cached = app.openapi_schema
        live_paths = _live_openapi_paths()
        if isinstance(cached, dict):
            cached_paths = set(cached.get("paths", {}))
            if cached_paths == live_paths:
                return cached

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description or "",
            routes=app.routes,
        )
        schema["info"]["description"] = "Public API contract for the Betting Stock market intelligence platform."
        schema["servers"] = [{"url": API_BASE_URL}]
        _attach_api_key_openapi_security(schema)
        app.openapi_schema = schema
        return schema


    app.openapi = custom_openapi;

