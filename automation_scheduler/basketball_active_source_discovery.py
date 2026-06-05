from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import (
    build_basketball_active_source_discovery_log,
    write_basketball_active_source_discovery_log,
)


def run_basketball_active_source_discovery(*, persist: bool = False) -> dict[str, Any]:
    report = build_basketball_active_source_discovery_log()
    if persist:
        report = {**report, "paths": write_basketball_active_source_discovery_log(report)}
    return report
