from __future__ import annotations

from pathlib import Path

from .max_effort_source_discovery import build_mlb_field_closure_report, write_mlb_field_closure_report


def build_mlb_max_effort_field_closure_report(*, base_data_dir: str | Path | None = None) -> dict:
    return build_mlb_field_closure_report(base_data_dir=base_data_dir)


def write_mlb_max_effort_field_closure_report(report: dict, *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_mlb_field_closure_report(report, output_dir=output_dir)
