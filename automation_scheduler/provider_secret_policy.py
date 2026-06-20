from __future__ import annotations

import os
from typing import Any

from src.providers.policy.secret_policy import (
    assert_no_secret_leak,
    list_required_secret_names as _canonical_list_required_secret_names,
    redact_http_diagnostic,
    redact_mapping,
    redact_secret,
)


def _normalize_provider(provider_id: str) -> str:
    return str(provider_id or "").strip().lower()


def list_required_secret_names(provider_id: str) -> list[str]:
    provider = _normalize_provider(provider_id)
    if provider == "sharp_sportsbook":
        return ["SHARP_API_KEY"]
    if provider in {"kalshi_prediction_market", "kalshi"}:
        return ["KALSHI_API_KEY", "KALSHI_API_SECRET"]
    return _canonical_list_required_secret_names(provider_id)


def credential_status_from_env(provider_id: str) -> dict[str, Any]:
    required = list_required_secret_names(provider_id)
    if not required:
        return {"status": "not_required", "required": [], "present": [], "missing": []}
    present = [name for name in required if os.getenv(name, "").strip()]
    missing = [name for name in required if name not in present]
    status = "ok" if not missing else "missing_credentials"
    return {
        "status": status,
        "required": required,
        "present": present,
        "missing": missing,
    }


__all__ = [
    "assert_no_secret_leak",
    "credential_status_from_env",
    "list_required_secret_names",
    "redact_http_diagnostic",
    "redact_mapping",
    "redact_secret",
]
