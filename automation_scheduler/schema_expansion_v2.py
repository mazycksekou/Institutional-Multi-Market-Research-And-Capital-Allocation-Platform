from __future__ import annotations

from pathlib import Path

from .max_effort_source_discovery import (
    build_combined_schema_expansion_report,
    build_schema_expansion_v2_report,
    write_combined_schema_expansion_report,
    write_schema_expansion_v2_report,
)


def build_schema_expansion_v2(*, base_data_dir: str | Path | None = None) -> dict:
    return build_schema_expansion_v2_report(base_data_dir=base_data_dir)


def write_schema_expansion_v2(report: dict, *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_schema_expansion_v2_report(report, output_dir=output_dir)


def build_nfl_mlb_schema_expansion_report(*, base_data_dir: str | Path | None = None) -> dict:
    return build_combined_schema_expansion_report(base_data_dir=base_data_dir)


def write_nfl_mlb_schema_expansion_report(report: dict, *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_combined_schema_expansion_report(report, output_dir=output_dir)
