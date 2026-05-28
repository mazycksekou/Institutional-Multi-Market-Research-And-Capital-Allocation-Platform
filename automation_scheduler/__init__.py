from __future__ import annotations

from .scheduler_runner import run_scheduler_once
from .system_health import get_system_health
from .review_queue import list_active_review_items
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories


def get_scheduler_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return get_system_health(config)


def get_scheduler_review_queue(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    items = list_active_review_items(config)
    return {
        "ok": True,
        "count": len(items),
        "items": items,
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }
