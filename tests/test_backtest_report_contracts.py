from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from src.analytics.governance import build_calibration_summary
from src.backtesting.backtest_report_contracts import (
    BACKTEST_REPORT_SCHEMA_VERSION,
    BacktestPerformanceBucketContract,
    BacktestReportContract,
)


CREATED_AT = "2026-07-12T12:00:00Z"
EVALUATION_START = "2026-07-01T00:00:00Z"
EVALUATION_END = "2026-07-31T00:00:00Z"


def _bucket(label: str, **overrides: object) -> BacktestPerformanceBucketContract:
    payload: dict[str, object] = {
        "label": label,
        "sample_size": 4,
        "wins": 2,
        "losses": 1,
        "pushes": 1,
        "roi_percent": 3.5,
        "brier_score": 0.21,
        "log_loss": 0.58,
        "calibration_summary": {"label": f"{label}_calibration", "sample_count": 4},
        "drawdown_summary": {"max_drawdown_percent": 2.5},
        "warnings": ("bucket_warning",),
        "metadata": {"bucket": label},
    }
    payload.update(overrides)
    return BacktestPerformanceBucketContract(**payload)


def _report(**overrides: object) -> BacktestReportContract:
    payload: dict[str, object] = {
        "experiment_id": "exp_backtest_123",
        "report_version": BACKTEST_REPORT_SCHEMA_VERSION,
        "created_at": CREATED_AT,
        "evaluation_start": EVALUATION_START,
        "evaluation_end": EVALUATION_END,
        "total_decisions": 12,
        "eligible_decisions": 10,
        "rejected_decisions": 2,
        "wins": 6,
        "losses": 3,
        "pushes": 1,
        "sample_size": 10,
        "roi_percent": 4.25,
        "brier_score": 0.18,
        "log_loss": 0.53,
        "calibration_summary": build_calibration_summary(
            label="calibration",
            sample_count=10,
            calibration_error=0.04,
            calibration_score=0.96,
            buckets={"0.0-0.1": 0.6, "0.1-0.2": 0.4},
        ),
        "drawdown_summary": {"max_drawdown_percent": 7.4, "recovery_need": 0.25},
        "performance_by_season": {
            "2025": _bucket("2025", sample_size=4, wins=2, losses=1, pushes=1, roi_percent=2.5),
            "2024": _bucket("2024", sample_size=6, wins=4, losses=1, pushes=1, roi_percent=5.0),
        },
        "performance_by_market": {
            "moneyline": {
                "sample_size": 5,
                "wins": 3,
                "losses": 1,
                "pushes": 1,
                "roi_percent": 4.0,
            }
        },
        "performance_by_edge_bucket": [
            ("0-2", {"sample_size": 3, "wins": 2, "losses": 1, "pushes": 0, "roi_percent": 6.0}),
        ],
        "rejection_reasons": {"missing_line": 2, "late_data": 1},
        "missingness_summary": {"closing_odds": 2, "market_implied_probability": 1},
        "warnings": ["needs_follow_up", "low_sample", "needs_follow_up"],
        "metrics_reference": "data/metrics/exp_backtest_123.json",
        "artifact_reference": {"uri": "artifacts/exp_backtest_123.tar.gz"},
    }
    payload.update(overrides)
    return BacktestReportContract(**payload)


class _UnsupportedSummaryObject:
    def as_dict(self) -> dict[str, object]:
        return {"label": "unsupported"}


def test_backtest_performance_bucket_contract_round_trips() -> None:
    bucket = _bucket("2024")

    expected_json = json.dumps(bucket.as_dict(), indent=2, sort_keys=True, ensure_ascii=False)
    assert bucket.to_json() == expected_json
    assert BacktestPerformanceBucketContract.from_json(bucket.to_json()) == bucket
    assert bucket.as_dict()["warnings"] == ["bucket_warning"]


def test_backtest_report_contract_valid_construction_and_round_trip() -> None:
    report = _report()

    assert report.experiment_id == "exp_backtest_123"
    assert report.report_version == BACKTEST_REPORT_SCHEMA_VERSION
    assert report.calibration_summary["sample_count"] == 10
    assert report.metrics_reference == {"uri": "data/metrics/exp_backtest_123.json"}
    assert report.artifact_reference == {"uri": "artifacts/exp_backtest_123.tar.gz"}
    assert report.warnings == ("low_sample", "needs_follow_up")
    assert list(report.as_dict()["performance_by_season"]) == ["2024", "2025"]
    assert list(report.as_dict()["rejection_reasons"]) == ["late_data", "missing_line"]
    assert list(report.as_dict()["missingness_summary"]) == ["closing_odds", "market_implied_probability"]

    expected_json = json.dumps(report.as_dict(), indent=2, sort_keys=True, ensure_ascii=False)
    assert report.to_json() == expected_json
    assert BacktestReportContract.from_json(report.to_json()) == report


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {"total_decisions": -1},
            "total_decisions",
        ),
        (
            {"eligible_decisions": 9, "rejected_decisions": 2},
            "must equal total_decisions",
        ),
        (
            {"sample_size": 9},
            "sample_size",
        ),
        (
            {"evaluation_start": EVALUATION_END, "evaluation_end": EVALUATION_START},
            "evaluation_end",
        ),
    ],
)
def test_backtest_report_contract_rejects_invalid_counts_and_date_ranges(
    payload: dict[str, object],
    message: str,
) -> None:
    base = {
        "experiment_id": "exp_backtest_123",
        "report_version": BACKTEST_REPORT_SCHEMA_VERSION,
        "created_at": CREATED_AT,
        "evaluation_start": EVALUATION_START,
        "evaluation_end": EVALUATION_END,
        "total_decisions": 12,
        "eligible_decisions": 10,
        "rejected_decisions": 2,
        "wins": 6,
        "losses": 3,
        "pushes": 1,
        "sample_size": 10,
        "roi_percent": 4.25,
    }
    base.update(payload)

    with pytest.raises((TypeError, ValueError), match=message):
        BacktestReportContract(**base)

    with pytest.raises(ValueError, match="sample_size"):
        BacktestPerformanceBucketContract(
            label="bad_bucket",
            sample_size=1,
            wins=1,
            losses=1,
            pushes=0,
            roi_percent=0.0,
            )


@pytest.mark.parametrize(
    ("factory", "field_name", "value", "message"),
    [
        (_report, "roi_percent", float("inf"), "roi_percent"),
        (_report, "brier_score", 1.1, "brier_score"),
        (_report, "log_loss", -0.1, "log_loss"),
        (_bucket, "roi_percent", float("inf"), "roi_percent"),
        (_bucket, "brier_score", -0.1, "brier_score"),
        (_bucket, "log_loss", -0.1, "log_loss"),
    ],
)
def test_backtest_report_contract_rejects_invalid_probability_and_percentage_ranges(
    factory,
    field_name: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        if factory is _report:
            factory(**{field_name: value})
        else:
            factory("range_case", **{field_name: value})


def test_backtest_report_contract_rejects_invalid_report_version() -> None:
    with pytest.raises(ValueError, match="report_version"):
        _report(report_version="src.backtesting.backtest_report_contracts.v2")


def test_backtest_report_contract_is_frozen_and_nested_mappings_are_read_only() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.total_decisions = 99  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.performance_by_market[0].roi_percent = 99.0  # type: ignore[misc]

    with pytest.raises(TypeError):
        report.metrics_reference["extra"] = "value"


def test_backtest_report_contract_distinguishes_missing_and_zero_metrics() -> None:
    missing_report = _report(brier_score=None, log_loss=None)
    zero_report = _report(brier_score=0.0, log_loss=0.0)

    missing_payload = missing_report.as_dict()
    zero_payload = zero_report.as_dict()

    assert missing_payload["brier_score"] is None
    assert missing_payload["log_loss"] is None
    assert zero_payload["brier_score"] == 0.0
    assert zero_payload["log_loss"] == 0.0
    assert missing_report.metrics_reference == {"uri": "data/metrics/exp_backtest_123.json"}
    assert zero_report.artifact_reference == {"uri": "artifacts/exp_backtest_123.tar.gz"}


def test_backtest_report_contract_rejects_unsupported_summary_objects() -> None:
    with pytest.raises(TypeError, match="calibration_summary"):
        _report(calibration_summary=_UnsupportedSummaryObject())

    with pytest.raises(TypeError, match="performance_by_market"):
        _report(performance_by_market=[("moneyline", _UnsupportedSummaryObject())])


def test_backtest_report_contract_serialization_is_stable() -> None:
    report = _report()

    serialized_once = report.to_json()
    serialized_twice = report.to_json()

    assert serialized_once == serialized_twice
    assert serialized_once == json.dumps(report.as_dict(), indent=2, sort_keys=True, ensure_ascii=False)
