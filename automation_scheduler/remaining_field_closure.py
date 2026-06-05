from __future__ import annotations

from pathlib import Path

from .max_effort_source_discovery import (
    build_existing_field_closure_report,
    build_manual_templates,
    write_existing_field_closure_report,
    write_manual_templates,
)


def build_remaining_field_closure_report(*, base_data_dir: str | Path | None = None) -> dict:
    return build_existing_field_closure_report(base_data_dir=base_data_dir)


def write_remaining_field_closure_report(report: dict, *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_existing_field_closure_report(report, output_dir=output_dir)


def build_remaining_manual_templates(*, base_data_dir: str | Path | None = None) -> dict:
    return build_manual_templates(base_data_dir=base_data_dir)


def write_remaining_manual_templates(report: dict, *, output_dir: str | Path | None = None) -> dict[str, str]:
    return write_manual_templates(report, output_dir=output_dir)
