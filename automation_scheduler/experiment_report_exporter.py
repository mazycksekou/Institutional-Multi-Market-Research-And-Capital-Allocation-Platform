"""Experiment Report Export – Phase 10H18.

Exports saved ablation/calibration runs as a clean human‑readable Markdown
review pack.  Does **not** re‑run model tests, alter any schema, or write
files to disk from this module.
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from automation_scheduler.experiment_history_store import (
    get_experiment_history_run,
)

EXPERIMENT_REPORT_EXPORT_VERSION: str = "10H18"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def normalize_report_value(value) -> str:
    """Convert report values into deterministic readable strings."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)

def format_report_percent(value: Any) -> str:
    """None/blank → ''; numeric → two decimals + '%'; string numbers → same;
    non‑numeric → original string."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    if isinstance(value, str):
        # try to interpret as numeric
        try:
            f = float(value.replace("%", "").strip())
            return f"{f:.2f}%"
        except (ValueError, AttributeError):
            return value
    return str(value)


def format_report_money(value: Any) -> str:
    """None/blank → ''; numeric → two decimals (no sign); string numbers → same;
    non‑numeric → original string."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    if isinstance(value, str):
        try:
            f = float(value.replace("$", "").replace(",", "").strip())
            return f"{f:.2f}"
        except (ValueError, AttributeError):
            return value
    return str(value)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _safe_value(value: Any, default: str = "") -> str:
    """Return a deterministic string, never crashing on weird input."""
    try:
        return normalize_report_value(value) or default
    except Exception:
        return default


def _safe_list(value: Any) -> list[str]:
    """Return a list of strings from value that may be a list or JSON string."""
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def _safe_dict(value: Any) -> dict[str, Any]:
    """Return a dict from value that may be a dict or JSON string."""
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return dict(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


# ---------------------------------------------------------------------------
# Build sections
# ---------------------------------------------------------------------------


def build_experiment_report_sections(run: Mapping[str, Any]) -> dict[str, Any]:
    """Return stable sections.  Input (run) is *never* mutated.

    Returns a plain dict with keys:
      summary, configuration, fields, inclusion_exclusion, performance,
      warnings, raw_keys
    """
    # Work on a safe copy for reading
    safe = dict(run)

    # Extract scalars
    def _s(key: str) -> str:
        return _safe_value(safe.get(key))

    def _l(key: str) -> list[str]:
        return _safe_list(safe.get(key))

    def _d(key: str) -> dict:
        return _safe_dict(safe.get(key))

    run_id = _s("run_id")
    created_at = _s("created_at")
    run_type = _s("run_type")
    run_label = _s("run_label")
    notes = _s("notes")
    mode = _s("mode")
    sport_key = _s("sport_key")
    market_family = _s("market_family")

    # Numeric fields (safe)
    def _n(key: str) -> str:
        # Return as string or default "0"
        val = safe.get(key)
        if val is None:
            return "0"
        try:
            return str(int(float(val))) if isinstance(val, (int, float)) else str(val)
        except (ValueError, TypeError):
            return "0"

    def _f(key: str) -> str:
        # Return as money string
        return format_report_money(safe.get(key))

    total_rows = _n("total_rows")
    included_row_count = _n("included_row_count")
    excluded_row_count = _n("excluded_row_count")
    eligible_rows = _n("eligible_rows")
    skipped_rows = _n("skipped_rows")
    settled_count = _n("settled_count")
    wins = _n("wins")
    losses = _n("losses")
    pushes = _n("pushes")
    net_result = _f("net_result")
    roi_percent = _s("roi_percent")  # use raw string since we want raw value
    win_rate_percent = _s("win_rate_percent")

    # List / dict fields
    selected_groups = _l("selected_groups")
    selected_fields = _l("selected_fields")
    removed_fields = _l("removed_fields")
    active_fields = _l("active_fields")
    included_sports = _l("included_sports")
    excluded_sports = _l("excluded_sports")
    included_market_families = _l("included_market_families")
    excluded_market_families = _l("excluded_market_families")

    roi_by_sport = _d("roi_by_sport")
    roi_by_market_family = _d("roi_by_market_family")
    warnings_raw = _l("warnings")
    config = _d("config")

    summary = {
        "run_id": run_id,
        "created_at": created_at,
        "run_type": run_type,
        "run_label": run_label,
        "notes": notes,
        "mode": mode,
        "sport_key": sport_key,
        "market_family": market_family,
    }

    configuration = {
        "total_rows": total_rows,
        "included_row_count": included_row_count,
        "excluded_row_count": excluded_row_count,
        "eligible_rows": eligible_rows,
        "skipped_rows": skipped_rows,
    }

    fields = {
        "selected_groups": selected_groups,
        "selected_fields": selected_fields,
        "removed_fields": removed_fields,
        "active_fields": active_fields,
    }

    inclusion_exclusion = {
        "included_sports": included_sports,
        "excluded_sports": excluded_sports,
        "included_market_families": included_market_families,
        "excluded_market_families": excluded_market_families,
    }

    performance = {
        "settled_count": settled_count,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "net_result": net_result,
        "roi_percent": roi_percent,
        "win_rate_percent": win_rate_percent,
    }

    warnings = warnings_raw

    raw_keys = list(safe.keys())

    return {
        "summary": summary,
        "configuration": configuration,
        "fields": fields,
        "inclusion_exclusion": inclusion_exclusion,
        "performance": performance,
        "warnings": warnings,
        "roi_by_sport": roi_by_sport,
        "roi_by_market_family": roi_by_market_family,
        "config": config,
        "raw_keys": raw_keys,
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _section_list(key: str, items: list[str]) -> str:
    if not items:
        return "  None recorded."
    lines = [f"  **{key}**"]
    for item in items:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def _section_dict(key: str, data: dict[str, Any]) -> str:
    if not data:
        return "  None recorded."
    lines = [f"  **{key}**"]
    for k, v in data.items():
        lines.append(f"  - {k}: {normalize_report_value(v)}")
    return "\n".join(lines)


def render_experiment_report_markdown(run: Mapping[str, Any]) -> dict[str, Any]:
    """Return stable dict with key 'markdown'.

    Input run is never mutated.
    """
    sections = build_experiment_report_sections(run)
    summary = sections["summary"]
    configuration = sections["configuration"]
    fields = sections["fields"]
    inc_exc = sections["inclusion_exclusion"]
    perf = sections["performance"]
    warnings = sections["warnings"]
    roi_sport = sections["roi_by_sport"]
    roi_mkt = sections["roi_by_market_family"]
    # config is not displayed in this version

    md_lines: list[str] = []

    md_lines.append("# Calibration Report / Operator Review Pack")
    md_lines.append("")
    md_lines.append(
        "This report exports a saved ablation or calibration run for offline operator review."
    )
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Run Summary
    md_lines.append("## Run Summary")
    md_lines.append("")
    for key, val in summary.items():
        md_lines.append(f"- **{key}**: {normalize_report_value(val)}")
    md_lines.append("")

    # Configuration
    md_lines.append("## Configuration")
    md_lines.append("")
    for key, val in configuration.items():
        md_lines.append(f"- **{key}**: {normalize_report_value(val)}")
    md_lines.append("")

    # Field Selection
    md_lines.append("## Field Selection")
    md_lines.append("")
    md_lines.append(
        "Leakage fields are not allowed as active pre-decision fields."
    )
    md_lines.append("")
    for key in ("selected_groups", "selected_fields", "removed_fields", "active_fields"):
        items = fields.get(key, [])
        md_lines.append(_section_list(key, items))
    md_lines.append("")

    # Inclusion / Exclusion
    md_lines.append("## Inclusion / Exclusion")
    md_lines.append("")
    md_lines.append(
        "2-Way / 3-Way Moneyline"
    )
    md_lines.append("")
    for key, items in inc_exc.items():
        md_lines.append(_section_list(key, items))
    md_lines.append("")

    # Performance
    md_lines.append("## Performance")
    md_lines.append("")
    for key, val in perf.items():
        md_lines.append(f"- **{key}**: {normalize_report_value(val)}")
    md_lines.append("")

    # ROI by Sport
    md_lines.append("## ROI by Sport")
    md_lines.append("")
    md_lines.append(_section_dict("roi_by_sport", roi_sport))
    md_lines.append("")

    # ROI by Market Family
    md_lines.append("## ROI by Market Family")
    md_lines.append("")
    md_lines.append(_section_dict("roi_by_market_family", roi_mkt))
    md_lines.append("")

    # Warnings
    md_lines.append("## Warnings")
    md_lines.append("")
    if warnings:
        for w in warnings:
            md_lines.append(f"- {normalize_report_value(w)}")
    else:
        md_lines.append("None recorded.")
    md_lines.append("")

    # Review Notes
    md_lines.append("## Review Notes")
    md_lines.append("")
    md_lines.append("*This is an exported report from an experiment history run.*")
    md_lines.append("")

    markdown = "\n".join(md_lines)

    return {
        "ok": True,
        "version": EXPERIMENT_REPORT_EXPORT_VERSION,
        "markdown": markdown,
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Public export function
# ---------------------------------------------------------------------------


def build_experiment_report_export(
    db_path: str | Path,
    run_id: str,
    export_format: str = "markdown",
) -> dict[str, Any]:
    """Fetch a saved run and build an export.

    Currently only ``markdown`` is supported.

    Returns stable dict with keys:
      ok, version, run_id, export_format, filename, content, markdown, warnings

    Does **not** write files to disk.
    """
    version = EXPERIMENT_REPORT_EXPORT_VERSION

    if not run_id or not run_id.strip():
        return {
            "ok": False,
            "version": version,
            "run_id": run_id or "",
            "export_format": export_format,
            "filename": "",
            "content": "",
            "markdown": "",
            "warnings": ["missing_run_id"],
        }

    if export_format != "markdown":
        return {
            "ok": False,
            "version": version,
            "run_id": run_id,
            "export_format": export_format,
            "filename": "",
            "content": "",
            "markdown": "",
            "warnings": ["unsupported_export_format"],
        }

    try:
        run_result = get_experiment_history_run(str(db_path), run_id)
    except Exception as exc:
        return {
            "ok": False,
            "version": version,
            "run_id": run_id,
            "export_format": export_format,
            "filename": "",
            "content": "",
            "markdown": "",
            "warnings": [f"could not query run: {exc}"],
        }

    if not run_result.get("found"):
        return {
            "ok": False,
            "version": version,
            "run_id": run_id,
            "export_format": export_format,
            "filename": "",
            "content": "",
            "markdown": "",
            "warnings": ["not_found"],
        }

    run = run_result["run"]
    rendered = render_experiment_report_markdown(run)
    if not rendered.get("ok"):
        return {
            "ok": False,
            "version": version,
            "run_id": run_id,
            "export_format": export_format,
            "filename": "",
            "content": "",
            "markdown": "",
            "warnings": rendered.get("warnings", []),
        }

    markdown = rendered["markdown"]

    # Build safe filename
    safe_run_id = "".join(c for c in run_id if c.isalnum() or c in ("-", "_"))
    if not safe_run_id:
        safe_run_id = "unknown"
    filename = f"calibration_report_{safe_run_id}.md"

    return {
        "ok": True,
        "version": version,
        "run_id": run_id,
        "export_format": export_format,
        "filename": filename,
        "content": markdown,
        "markdown": markdown,
        "warnings": [],
    }
