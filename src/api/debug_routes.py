from __future__ import annotations

from typing import Any

from fastapi import Depends



def register_debug_routes(app: Any, *, require_action_key: Any, get_configured_action_key: Any) -> None:
    """
    Register debug/config/auth-status routes.

    Canonical owner: src/api/debug_routes.py
    """

    @app.get("/api/debug/config", operation_id="debugConfig", dependencies=[Depends(require_action_key)])
    async def debug_config():
        return {
            "ok": True,
            "environment": {
                "ODDS_API_KEY": bool(os.getenv("ODDS_API_KEY")),
                "ODDS_API_ENABLED": os.getenv("ODDS_API_ENABLED", "true").lower() == "true",
                "ACTION_API_KEY": bool(os.getenv("ACTION_API_KEY")),
                "SHARP_API_KEY": bool(os.getenv("SHARP_API_KEY")),
                "SHARP_API_BASE_URL": bool(os.getenv("SHARP_API_BASE_URL")),
                "SHARP_API_ENABLED": os.getenv("SHARP_API_ENABLED", "false").lower() == "true",
                "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
                "KALSHI_ENABLED": os.getenv("KALSHI_ENABLED", "false").lower() == "true",
                "KALSHI_ENV": os.getenv("KALSHI_ENV", "demo"),
                "KALSHI_BASE_URL": bool(os.getenv("KALSHI_BASE_URL")),
                "KALSHI_API_KEY_ID": bool(os.getenv("KALSHI_API_KEY_ID")),
                "KALSHI_PRIVATE_KEY": bool(os.getenv("KALSHI_PRIVATE_KEY")),
            },
            "default_bookmakers": DEFAULT_BOOKMAKERS,
            "default_regions": DEFAULT_REGIONS,
            "default_betting_provider": PROVIDER_ROUTER.default_betting_provider(),
            "default_market_provider": PROVIDER_ROUTER.default_market_provider(),
        }


    @app.get("/api/debug/auth-status", operation_id="getAuthStatus")
    async def auth_status():
        return {
            "action_api_key_configured": bool(get_configured_action_key()),
            "accepted_headers": ["X-API-Key", "Authorization: Bearer"],
            "auth_dependency_loaded": True,
        }
