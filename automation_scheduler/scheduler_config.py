from __future__ import annotations

import os
import re
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "automation_scheduler.v1"
ROI_TARGET_DISCLAIMER = "ROI target is a filter target, not a guarantee."


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_filename(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return compact[:120] or "item"


def safe_run_id(namespace: str, seed: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{seed}").hex[:16]


def clamp(value: Any, minimum: float, maximum: float) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        n = minimum
    return max(minimum, min(maximum, n))


def redact_secrets(payload: Any) -> Any:
    if isinstance(payload, dict):
        out = {}
        for k, v in payload.items():
            lk = str(k).lower()
            if any(s in lk for s in ("key", "secret", "token", "password", "auth", "credential")):
                out[k] = "[redacted]"
            else:
                out[k] = redact_secrets(v)
        return out
    if isinstance(payload, list):
        return [redact_secrets(v) for v in payload]
    return payload


def hash_payload(payload: Any) -> str:
    safe_text = repr(redact_secrets(payload)).encode("utf-8")
    return hashlib.sha256(safe_text).hexdigest()


def ensure_runtime_directories(config: dict[str, Any]) -> dict[str, str]:
    for p in config["paths"].values():
        Path(p).mkdir(parents=True, exist_ok=True)
    return config["paths"]


def get_default_scheduler_config(base_data_dir: str | None = None) -> dict[str, Any]:
    from .provider_registry import get_provider_registry

    root = Path(base_data_dir or os.getenv("AUTOMATION_SCHEDULER_DATA_DIR", "data"))
    cfg = {
        "schema_version": SCHEMA_VERSION,
        "dry_run": True,
        "human_approval_required": True,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "auto_execution_enabled": False,
        "paper_execution_only": True,
        "alert_only_mode": True,
        "roi_target_percent": 10,
        "roi_target_is_filter_only": True,
        "paths": {
            "snapshots": str(root / "snapshots"),
            "reports": str(root / "reports"),
            "review_queue": str(root / "review_queue"),
            "audit_log": str(root / "audit_log"),
            "system_health": str(root / "system_health"),
            "scheduler_runs": str(root / "scheduler_runs"),
        },
        "score_thresholds": {"ignore_below": 55, "watch_threshold": 55, "review_threshold": 70, "urgent_threshold": 85},
        "cadence_profiles": {
            "sports_pregame_main": {"hot_watchlist_seconds": 60, "broad_scan_seconds": 300},
            "sports_player_props": {"hot_watchlist_seconds": 90, "broad_scan_seconds": 300},
            "sports_live": {"hot_watchlist_seconds": 15, "fallback_seconds": 60, "streaming_preferred": True},
            "prediction_markets": {"hot_watchlist_seconds": 30, "broad_scan_seconds": 300, "streaming_preferred": True},
            "stocks_watchlist": {"hot_watchlist_seconds": 15, "broad_scan_seconds": 60, "streaming_preferred": True},
            "news_events": {"standard_watchlist_seconds": 300},
            "low_liquidity": {"standard_watchlist_seconds": 900},
            "stocks_broad": {"slow_scan_seconds": 300},
        },
        "providers": get_provider_registry(),
    }
    ensure_runtime_directories(cfg)
    return cfg


SchedulerConfig = dict[str, Any]
