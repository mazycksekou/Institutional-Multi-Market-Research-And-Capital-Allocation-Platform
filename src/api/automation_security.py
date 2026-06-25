from __future__ import annotations

import hmac
import os
from typing import Any, Optional

from fastapi import Header, HTTPException

from src.services.execution_support import get_storage_health


def get_configured_cron_token() -> Optional[str]:
    """
    Return the configured automation cron token, if one exists.

    Canonical owner: src/api/automation_security.py
    """
    for name in (
        "COLLECTOR_CRON_TOKEN",
        "AUTOMATION_CRON_TOKEN",
        "AUTOMATION_SCHEDULER_CRON_TOKEN",
        "SCHEDULER_CRON_TOKEN",
        "CRON_TOKEN",
        "CRON_SECRET",
    ):
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _clean_token(value: object) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_cron_token_response(status: str, *, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "errors": list(errors or [])[:10],
        "provider_write": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "storage_backend": "file",
        "storage_health": get_storage_health(),
        "raw_payload_included": False,
    }


def validate_cron_token(
    cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> tuple[bool, int, dict[str, Any] | None]:
    """
    Validate scheduled automation calls when a cron token is configured.

    If no cron token environment variable is configured, validation is permissive
    to preserve current local/dev behavior.
    """
    expected = get_configured_cron_token()
    if not expected:
        return False, 503, _safe_cron_token_response(
            "scheduled_endpoint_disabled",
            errors=["missing_COLLECTOR_CRON_TOKEN"],
        )

    provided = _clean_token(cron_token)

    auth = _clean_token(authorization)
    if not provided and auth and auth.lower().startswith("bearer "):
        provided = auth.split(" ", 1)[1].strip() or None

    if not provided or not hmac.compare_digest(provided, expected):
        return False, 401 if not provided else 403, _safe_cron_token_response(
            "unauthorized" if not provided else "forbidden",
            errors=["missing_X_Cron_Token"] if not provided else ["invalid_X_Cron_Token"],
        )

    return True, 200, None


def require_cron_token(
    cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> None:
    ok, status_code, payload = validate_cron_token(cron_token, authorization)
    if not ok:
        raise HTTPException(status_code=status_code, detail=payload)
