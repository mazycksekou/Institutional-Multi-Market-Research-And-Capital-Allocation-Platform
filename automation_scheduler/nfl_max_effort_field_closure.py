from __future__ import annotations

from pathlib import Path

from .max_effort_source_discovery import build_nfl_field_closure_report, write_nfl_field_closure_report


def build_nfl_max_effort_field_closure_report(*, base_data_dir: str | Path | None = None) -> dict:
    return build_nfl_field_closure_report(base_data_dir=base_data_dir)


def write_nfl_max_effort_field_closure_report(report: dict, *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_nfl_field_closure_report(report, output_dir=output_dir)
