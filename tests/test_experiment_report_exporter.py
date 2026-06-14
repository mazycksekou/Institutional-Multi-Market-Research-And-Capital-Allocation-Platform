from __future__ import annotations
"""Tests for Phase 10H18 – experiment_report_exporter."""


import json
from pathlib import Path
from typing import Any

import pytest

from automation_scheduler.experiment_report_exporter import (
    build_experiment_report_export,
    build_experiment_report_sections,
    format_report_money,
    format_report_percent,
    normalize_report_value,
    render_experiment_report_markdown,
)
from automation_scheduler.experiment_history_store import (
    save_experiment_history_run,
    initialize_experiment_history_store,
)


# ---------------------------------------------------------------------------
# normalize_report_value
# ---------------------------------------------------------------------------


def test_normalize_report_value_handles_none_scalars_and_json():
    assert normalize_report_value(None) == ""
    assert normalize_report_value(True) == "Yes"
    assert normalize_report_value(False) == "No"
    assert normalize_report_value(5) == "5"
    assert normalize_report_value(3.14) == "3.14"
    assert normalize_report_value("hello") == "hello"
    assert json.loads(normalize_report_value([1, 2])) == [1, 2]
    assert json.loads(normalize_report_value({"a": 1})) == {"a": 1}
    assert normalize_report_value(set()) == "set()"  # fallback


# ---------------------------------------------------------------------------
# format_report_percent
# ---------------------------------------------------------------------------


def test_format_report_percent():
    assert format_report_percent(None) == ""
    assert format_report_percent("") == ""
    assert format_report_percent(10.5) == "10.50%"
    assert format_report_percent("12.3") == "12.30%"
    assert format_report_percent("0.2%") == "0.20%"
    assert format_report_percent("abc") == "abc"  # nonnumeric


# ---------------------------------------------------------------------------
# format_report_money
# ---------------------------------------------------------------------------


def test_format_report_money():
    assert format_report_money(None) == ""
    assert format_report_money("") == ""
    assert format_report_money(123.1) == "123.10"
    assert format_report_money("45.678") == "45.68"
    assert format_report_money("$1,234.50") == "1234.50"
    assert format_report_money("abc") == "abc"


# ---------------------------------------------------------------------------
# build_experiment_report_sections
# ---------------------------------------------------------------------------


def test_build_experiment_report_sections_does_not_mutate_input():
    inp: dict[str, Any] = {"run_id": "exp_1"}
    original_id = id(inp)
    sections = build_experiment_report_sections(inp)
    assert id(inp) == original_id
    # The returned dict should be separate
    assert inp["run_id"] == "exp_1"


def test_build_experiment_report_sections_contains_expected_groups():
    run = {
        "run_id": "test_run",
        "created_at": "2026-06-14T12:00:00Z",
        "run_type": "calibration_strategy_filter",
        "run_label": "test",
        "notes": "None",
        "mode": "single_sport",
        "sport_key": "basketball_nba",
        "market_family": "general_market",
        "total_rows": 100,
        "included_row_count": 90,
        "excluded_row_count": 10,
        "eligible_rows": 80,
        "skipped_rows": 5,
        "settled_count": 40,
        "wins": 20,
        "losses": 15,
        "pushes": 5,
        "net_result": 12.34,
        "roi_percent": "5.00",
        "win_rate_percent": "55.55",
        "selected_groups": ["core_event"],
        "selected_fields": ["sport", "league"],
        "removed_fields": ["player_stats"],
        "active_fields": ["sport"],
        "included_sports": ["basketball_nba"],
        "excluded_sports": ["baseball_mlb"],
        "included_market_families": ["moneyline_or_1x2"],
        "excluded_market_families": ["player_prop"],
        "roi_by_sport": {"basketball_nba": {"net_result": 12.34}},
        "roi_by_market_family": {"moneyline_or_1x2": {"net_result": 12.34}},
        "warnings": ["test warning"],
        "config": {"some": "value"},
        "extra_field": "should be in raw_keys",
    }
    sections = build_experiment_report_sections(run)
    assert "summary" in sections
    assert "configuration" in sections
    assert "fields" in sections
    assert "inclusion_exclusion" in sections
    assert "performance" in sections
    assert "warnings" in sections
    assert "raw_keys" in sections
    assert sections["summary"]["run_id"] == "test_run"
    assert sections["summary"]["run_type"] == "calibration_strategy_filter"
    assert sections["performance"]["net_result"] == "12.34"
    assert sections["configuration"]["total_rows"] == "100"
    assert "extra_field" in sections["raw_keys"]


# ---------------------------------------------------------------------------
# render_experiment_report_markdown
# ---------------------------------------------------------------------------


def test_render_experiment_report_markdown_contains_required_heading_and_sentence():
    run = {"run_id": "x"}
    md = render_experiment_report_markdown(run)["markdown"]
    assert "# Calibration Report / Operator Review Pack" in md
    assert (
        "This report exports a saved ablation or calibration run "
        "for offline operator review." in md
    )


def test_render_experiment_report_markdown_contains_required_sections():
    run = {"run_id": "y"}
    md = render_experiment_report_markdown(run)["markdown"]
    assert "## Run Summary" in md
    assert "## Configuration" in md
    assert "## Field Selection" in md
    assert "## Inclusion / Exclusion" in md
    assert "## Performance" in md
    assert "## ROI by Sport" in md
    assert "## ROI by Market Family" in md
    assert "## Warnings" in md
    assert "## Review Notes" in md


def test_render_experiment_report_markdown_includes_leakage_safety_note():
    run = {"run_id": "z"}
    md = render_experiment_report_markdown(run)["markdown"]
    assert "Leakage fields are not allowed as active pre-decision fields." in md


def test_render_experiment_report_markdown_handles_empty_sections():
    run = {"run_id": "empty", "warnings": []}
    md = render_experiment_report_markdown(run)["markdown"]
    # Empty warnings should say "None recorded."
    assert "None recorded." in md
    # empty roi sections
    assert "None recorded." in md


# ---------------------------------------------------------------------------
# build_experiment_report_export
# ---------------------------------------------------------------------------


def test_build_experiment_report_export_returns_markdown_for_saved_run(tmp_path):
    db_path = tmp_path / "export_test.db"
    init = initialize_experiment_history_store(db_path)
    assert init["ok"]
    result = {"run_id": "test_run_for_export", "total_rows": 50, "warnings": []}
    saved = save_experiment_history_run(db_path, result, run_label="export_test")
    assert saved["saved"]
    run_id = saved["run_id"]
    export = build_experiment_report_export(db_path, run_id, export_format="markdown")
    assert export["ok"]
    assert export["export_format"] == "markdown"
    assert export["filename"].endswith(".md")
    assert "Calibration Report" in export["markdown"]
    assert export["warnings"] == []


def test_build_experiment_report_export_missing_run_returns_not_found(tmp_path):
    db_path = tmp_path / "missing_run.db"
    export = build_experiment_report_export(db_path, "nonexistent_id")
    assert not export["ok"]
    assert "not_found" in export["warnings"]


def test_build_experiment_report_export_unsupported_format_returns_warning(tmp_path):
    db_path = tmp_path / "unsup.db"
    export = build_experiment_report_export(
        db_path, "some_id", export_format="pdf"
    )
    assert not export["ok"]
    assert "unsupported_export_format" in export["warnings"]


def test_export_filename_is_safe_and_markdown(tmp_path):
    db_path = tmp_path / "safe_name.db"
    init = initialize_experiment_history_store(db_path)
    assert init["ok"]
    result = {"total_rows": 10}
    saved = save_experiment_history_run(db_path, result)
    run_id = saved["run_id"]
    export = build_experiment_report_export(db_path, run_id)
    fn = export["filename"]
    assert fn.startswith("calibration_report_")
    assert fn.endswith(".md")
    # No characters that cause filesystem issues
    assert all(c.isalnum() or c in ("-", "_", ".") for c in fn)


def test_report_uses_2_way_3_way_moneyline_wording_not_legacy_preferred_label(
    tmp_path,
):
    db_path = tmp_path / "wording.db"
    init = initialize_experiment_history_store(db_path)
    assert init["ok"]
    result = {"total_rows": 5}
    saved = save_experiment_history_run(db_path, result)
    run_id = saved["run_id"]
    export = build_experiment_report_export(db_path, run_id)
    for phrase in ("1x2", "moneyline_or_1x2"):
        # The literal string "moneyline_or_1x2" should NOT appear in the
        # rendered markdown for wording preference; we check it doesn't
        # contain the literal key as the pref label.  The markdown
        # includes "2-Way / 3-Way Moneyline".
        pass
    assert "2-Way / 3-Way Moneyline" in export["markdown"]
    assert "moneyline_or_1x2" not in export["markdown"]
"""Tests for Phase 10H18 – experiment_report_exporter."""


import json
from pathlib import Path
from typing import Any

import pytest

from automation_scheduler.experiment_report_exporter import (
    build_experiment_report_export,
    build_experiment_report_sections,
    format_report_money,
    format_report_percent,
    normalize_report_value,
    render_experiment_report_markdown,
)
from automation_scheduler.experiment_history_store import (
    save_experiment_history_run,
    initialize_experiment_history_store,
)


# ---------------------------------------------------------------------------
# normalize_report_value
# ---------------------------------------------------------------------------


def test_normalize_report_value_handles_none_scalars_and_json():
    assert normalize_report_value(None) == ""
    assert normalize_report_value(True) == "Yes"
    assert normalize_report_value(False) == "No"
    assert normalize_report_value(5) == "5"
    assert normalize_report_value(3.14) == "3.14"
    assert normalize_report_value("hello") == "hello"
    assert json.loads(normalize_report_value([1, 2])) == [1, 2]
    assert json.loads(normalize_report_value({"a": 1})) == {"a": 1}
    assert normalize_report_value(set()) == "set()"  # fallback


# ---------------------------------------------------------------------------
# format_report_percent
# ---------------------------------------------------------------------------


def test_format_report_percent():
    assert format_report_percent(None) == ""
    assert format_report_percent("") == ""
    assert format_report_percent(10.5) == "10.50%"
    assert format_report_percent("12.3") == "12.30%"
    assert format_report_percent("0.2%") == "0.20%"
    assert format_report_percent("abc") == "abc"  # nonnumeric


# ---------------------------------------------------------------------------
# format_report_money
# ---------------------------------------------------------------------------


def test_format_report_money():
    assert format_report_money(None) == ""
    assert format_report_money("") == ""
    assert format_report_money(123.1) == "123.10"
    assert format_report_money("45.678") == "45.68"
    assert format_report_money("$1,234.50") == "1234.50"
    assert format_report_money("abc") == "abc"


# ---------------------------------------------------------------------------
# build_experiment_report_sections
# ---------------------------------------------------------------------------


def test_build_experiment_report_sections_does_not_mutate_input():
    inp: dict[str, Any] = {"run_id": "exp_1"}
    original_id = id(inp)
    sections = build_experiment_report_sections(inp)
    assert id(inp) == original_id
    # The returned dict should be separate
    assert inp["run_id"] == "exp_1"


def test_build_experiment_report_sections_contains_expected_groups():
    run = {
        "run_id": "test_run",
        "created_at": "2026-06-14T12:00:00Z",
        "run_type": "calibration_strategy_filter",
        "run_label": "test",
        "notes": "None",
        "mode": "single_sport",
        "sport_key": "basketball_nba",
        "market_family": "general_market",
        "total_rows": 100,
        "included_row_count": 90,
        "excluded_row_count": 10,
        "eligible_rows": 80,
        "skipped_rows": 5,
        "settled_count": 40,
        "wins": 20,
        "losses": 15,
        "pushes": 5,
        "net_result": 12.34,
        "roi_percent": "5.00",
        "win_rate_percent": "55.55",
        "selected_groups": ["core_event"],
        "selected_fields": ["sport", "league"],
        "removed_fields": ["player_stats"],
        "active_fields": ["sport"],
        "included_sports": ["basketball_nba"],
        "excluded_sports": ["baseball_mlb"],
        "included_market_families": ["moneyline_or_1x2"],
        "excluded_market_families": ["player_prop"],
        "roi_by_sport": {"basketball_nba": {"net_result": 12.34}},
        "roi_by_market_family": {"moneyline_or_1x2": {"net_result": 12.34}},
        "warnings": ["test warning"],
        "config": {"some": "value"},
        "extra_field": "should be in raw_keys",
    }
    sections = build_experiment_report_sections(run)
    assert "summary" in sections
    assert "configuration" in sections
    assert "fields" in sections
    assert "inclusion_exclusion" in sections
    assert "performance" in sections
    assert "warnings" in sections
    assert "raw_keys" in sections
    assert sections["summary"]["run_id"] == "test_run"
    assert sections["summary"]["run_type"] == "calibration_strategy_filter"
    assert sections["performance"]["net_result"] == "12.34"
    assert sections["configuration"]["total_rows"] == "100"
    assert "extra_field" in sections["raw_keys"]


# ---------------------------------------------------------------------------
# render_experiment_report_markdown
# ---------------------------------------------------------------------------


def test_render_experiment_report_markdown_contains_required_heading_and_sentence():
    run = {"run_id": "x"}
    md = render_experiment_report_markdown(run)["markdown"]
    assert "# Calibration Report / Operator Review Pack" in md
    assert (
        "This report exports a saved ablation or calibration run "
        "for offline operator review." in md
    )


def test_render_experiment_report_markdown_contains_required_sections():
    run = {"run_id": "y"}
    md = render_experiment_report_markdown(run)["markdown"]
    assert "## Run Summary" in md
    assert "## Configuration" in md
    assert "## Field Selection" in md
    assert "## Inclusion / Exclusion" in md
    assert "## Performance" in md
    assert "## ROI by Sport" in md
    assert "## ROI by Market Family" in md
    assert "## Warnings" in md
    assert "## Review Notes" in md


def test_render_experiment_report_markdown_includes_leakage_safety_note():
    run = {"run_id": "z"}
    md = render_experiment_report_markdown(run)["markdown"]
    assert "Leakage fields are not allowed as active pre-decision fields." in md


def test_render_experiment_report_markdown_handles_empty_sections():
    run = {"run_id": "empty", "warnings": []}
    md = render_experiment_report_markdown(run)["markdown"]
    # Empty warnings should say "None recorded."
    assert "None recorded." in md
    # empty roi sections
    assert "None recorded." in md


# ---------------------------------------------------------------------------
# build_experiment_report_export
# ---------------------------------------------------------------------------


def test_build_experiment_report_export_returns_markdown_for_saved_run(tmp_path):
    db_path = tmp_path / "export_test.db"
    init = initialize_experiment_history_store(db_path)
    assert init["ok"]
    result = {"run_id": "test_run_for_export", "total_rows": 50, "warnings": []}
    saved = save_experiment_history_run(db_path, result, run_label="export_test")
    assert saved["saved"]
    run_id = saved["run_id"]
    export = build_experiment_report_export(db_path, run_id, export_format="markdown")
    assert export["ok"]
    assert export["export_format"] == "markdown"
    assert export["filename"].endswith(".md")
    assert "Calibration Report" in export["markdown"]
    assert export["warnings"] == []


def test_build_experiment_report_export_missing_run_returns_not_found(tmp_path):
    db_path = tmp_path / "missing_run.db"
    export = build_experiment_report_export(db_path, "nonexistent_id")
    assert not export["ok"]
    assert "not_found" in export["warnings"]


def test_build_experiment_report_export_unsupported_format_returns_warning(tmp_path):
    db_path = tmp_path / "unsup.db"
    export = build_experiment_report_export(
        db_path, "some_id", export_format="pdf"
    )
    assert not export["ok"]
    assert "unsupported_export_format" in export["warnings"]


def test_export_filename_is_safe_and_markdown(tmp_path):
    db_path = tmp_path / "safe_name.db"
    init = initialize_experiment_history_store(db_path)
    assert init["ok"]
    result = {"total_rows": 10}
    saved = save_experiment_history_run(db_path, result)
    run_id = saved["run_id"]
    export = build_experiment_report_export(db_path, run_id)
    fn = export["filename"]
    assert fn.startswith("calibration_report_")
    assert fn.endswith(".md")
    # No characters that cause filesystem issues
    assert all(c.isalnum() or c in ("-", "_", ".") for c in fn)


def test_report_uses_2_way_3_way_moneyline_wording_not_legacy_preferred_label(
    tmp_path,
):
    db_path = tmp_path / "wording.db"
    init = initialize_experiment_history_store(db_path)
    assert init["ok"]
    result = {"total_rows": 5}
    saved = save_experiment_history_run(db_path, result)
    run_id = saved["run_id"]
    export = build_experiment_report_export(db_path, run_id)
    for phrase in ("1x2", "moneyline_or_1x2"):
        # The literal string "moneyline_or_1x2" should NOT appear in the
        # rendered markdown for wording preference; we check it doesn't
        # contain the literal key as the pref label.  The markdown
        # includes "2-Way / 3-Way Moneyline".
        pass
    assert "2-Way / 3-Way Moneyline" in export["markdown"]
    assert "moneyline_or_1x2" not in export["markdown"]
