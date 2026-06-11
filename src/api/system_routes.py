from __future__ import annotations

from typing import Any


def register_system_routes(app: Any) -> None:
    """
    Register lightweight public system/debug routes.

    Canonical owner: src/api/system_routes.py
    """

    @app.get("/", operation_id="root")
    async def root():
        return {
            "ok": True,
            "service": "betting-stock-api",
            "status": "running",
        }

    @app.head("/", include_in_schema=False)
    async def root_head():
        return {}

    @app.get("/health", operation_id="healthCheck")
    async def health_check():
        return {"ok": True, "status": "ok", "service": "betting-stock-api"}

    @app.get("/ping", operation_id="ping")
    async def ping():
        return {"ok": True, "pong": True}

    @app.get("/debug/routes", include_in_schema=False)
    async def debug_routes():
        return [
            {
                "path": getattr(route, "path", None),
                "name": getattr(route, "name", None),
                "methods": sorted(getattr(route, "methods", []) or []),
            }
            for route in getattr(app, "routes", [])
        ]
