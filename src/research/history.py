from __future__ import annotations

from importlib import import_module
from typing import Any


def _legacy_history():
    return import_module("automation_scheduler.experiment_history_store")


def _legacy_report():
    return import_module("automation_scheduler.experiment_report_exporter")


def initialize_experiment_history_store(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().initialize_experiment_history_store(*args, **kwargs)


def normalize_experiment_history_run_type(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().normalize_experiment_history_run_type(*args, **kwargs)


def make_experiment_run_id(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().make_experiment_run_id(*args, **kwargs)


def extract_experiment_history_metrics(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().extract_experiment_history_metrics(*args, **kwargs)


def sanitize_experiment_history_result(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().sanitize_experiment_history_result(*args, **kwargs)


def save_experiment_history_run(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().save_experiment_history_run(*args, **kwargs)


def list_experiment_history_runs(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().list_experiment_history_runs(*args, **kwargs)


def get_experiment_history_run(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().get_experiment_history_run(*args, **kwargs)


def compare_experiment_history_runs(*args: Any, **kwargs: Any) -> Any:
    return _legacy_history().compare_experiment_history_runs(*args, **kwargs)


def build_experiment_report_export(*args: Any, **kwargs: Any) -> Any:
    return _legacy_report().build_experiment_report_export(*args, **kwargs)


def normalize_report_value(*args: Any, **kwargs: Any) -> Any:
    return _legacy_report().normalize_report_value(*args, **kwargs)


def format_report_percent(*args: Any, **kwargs: Any) -> Any:
    return _legacy_report().format_report_percent(*args, **kwargs)


def format_report_money(*args: Any, **kwargs: Any) -> Any:
    return _legacy_report().format_report_money(*args, **kwargs)


def build_experiment_report_sections(*args: Any, **kwargs: Any) -> Any:
    return _legacy_report().build_experiment_report_sections(*args, **kwargs)


def render_experiment_report_markdown(*args: Any, **kwargs: Any) -> Any:
    return _legacy_report().render_experiment_report_markdown(*args, **kwargs)


__all__ = [
    "build_experiment_report_export",
    "build_experiment_report_sections",
    "compare_experiment_history_runs",
    "extract_experiment_history_metrics",
    "format_report_money",
    "format_report_percent",
    "get_experiment_history_run",
    "initialize_experiment_history_store",
    "list_experiment_history_runs",
    "make_experiment_run_id",
    "normalize_experiment_history_run_type",
    "normalize_report_value",
    "render_experiment_report_markdown",
    "sanitize_experiment_history_result",
    "save_experiment_history_run",
]

