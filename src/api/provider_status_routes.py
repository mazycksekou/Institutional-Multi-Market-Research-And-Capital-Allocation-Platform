from __future__ import annotations

from typing import Any

from fastapi import Query

import src.services.automation_scheduler_facade as automation_scheduler
from src.services.automation_scheduler_facade import (
    compact_provider_health_response,
    compact_provider_registry_response,
    compact_provider_status,
    redact_and_limit_payload,
)


def register_provider_status_routes(app: Any) -> None:
    """
    Register provider health/registry/snapshot routes.

    Canonical owner: src/api/provider_status_routes.py
    """

    @app.get("/api/providers/health", operation_id="getProvidersHealth")
    async def get_providers_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_provider_health()
        compact = compact_provider_health_response(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/providers/registry", operation_id="getProvidersRegistry")
    async def get_providers_registry_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_provider_registry_snapshot()
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_provider_registry_response(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/providers/sharp/health", operation_id="getSharpProviderHealth")
    async def get_sharp_provider_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_sharp_provider_health()
        compact = compact_provider_status(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/providers/sharp/snapshot", operation_id="createSharpProviderSnapshot")
    async def create_sharp_provider_snapshot_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.run_sharp_provider_snapshot()
        compact = compact_provider_status(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/providers/kalshi/health", operation_id="getKalshiProviderHealth")
    async def get_kalshi_provider_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.get_kalshi_provider_health()
        compact = compact_provider_status(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/providers/kalshi/snapshot", operation_id="createKalshiProviderSnapshot")
    async def create_kalshi_provider_snapshot_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = automation_scheduler.run_kalshi_provider_snapshot()
        compact = compact_provider_status(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact
