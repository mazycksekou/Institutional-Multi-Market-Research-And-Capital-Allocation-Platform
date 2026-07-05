from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends


def register_betting_metadata_routes(
    app: Any,
    *,
    require_action_key: Any,
    provider_router: Any,
) -> None:
    """
    Register compact betting metadata routes.

    Canonical owner: src/api/betting_metadata_routes.py
    """
    PROVIDER_ROUTER = provider_router

    @app.get("/api/betting/providers", operation_id="getBettingProviders", dependencies=[Depends(require_action_key)])
    async def get_betting_providers():
        return {
            "ok": True,
            "default_provider": PROVIDER_ROUTER.default_betting_provider(),
            "providers": PROVIDER_ROUTER.capabilities(),
        }


    @app.get("/api/betting/sports", operation_id="getSupportedBettingSports", dependencies=[Depends(require_action_key)])
    async def get_supported_betting_sports(provider: Optional[str] = None):
        return await PROVIDER_ROUTER.get_supported_sports(provider)
