from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from src.backtesting import (
    reconstruct_point_in_time_covariance_matrix,
    reconstruct_point_in_time_time_dependent_risk_state,
)
from src.core.market_clock import (
    adjust_confidence_for_freshness,
    forecast_horizon_state,
    freshness_decay_weight,
    holding_horizon_state,
    information_age_seconds,
    normalize_time_risk_timestamp,
    time_dependent_risk_state,
    time_to_event_seconds,
)
from src.core.portfolio import (
    incremental_portfolio_risk,
    portfolio_exposure,
    portfolio_risk_summary,
)


def test_information_age_zero_and_positive_age() -> None:
    assert information_age_seconds(
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00Z",
    ) == pytest.approx(0.0, abs=1e-12)
    assert information_age_seconds(
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:10:00Z",
    ) == pytest.approx(600.0, abs=1e-12)


def test_information_age_is_timezone_safe() -> None:
    assert information_age_seconds(
        "2026-01-01T07:00:00-05:00",
        "2026-01-01T12:10:00Z",
    ) == pytest.approx(600.0, abs=1e-12)


def test_information_age_rejects_future_information_unless_explicitly_allowed() -> None:
    with pytest.raises(
        ValueError,
        match="information_available_at must be at or before evaluation_time.",
    ):
        information_age_seconds(
            "2026-01-01T12:11:00Z",
            "2026-01-01T12:10:00Z",
        )

    assert information_age_seconds(
        "2026-01-01T12:11:00Z",
        "2026-01-01T12:10:00Z",
        allow_negative=True,
    ) == pytest.approx(-60.0, abs=1e-12)


@pytest.mark.parametrize(
    "value",
    [
        "not-a-time",
        "",
        datetime(2026, 1, 1, 12, 0, 0),
        123,
        None,
    ],
)
def test_time_risk_timestamp_normalization_rejects_invalid_timestamps(value: object) -> None:
    with pytest.raises(ValueError, match="timestamp must"):
        normalize_time_risk_timestamp(value)


def test_time_risk_timestamp_normalization_returns_utc_timestamp() -> None:
    result = normalize_time_risk_timestamp("2026-01-01T07:00:00-05:00")

    assert result == datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_freshness_decay_half_life_values_are_hand_verifiable() -> None:
    assert freshness_decay_weight(0, half_life_seconds=600) == pytest.approx(1.0, abs=1e-12)
    assert freshness_decay_weight(600, half_life_seconds=600) == pytest.approx(0.5, abs=1e-12)
    assert freshness_decay_weight(1200, half_life_seconds=600) == pytest.approx(0.25, abs=1e-12)


def test_freshness_decay_is_monotonic_bounded_and_deterministic() -> None:
    weights = [freshness_decay_weight(age, half_life_seconds=600) for age in (0, 300, 600, 1200)]

    assert weights == sorted(weights, reverse=True)
    assert all(0.0 <= weight <= 1.0 for weight in weights)
    assert weights == [freshness_decay_weight(age, half_life_seconds=600) for age in (0, 300, 600, 1200)]


@pytest.mark.parametrize(
    ("age_seconds", "half_life_seconds", "message"),
    [
        (-1, 600, "age_seconds must be non-negative seconds."),
        (math.nan, 600, "age_seconds must not be NaN."),
        (math.inf, 600, "age_seconds must be finite."),
        (0, 0, "half_life_seconds must be positive seconds."),
        (0, -1, "half_life_seconds must be positive seconds."),
        (0, math.nan, "half_life_seconds must not be NaN."),
        (0, math.inf, "half_life_seconds must be finite."),
        (0, "bad", "half_life_seconds must be numeric."),
    ],
)
def test_freshness_decay_rejects_invalid_inputs(
    age_seconds: object,
    half_life_seconds: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        freshness_decay_weight(age_seconds, half_life_seconds=half_life_seconds)


def test_confidence_adjustment_preserves_base_confidence_and_applies_weight() -> None:
    result = adjust_confidence_for_freshness(0.8, 0.5)

    assert result["base_confidence"] == pytest.approx(0.8, abs=1e-12)
    assert result["freshness_weight"] == pytest.approx(0.5, abs=1e-12)
    assert result["effective_confidence"] == pytest.approx(0.4, abs=1e-12)
    assert result["confidence_scale"] == "unit"


def test_confidence_adjustment_supports_explicit_percent_scale() -> None:
    result = adjust_confidence_for_freshness(80.0, 0.5, confidence_scale="percent")

    assert result["base_confidence"] == pytest.approx(80.0, abs=1e-12)
    assert result["effective_confidence"] == pytest.approx(40.0, abs=1e-12)
    assert result["confidence_scale"] == "percent"


@pytest.mark.parametrize(
    ("base_confidence", "freshness_weight", "expected"),
    [
        (0.8, 1.0, 0.8),
        (0.0, 0.5, 0.0),
        (1.0, 0.25, 0.25),
    ],
)
def test_confidence_adjustment_handles_fresh_zero_and_maximum_confidence(
    base_confidence: float,
    freshness_weight: float,
    expected: float,
) -> None:
    result = adjust_confidence_for_freshness(base_confidence, freshness_weight)

    assert result["effective_confidence"] == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    ("base_confidence", "freshness_weight", "kwargs", "message"),
    [
        (-0.1, 0.5, {}, "base_confidence must be between 0 and 1."),
        (1.1, 0.5, {}, "base_confidence must be between 0 and 1."),
        (101.0, 0.5, {"confidence_scale": "percent"}, "base_confidence must be between 0 and 100."),
        (math.nan, 0.5, {}, "base_confidence must not be NaN."),
        (0.8, -0.1, {}, "freshness_weight must be between 0 and 1."),
        (0.8, 1.1, {}, "freshness_weight must be between 0 and 1."),
        (0.8, math.inf, {}, "freshness_weight must be finite."),
        (0.8, 0.5, {"confidence_scale": "bad"}, "confidence_scale must be 'unit' or 'percent'."),
    ],
)
def test_confidence_adjustment_rejects_invalid_inputs(
    base_confidence: object,
    freshness_weight: object,
    kwargs: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        adjust_confidence_for_freshness(base_confidence, freshness_weight, **kwargs)


def test_time_to_event_pre_boundary_and_post_event_states() -> None:
    pre_event = time_dependent_risk_state(
        evaluation_time="2026-01-01T12:00:00Z",
        information_available_at="2026-01-01T11:55:00Z",
        event_time="2026-01-01T13:00:00Z",
    )
    at_boundary = time_dependent_risk_state(
        evaluation_time="2026-01-01T13:00:00Z",
        information_available_at="2026-01-01T12:55:00Z",
        event_time="2026-01-01T13:00:00Z",
    )
    post_event = time_dependent_risk_state(
        evaluation_time="2026-01-01T13:01:00Z",
        information_available_at="2026-01-01T12:55:00Z",
        event_time="2026-01-01T13:00:00Z",
    )

    assert pre_event["time_to_event_seconds"] == pytest.approx(3600.0, abs=1e-12)
    assert pre_event["event_state"] == "pre_event"
    assert at_boundary["time_to_event_seconds"] == pytest.approx(0.0, abs=1e-12)
    assert at_boundary["event_state"] == "at_event_boundary"
    assert post_event["time_to_event_seconds"] == pytest.approx(-60.0, abs=1e-12)
    assert post_event["event_state"] == "post_event"


def test_time_to_event_is_timezone_safe() -> None:
    assert time_to_event_seconds(
        "2026-01-01T08:00:00-05:00",
        "2026-01-01T12:00:00Z",
    ) == pytest.approx(3600.0, abs=1e-12)


def test_holding_horizon_representation_is_metadata_only() -> None:
    numeric = holding_horizon_state(3600)
    duration = holding_horizon_state(timedelta(minutes=30))

    assert numeric["holding_horizon_seconds"] == pytest.approx(3600.0, abs=1e-12)
    assert numeric["holding_horizon_unit"] == "seconds"
    assert numeric["risk_scaling_applied"] is False
    assert numeric["scaling_assumption"] == "none"
    assert duration["holding_horizon_seconds"] == pytest.approx(1800.0, abs=1e-12)


@pytest.mark.parametrize("value", [0, -1, math.nan, math.inf, "bad"])
def test_holding_horizon_rejects_invalid_duration(value: object) -> None:
    with pytest.raises(ValueError):
        holding_horizon_state(value)


def test_forecast_horizon_representation_preserves_horizon_without_calibration() -> None:
    result = forecast_horizon_state(7 * 24 * 60 * 60)

    assert result["forecast_horizon_seconds"] == pytest.approx(604800.0, abs=1e-12)
    assert result["forecast_horizon_unit"] == "seconds"
    assert result["calibration_assumption"] == "none"


@pytest.mark.parametrize("value", [0, -1, math.nan, math.inf, "bad"])
def test_forecast_horizon_rejects_invalid_duration(value: object) -> None:
    with pytest.raises(ValueError):
        forecast_horizon_state(value)


def test_time_dependent_risk_state_exposes_reproducible_metadata() -> None:
    result = time_dependent_risk_state(
        evaluation_time="2026-01-01T12:10:00Z",
        information_available_at="2026-01-01T12:00:00Z",
        event_time="2026-01-01T13:00:00Z",
        holding_horizon_seconds=1800,
        forecast_horizon_seconds=7200,
        freshness_half_life_seconds=600,
        base_confidence=0.8,
    )

    assert result["status"] == "ready"
    assert result["evaluation_time"] == "2026-01-01T12:10:00Z"
    assert result["information_available_at"] == "2026-01-01T12:00:00Z"
    assert result["information_age_seconds"] == pytest.approx(600.0, abs=1e-12)
    assert result["freshness_model"] == "exponential_half_life"
    assert result["freshness_weight"] == pytest.approx(0.5, abs=1e-12)
    assert result["base_confidence"] == pytest.approx(0.8, abs=1e-12)
    assert result["effective_confidence"] == pytest.approx(0.4, abs=1e-12)
    assert result["time_to_event_seconds"] == pytest.approx(3000.0, abs=1e-12)
    assert result["holding_horizon_seconds"] == pytest.approx(1800.0, abs=1e-12)
    assert result["forecast_horizon_seconds"] == pytest.approx(7200.0, abs=1e-12)
    assert result["exposure_mutation_applied"] is False


def test_time_dependent_risk_state_without_half_life_preserves_confidence() -> None:
    result = time_dependent_risk_state(
        evaluation_time="2026-01-01T12:10:00Z",
        information_available_at="2026-01-01T12:00:00Z",
        base_confidence=0.8,
    )

    assert result["freshness_weight"] is None
    assert result["effective_confidence"] == pytest.approx(0.8, abs=1e-12)
    assert result["confidence_adjustment_applied"] is False


def test_time_dependent_risk_state_rejects_invalid_confidence_scale_without_confidence() -> None:
    with pytest.raises(ValueError, match="confidence_scale must be 'unit' or 'percent'."):
        time_dependent_risk_state(
            evaluation_time="2026-01-01T12:10:00Z",
            information_available_at="2026-01-01T12:00:00Z",
            confidence_scale="bad",
        )


def test_point_in_time_time_dependent_state_uses_latest_eligible_observation() -> None:
    observations = [
        {
            "available_at": "2026-01-01T12:00:00Z",
            "event_time": "2026-01-01T13:00:00Z",
            "base_confidence": 0.8,
        },
        {
            "available_at": "2026-01-01T12:20:00Z",
            "event_time": "2026-01-01T13:00:00Z",
            "base_confidence": 1.0,
        },
    ]

    result = reconstruct_point_in_time_time_dependent_risk_state(
        observations,
        cutoff_time="2026-01-01T12:10:00Z",
        freshness_half_life_seconds=600,
    )

    assert result["ok"] is True
    assert result["selected_observation_index"] == 0
    assert result["eligible_observation_count"] == 1
    assert result["state"]["information_age_seconds"] == pytest.approx(600.0, abs=1e-12)
    assert result["state"]["freshness_weight"] == pytest.approx(0.5, abs=1e-12)
    assert result["state"]["effective_confidence"] == pytest.approx(0.4, abs=1e-12)


def test_point_in_time_time_dependent_state_includes_exact_cutoff_observation() -> None:
    observations = [
        {"available_at": "2026-01-01T12:00:00Z", "base_confidence": 0.5},
        {"available_at": "2026-01-01T12:20:00Z", "base_confidence": 0.9},
    ]

    result = reconstruct_point_in_time_time_dependent_risk_state(
        observations,
        cutoff_time="2026-01-01T12:20:00Z",
        freshness_half_life_seconds=600,
    )

    assert result["selected_observation_index"] == 1
    assert result["state"]["information_age_seconds"] == pytest.approx(0.0, abs=1e-12)
    assert result["state"]["effective_confidence"] == pytest.approx(0.9, abs=1e-12)


def test_point_in_time_time_dependent_state_reports_no_eligible_information() -> None:
    result = reconstruct_point_in_time_time_dependent_risk_state(
        [{"available_at": "2026-01-01T12:00:00Z", "base_confidence": 0.5}],
        cutoff_time="2026-01-01T11:59:00Z",
        freshness_half_life_seconds=600,
    )

    assert result == {
        "ok": False,
        "status": "no_eligible_information",
        "cutoff_time": "2026-01-01T11:59:00Z",
        "cutoff_policy": "information_available_at <= cutoff_time",
        "eligible_observation_count": 0,
        "selected_observation_index": None,
        "point_in_time_safe": True,
        "state": None,
        "value": None,
    }


def test_point_in_time_time_dependent_state_is_invariant_to_future_mutation() -> None:
    baseline_observations = [
        {"available_at": "2026-01-01T12:00:00Z", "base_confidence": 0.8},
        {"available_at": "2026-01-01T12:20:00Z", "base_confidence": 1.0},
    ]
    mutated_observations = [
        {"available_at": "2026-01-01T12:00:00Z", "base_confidence": 0.8},
        {"available_at": "2026-01-01T12:20:00Z", "base_confidence": 0.0},
    ]

    first = reconstruct_point_in_time_time_dependent_risk_state(
        baseline_observations,
        cutoff_time="2026-01-01T12:10:00Z",
        freshness_half_life_seconds=600,
    )
    second = reconstruct_point_in_time_time_dependent_risk_state(
        mutated_observations,
        cutoff_time="2026-01-01T12:10:00Z",
        freshness_half_life_seconds=600,
    )

    assert first == second


def test_point_in_time_time_dependent_state_is_invariant_to_future_additions() -> None:
    baseline_observations = [
        {"available_at": "2026-01-01T12:00:00Z", "base_confidence": 0.8},
        {"available_at": "2026-01-01T12:20:00Z", "base_confidence": 1.0},
    ]
    extended_observations = [
        *baseline_observations,
        {"available_at": "2026-01-01T12:30:00Z", "base_confidence": 0.1},
    ]

    first = reconstruct_point_in_time_time_dependent_risk_state(
        baseline_observations,
        cutoff_time="2026-01-01T12:10:00Z",
        freshness_half_life_seconds=600,
    )
    second = reconstruct_point_in_time_time_dependent_risk_state(
        extended_observations,
        cutoff_time="2026-01-01T12:10:00Z",
        freshness_half_life_seconds=600,
    )

    assert first == second


def test_point_in_time_time_dependent_state_is_repeatedly_deterministic() -> None:
    observations = [{"available_at": "2026-01-01T12:00:00Z", "base_confidence": 0.8}]
    kwargs = {
        "observations": observations,
        "cutoff_time": "2026-01-01T12:10:00Z",
        "freshness_half_life_seconds": 600,
    }

    assert reconstruct_point_in_time_time_dependent_risk_state(**kwargs) == (
        reconstruct_point_in_time_time_dependent_risk_state(**kwargs)
    )


def test_point_in_time_time_dependent_state_rejects_unordered_observations() -> None:
    with pytest.raises(
        ValueError,
        match="observations must be ordered by information availability without internal resorting.",
    ):
        reconstruct_point_in_time_time_dependent_risk_state(
            [
                {"available_at": "2026-01-01T12:20:00Z"},
                {"available_at": "2026-01-01T12:00:00Z"},
            ],
            cutoff_time="2026-01-01T12:30:00Z",
        )


def test_point_in_time_time_dependent_state_rejects_invalid_observations() -> None:
    with pytest.raises(ValueError, match="observations\\[0\\] must be a mapping."):
        reconstruct_point_in_time_time_dependent_risk_state(
            ["not-a-mapping"],  # type: ignore[list-item]
            cutoff_time="2026-01-01T12:30:00Z",
        )
    with pytest.raises(ValueError, match="observations\\[0\\] must contain available_at."):
        reconstruct_point_in_time_time_dependent_risk_state(
            [{}],
            cutoff_time="2026-01-01T12:30:00Z",
        )


def test_generic_worldview_timestamp_names_can_reuse_point_in_time_state() -> None:
    result = reconstruct_point_in_time_time_dependent_risk_state(
        [
            {
                "source_published_at": "2026-01-01T11:58:00Z",
                "ingested_at": "2026-01-01T11:59:00Z",
                "parsed_at": "2026-01-01T11:59:30Z",
                "validated_at": "2026-01-01T11:59:45Z",
                "canonical_available_at": "2026-01-01T12:00:00Z",
                "confidence_score": 80.0,
            }
        ],
        cutoff_time="2026-01-01T12:10:00Z",
        information_time_field="canonical_available_at",
        base_confidence_field="confidence_score",
        event_time_field=None,
        confidence_scale="percent",
        freshness_half_life_seconds=600,
    )

    assert result["ok"] is True
    assert result["state"]["information_available_at"] == "2026-01-01T12:00:00Z"
    assert result["state"]["base_confidence"] == pytest.approx(80.0, abs=1e-12)
    assert result["state"]["effective_confidence"] == pytest.approx(40.0, abs=1e-12)
    assert result["state"]["event_time"] is None


def test_portfolio_compatibility_keeps_covariance_exposure_and_incremental_risk_unchanged() -> None:
    covariance_result = reconstruct_point_in_time_covariance_matrix(
        {
            "A": [1.0, 2.0, 3.0, 1000.0],
            "B": [1.0, 2.0, 3.0, -1000.0],
        },
        [
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            "2026-01-03T00:00:00Z",
            "2026-01-04T00:00:00Z",
        ],
        cutoff_time="2026-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )
    positions = {"A": 100.0, "B": 100.0}
    exposure_before = portfolio_exposure(positions)
    risk_before = portfolio_risk_summary(positions, covariance_result["matrix"])

    metadata = time_dependent_risk_state(
        evaluation_time="2026-01-03T00:00:00Z",
        information_available_at="2026-01-02T23:50:00Z",
        event_time="2026-01-03T01:00:00Z",
        freshness_half_life_seconds=600,
        base_confidence=0.8,
    )
    incremental = incremental_portfolio_risk(
        {"A": 100.0},
        "B",
        100.0,
        covariance_result["matrix"],
    )
    risk_package = {
        "portfolio_risk": risk_before,
        "incremental_portfolio_risk": incremental,
        "time_dependent_risk": metadata,
    }

    assert portfolio_exposure(positions) == exposure_before
    assert portfolio_risk_summary(positions, covariance_result["matrix"]) == risk_before
    assert risk_package["time_dependent_risk"]["exposure_mutation_applied"] is False
    assert risk_package["incremental_portfolio_risk"]["proposed_portfolio_risk"] == pytest.approx(
        risk_before["portfolio_volatility"],
        abs=1e-12,
    )
