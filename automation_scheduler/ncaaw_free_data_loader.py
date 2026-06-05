from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import load_free_data_sample


def load_ncaaw_free_data_sample(lane_name: str | None = None, *, run_live_sample: bool = False) -> dict[str, Any]:
    return load_free_data_sample("basketball_ncaaw", lane_name=lane_name, run_live_sample=run_live_sample)
