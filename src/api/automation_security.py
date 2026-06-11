from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException


def get_configured_cron_token() -> Optional[str]:
    """
    Return the configured automation cron token, if one exists.

    Canonical owner: src/api/automation_security.py
    """
    for name in (
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


def validate_cron_token(
    cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> None:
    """
    Validate scheduled automation calls when a cron token is configured.

    If no cron token environment variable is configured, validation is permissive
    to preserve current local/dev behavior.
    """
    expected = get_configured_cron_token()
    if not expected:
        return None

    provided = _clean_token(cron_token)

    auth = _clean_token(authorization)
    if not provided and auth and auth.lower().startswith("bearer "):
        provided = auth.split(" ", 1)[1].strip() or None

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing cron token")

    return None
