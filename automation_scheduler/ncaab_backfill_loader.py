from __future__ import annotations

from pathlib import Path
from typing import Any

from .basketball_loader_ready_backfill import (
    build_and_write_basketball_loader_ready_backfill_report,
    build_basketball_loader_ready_backfill_report,
    write_basketball_loader_ready_backfill_report,
)


SPORT = "basketball_ncaab"


def build_ncaab_backfill_loader_report() -> dict[str, Any]:
    return build_basketball_loader_ready_backfill_report(sport=SPORT)


def build_ncaab_backfill_loader() -> dict[str, Any]:
    return build_ncaab_backfill_loader_report()


def write_ncaab_backfill_loader_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_basketball_loader_ready_backfill_report(report, output_dir=output_dir)


def build_and_write_ncaab_backfill_loader_report(*, output_dir: str | Path | None = None) -> dict[str, Any]:
    return build_and_write_basketball_loader_ready_backfill_report(sport=SPORT, output_dir=output_dir)
