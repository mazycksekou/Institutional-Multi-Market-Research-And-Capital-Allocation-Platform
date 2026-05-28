from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "automation_scheduler.v1"
ROI_TARGET_DISCLAIMER = "ROI target is a filter target, not a guarantee."
_SECRET_TOKENS = ("key", "secret", "token", "password", "auth", "credential")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: Any, minimum: float, maximum: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = minimum
    return max(minimum, min(maximum, numeric))


def safe_run_id(namespace: str, seed: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{seed}").hex[:16]


def _default_data_root(base_data_dir: str | None = None) -> Path:
    root = base_data_dir or os.getenv("AUTOMATION_SCHEDULER_DATA_DIR", "data")
    return Path(root)


def ensure_runtime_directories(config: dict[str, Any]) -> dict[str, str]:
    paths = config["paths"]
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)
    return paths


def sanitize_filename(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return compact[:120] or "item"


def redact_secrets(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _SECRET_TOKENS):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = redact_secrets(value)
        return redacted
    if isinstance(payload, list):
        return [redact_secrets(item) for item in payload]
    if isinstance(payload, tuple):
        return [redact_secrets(item) for item in payload]
    return payload


def hash_payload(payload: Any) -> str:
    safe_text = repr(redact_secrets(payload)).encode("utf-8")
    return hashlib.sha256(safe_text).hexdigest()


def get_default_scheduler_config(base_data_dir: str | None = None) -> dict[str, Any]:
    from .provider_registry import get_provider_registry

    data_root = _default_data_root(base_data_dir)
    config = {
        "schema_version": SCHEMA_VERSION,
        "dry_run": True,
        "human_approval_required": True,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "auto_execution_enabled": False,
        "paper_execution_only": True,
        "alert_only_mode": True,
        "roi_target_percent": 10,
        "paths": {
            "snapshots": str(data_root / "snapshots"),
            "reports": str(data_root / "reports"),
            "review_queue": str(data_root / "review_queue"),
            "audit_log": str(data_root / "audit_log"),
            "system_health": str(data_root / "system_health"),
        },
        "score_thresholds": {
            "ignore_below": 55,
            "watch_threshold": 55,
            "review_threshold": 70,
            "urgent_threshold": 85,
            "auto_execution_threshold_later": 92,
        },
        "cadence_profiles": {
            "sports_pregame_main": {
                "hot_watchlist_seconds": 30,
                "standard_watchlist_seconds": 60,
                "broad_scan_seconds": 300,
            },
            "sports_player_props": {
                "hot_watchlist_seconds": 45,
                "standard_watchlist_seconds": 90,
                "broad_scan_seconds": 300,
            },
            "sports_live": {
                "streaming_preferred": True,
                "hot_watchlist_seconds": 5,
                "standard_watchlist_seconds": 15,
                "fallback_seconds": 60,
                "not_competitive_for_live": True,
            },
            "prediction_markets": {
                "streaming_preferred": True,
                "hot_watchlist_seconds": 15,
                "standard_watchlist_seconds": 30,
                "broad_scan_seconds": 300,
            },
            "stocks_watchlist": {
                "streaming_preferred": True,
                "hot_watchlist_seconds": 5,
                "standard_watchlist_seconds": 15,
                "broad_scan_seconds": 60,
            },
            "stocks_broad": {
                "standard_scan_seconds": 60,
                "slow_scan_seconds": 300,
            },
            "news_events": {
                "hot_watchlist_seconds": 60,
                "standard_watchlist_seconds": 300,
                "broad_scan_seconds": 900,
            },
            "low_liquidity": {
                "standard_scan_seconds": 300,
                "slow_scan_seconds": 900,
            },
        },
        "providers": get_provider_registry(),
    }
    ensure_runtime_directories(config)
    return config
