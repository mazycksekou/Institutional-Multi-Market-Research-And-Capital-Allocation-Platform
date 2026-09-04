from __future__ import annotations

"""Canonical Phase 5.5 baseline backtesting from certified decision rows."""

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.analytics.governance import build_calibration_summary
from src.backtesting.backtest_report_contracts import (
    BACKTEST_REPORT_SCHEMA_VERSION,
    BacktestPerformanceBucketContract,
    BacktestReportContract,
)
from src.core.math_utils import (
    ewma_correlation,
    ewma_covariance,
    rolling_correlation,
    rolling_covariance,
)
from src.backtesting.decision_row_population import (
    DEFAULT_DECISION_DATASET_ID,
    DEFAULT_DECISION_RESEARCH_ASSET_ID,
    build_decision_row_population_dashboard_snapshot,
)
from src.data.data_paths import get_runtime_data_path
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


BASELINE_BACKTEST_SCHEMA_VERSION = "src.backtesting.baseline_backtesting.v1"
BASELINE_BACKTEST_TRANSFORMATION_VERSION = "phase5.5.baseline_backtesting.v1"
DEFAULT_BASELINE_BACKTEST_DATASET_ID = "dataset.sports.nfl.baseline_backtests"
DEFAULT_BASELINE_BACKTEST_DATASET_NAME = "nfl_baseline_backtests"
DEFAULT_BASELINE_BACKTEST_OWNER = "src.backtesting"
DEFAULT_BASELINE_BACKTEST_STORAGE_PATH = get_runtime_data_path(
    "baseline_backtesting",
    "canonical_data.sqlite",
)
DEFAULT_BASELINE_BACKTEST_STRATEGY_NAME = "phase5.5.certified_decision_replay"
DEFAULT_BASELINE_BACKTEST_MARKET = "sports:nfl"
DEFAULT_BASELINE_BACKTEST_MARKET_TYPE = "historical_backtest"
DEFAULT_UNIT_STAKE = 1.0
RECOMMENDED_MIN_SAMPLE_SIZE = 30
BACKTEST_ROW_TABLE = "backtest_rows"
BACKTEST_RUN_TABLE = "backtest_runs"

SIGNAL_CONSENSUS_PROBABILITY_ID = "signal.sports.market.consensus_probability"
SIGNAL_PRICING_GAP_ID = "signal.sports.market.pricing_gap"
SIGNAL_FAIR_AMERICAN_ODDS_ID = "signal.sports.market.fair_american_odds"
SIGNAL_FAIR_DECIMAL_ODDS_ID = "signal.sports.market.fair_decimal_odds"
SIGNAL_CONFIDENCE_SCORE_ID = "signal.sports.data_quality.confidence_score"
SIGNAL_CONFIDENCE_GRADE_ID = "signal.sports.data_quality.confidence_grade"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return float(default)
        return result
    except (TypeError, ValueError):
        return float(default)


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _parse_iso(value: Any) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.replace(microsecond=0)


def _to_iso8601_utc(value: Any) -> str:
    parsed = _parse_iso(value)
    if parsed is None:
        return _normalize_text(value)
    return (
        parsed.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, tuple):
            return list(obj)
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _load_json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): payload for key, payload in value.items()}
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return {str(key): payload for key, payload in parsed.items()}
    return {}


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _clamp_probability(value: Any) -> float | None:
    if value in (None, ""):
        return None
    candidate = _normalize_float(value, float("nan"))
    if math.isnan(candidate) or math.isinf(candidate):
        return None
    return min(max(candidate, 1e-6), 1.0 - 1e-6)


def _resolve_target_team_id(payload: Mapping[str, Any]) -> str:
    return _normalize_text(
        payload.get("target_team_id")
        or payload.get("home_team_id")
        or payload.get("away_team_id")
    )


def _resolve_opponent_team_id(
    payload: Mapping[str, Any],
    *,
    target_team_id: str | None = None,
) -> str:
    target = _normalize_text(target_team_id or payload.get("target_team_id"))
    opponent = _normalize_text(payload.get("opponent_team_id"))
    if opponent:
        return opponent
    home_team_id = _normalize_text(payload.get("home_team_id"))
    away_team_id = _normalize_text(payload.get("away_team_id"))
    if target and target == home_team_id and away_team_id:
        return away_team_id
    if target and target == away_team_id and home_team_id:
        return home_team_id
    return _normalize_text(away_team_id or home_team_id)


def _resolve_artifact_root(
    storage_path: Path,
    artifact_root: str | Path | None,
) -> Path:
    if artifact_root is not None:
        root = Path(artifact_root).expanduser().resolve()
    else:
        root = storage_path.resolve().parent / "baseline_backtesting_artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _decision_row_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _normalize_text(row.get("decision_cutoff_time")),
        _normalize_text(row.get("dataset_row_id")),
        _normalize_text(row.get("decision_id")),
        _normalize_text(row.get("snapshot_id")),
    )


def _decimal_from_american(american_odds: Any) -> float:
    odds = _normalize_float(american_odds, 0.0)
    if odds == 0.0:
        return 0.0
    if odds > 0:
        return round(1.0 + (odds / 100.0), 6)
    return round(1.0 + (100.0 / abs(odds)), 6)


def _profit_loss_units(*, decimal_odds: float, actual_outcome: float, push_flag: bool) -> float:
    if push_flag:
        return 0.0
    if actual_outcome >= 1.0:
        return round(decimal_odds - 1.0, 6)
    return -1.0


def _brier_score(probability: float | None, actual_outcome: float | None) -> float | None:
    if probability is None or actual_outcome is None:
        return None
    return round((probability - actual_outcome) ** 2, 6)


def _log_loss(probability: float | None, actual_outcome: float | None) -> float | None:
    if probability is None or actual_outcome is None:
        return None
    p = _clamp_probability(probability)
    if p is None:
        return None
    actual = 1.0 if actual_outcome >= 1.0 else 0.0
    loss = -(actual * math.log(p) + (1.0 - actual) * math.log(1.0 - p))
    return round(loss, 6)


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _market_selection_context(
    decision_row: Mapping[str, Any],
    dataset_row: Mapping[str, Any],
) -> dict[str, Any]:
    decision_context = _load_json_mapping(decision_row.get("decision_context_json"))
    signal_context = _load_json_mapping(decision_context.get("source_signal_context"))
    target_team_id = _resolve_target_team_id(dataset_row or signal_context or decision_row)
    opponent_team_id = _resolve_opponent_team_id(
        dataset_row or signal_context or decision_row,
        target_team_id=target_team_id,
    )
    return {
        "market_type": _normalize_text(
            dataset_row.get("market_type")
            or signal_context.get("market_type")
            or decision_context.get("market_type")
        ),
        "selection": _normalize_text(
            dataset_row.get("selection")
            or signal_context.get("selection")
            or decision_row.get("selection")
        ),
        "book": _normalize_text(
            dataset_row.get("book")
            or signal_context.get("book")
            or decision_row.get("book"),
            "consensus",
        ),
        "target_team_id": target_team_id,
        "opponent_team_id": opponent_team_id,
        "home_team_id": _normalize_text(
            dataset_row.get("home_team_id")
            or signal_context.get("home_team_id")
            or decision_row.get("home_team_id")
        ),
        "away_team_id": _normalize_text(
            dataset_row.get("away_team_id")
            or signal_context.get("away_team_id")
            or decision_row.get("away_team_id")
        ),
        "home_team": _normalize_text(
            dataset_row.get("home_team")
            or signal_context.get("home_team")
            or decision_row.get("home_team")
        ),
        "away_team": _normalize_text(
            dataset_row.get("away_team")
            or signal_context.get("away_team")
            or decision_row.get("away_team")
        ),
        "signal_context": signal_context,
        "decision_context": decision_context,
    }


def _settle_market(
    market_context: Mapping[str, Any],
    dataset_row: Mapping[str, Any],
) -> dict[str, Any]:
    market_type = _normalize_text(market_context.get("market_type")).lower()
    selection = _normalize_text(market_context.get("selection")).lower()
    label_settlement_status = _normalize_text(
        dataset_row.get("label_settlement_status"),
        "unsettled",
    )
    if label_settlement_status != "settled":
        return {
            "settlement_status": label_settlement_status,
            "outcome_status": "unsettled",
            "actual_outcome": None,
            "push_flag": False,
            "resolution_detail": "unsettled_result",
        }

    label_margin = _normalize_float(dataset_row.get("label_margin"), 0.0)
    label_total_points = _normalize_float(dataset_row.get("label_total_points"), 0.0)
    label_winner_team_id = _normalize_text(dataset_row.get("label_winner_team_id"))
    line_value = _normalize_float(dataset_row.get("line_value"), 0.0)
    home_team_id = _normalize_text(market_context.get("home_team_id"))
    away_team_id = _normalize_text(market_context.get("away_team_id"))
    target_team_id = _normalize_text(market_context.get("target_team_id"))

    if market_type == "moneyline":
        picked_team_id = target_team_id
        if selection == "home":
            picked_team_id = home_team_id
        elif selection == "away":
            picked_team_id = away_team_id
        actual_outcome = 1.0 if picked_team_id and picked_team_id == label_winner_team_id else 0.0
        return {
            "settlement_status": label_settlement_status,
            "outcome_status": "win" if actual_outcome >= 1.0 else "loss",
            "actual_outcome": actual_outcome,
            "push_flag": False,
            "resolution_detail": f"winner={label_winner_team_id}",
        }

    if market_type == "spread":
        effective_target_team_id = target_team_id or home_team_id
        target_margin = label_margin if effective_target_team_id == home_team_id else -label_margin
        adjusted_margin = round(target_margin + line_value, 6)
        if abs(adjusted_margin) <= 1e-9:
            return {
                "settlement_status": label_settlement_status,
                "outcome_status": "push",
                "actual_outcome": 0.0,
                "push_flag": True,
                "resolution_detail": f"adjusted_margin={adjusted_margin}",
            }
        actual_outcome = 1.0 if adjusted_margin > 0 else 0.0
        return {
            "settlement_status": label_settlement_status,
            "outcome_status": "win" if actual_outcome >= 1.0 else "loss",
            "actual_outcome": actual_outcome,
            "push_flag": False,
            "resolution_detail": f"adjusted_margin={adjusted_margin}",
        }

    if market_type == "total":
        adjusted_total = round(label_total_points - line_value, 6)
        if abs(adjusted_total) <= 1e-9:
            return {
                "settlement_status": label_settlement_status,
                "outcome_status": "push",
                "actual_outcome": 0.0,
                "push_flag": True,
                "resolution_detail": f"adjusted_total={adjusted_total}",
            }
        is_over = selection == "over"
        actual_outcome = 1.0 if (adjusted_total > 0 and is_over) or (adjusted_total < 0 and not is_over) else 0.0
        return {
            "settlement_status": label_settlement_status,
            "outcome_status": "win" if actual_outcome >= 1.0 else "loss",
            "actual_outcome": actual_outcome,
            "push_flag": False,
            "resolution_detail": f"adjusted_total={adjusted_total}",
        }

    return {
        "settlement_status": label_settlement_status,
        "outcome_status": "rejected",
        "actual_outcome": None,
        "push_flag": False,
        "resolution_detail": f"unsupported_market_type:{market_type or 'missing'}",
    }


def _point_in_time_validation(
    decision_row: Mapping[str, Any],
    dataset_row: Mapping[str, Any],
    market_context: Mapping[str, Any],
) -> dict[str, Any]:
    decision_cutoff = _parse_iso(decision_row.get("decision_cutoff_time"))
    scheduled_kickoff = _parse_iso(decision_row.get("scheduled_kickoff_time"))
    dataset_cutoff = _parse_iso(dataset_row.get("decision_cutoff_time"))
    dataset_kickoff = _parse_iso(dataset_row.get("scheduled_kickoff_time"))
    settlement_recorded = _parse_iso(dataset_row.get("label_result_recorded_time"))
    signal_context = _load_json_mapping(market_context.get("signal_context"))

    checks = {
        "decision_row_safe": _normalize_text(decision_row.get("point_in_time_status")) == "safe",
        "decision_cutoff_before_kickoff": bool(
            decision_cutoff is not None
            and scheduled_kickoff is not None
            and decision_cutoff <= scheduled_kickoff
        ),
        "dataset_cutoff_before_kickoff": bool(
            dataset_cutoff is not None
            and dataset_kickoff is not None
            and dataset_cutoff <= dataset_kickoff
        ),
        "decision_cutoff_matches_dataset": bool(
            decision_cutoff is not None
            and dataset_cutoff is not None
            and decision_cutoff == dataset_cutoff
        ),
        "kickoff_matches_dataset": bool(
            scheduled_kickoff is not None
            and dataset_kickoff is not None
            and scheduled_kickoff == dataset_kickoff
        ),
        "settlement_after_cutoff": bool(
            settlement_recorded is not None
            and decision_cutoff is not None
            and settlement_recorded > decision_cutoff
        ),
        "signal_context_matches_dataset_market": _normalize_text(
            signal_context.get("market_type")
        ) == _normalize_text(dataset_row.get("market_type")),
        "signal_context_matches_dataset_selection": _normalize_text(
            signal_context.get("selection")
        ) == _normalize_text(dataset_row.get("selection")),
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
    }


def _ordered_observation_timestamps(
    observation_timestamps: Sequence[Any],
    *,
    expected_count: int,
) -> list[datetime]:
    timestamps = list(observation_timestamps)
    if len(timestamps) != expected_count:
        raise ValueError("observation_timestamps must have the same length as the observation series.")

    parsed: list[datetime] = []
    previous: datetime | None = None
    for index, value in enumerate(timestamps):
        timestamp = _parse_iso(value)
        if timestamp is None:
            raise ValueError(f"observation_timestamps[{index}] must be a valid ISO-8601 timestamp.")
        if previous is not None and timestamp < previous:
            raise ValueError("observation_timestamps must be ordered ascending without internal resorting.")
        parsed.append(timestamp)
        previous = timestamp
    return parsed


def _point_in_time_series(
    x: Sequence[float],
    y: Sequence[float],
    observation_timestamps: Sequence[Any],
    *,
    cutoff_time: Any,
) -> tuple[list[float], list[float], list[datetime], str]:
    x_values = list(x)
    y_values = list(y)
    if len(x_values) != len(y_values):
        raise ValueError("Series must have the same length.")

    cutoff = _parse_iso(cutoff_time)
    if cutoff is None:
        raise ValueError("cutoff_time must be a valid ISO-8601 timestamp.")

    timestamps = _ordered_observation_timestamps(
        observation_timestamps,
        expected_count=len(x_values),
    )
    eligible_indexes = [index for index, timestamp in enumerate(timestamps) if timestamp <= cutoff]
    filtered_x = [x_values[index] for index in eligible_indexes]
    filtered_y = [y_values[index] for index in eligible_indexes]
    filtered_timestamps = [timestamps[index] for index in eligible_indexes]
    return filtered_x, filtered_y, filtered_timestamps, _to_iso8601_utc(cutoff)


def _point_in_time_result(
    *,
    metric: str,
    estimator: str,
    cutoff_time: str,
    included_observation_count: int,
    total_observation_count: int,
    estimator_parameters: Mapping[str, Any],
    value: float | None,
) -> dict[str, Any]:
    return {
        "ok": value is not None,
        "status": "ready" if value is not None else "insufficient_history",
        "metric": metric,
        "estimator": estimator,
        "cutoff_time": cutoff_time,
        "included_observation_count": included_observation_count,
        "excluded_future_observation_count": max(0, total_observation_count - included_observation_count),
        "point_in_time_safe": True,
        "estimator_parameters": dict(estimator_parameters),
        "value": value,
    }


def reconstruct_point_in_time_covariance(
    x: Sequence[float],
    y: Sequence[float],
    observation_timestamps: Sequence[Any],
    *,
    cutoff_time: Any,
    estimator: str,
    min_periods: int,
    window: int | None = None,
    ddof: int = 1,
    alpha: float | None = None,
) -> dict[str, Any]:
    """Reconstruct the covariance available at a historical cutoff.

    The caller is responsible for supplying already-aligned observations in
    chronological order. This function owns cutoff exclusion only.
    """
    filtered_x, filtered_y, filtered_timestamps, normalized_cutoff = _point_in_time_series(
        x,
        y,
        observation_timestamps,
        cutoff_time=cutoff_time,
    )
    estimator_key = _normalize_text(estimator).lower()
    if estimator_key == "rolling":
        if window is None:
            raise ValueError("window is required for rolling point-in-time covariance.")
        series = rolling_covariance(
            filtered_x,
            filtered_y,
            window=window,
            min_periods=min_periods,
            ddof=ddof,
        )
        return _point_in_time_result(
            metric="covariance",
            estimator="rolling",
            cutoff_time=normalized_cutoff,
            included_observation_count=len(filtered_timestamps),
            total_observation_count=len(x),
            estimator_parameters={
                "window": window,
                "min_periods": min_periods,
                "ddof": ddof,
            },
            value=series[-1] if series else None,
        )
    if estimator_key == "ewma":
        if alpha is None:
            raise ValueError("alpha is required for EWMA point-in-time covariance.")
        series = ewma_covariance(
            filtered_x,
            filtered_y,
            alpha=alpha,
            min_periods=min_periods,
        )
        return _point_in_time_result(
            metric="covariance",
            estimator="ewma",
            cutoff_time=normalized_cutoff,
            included_observation_count=len(filtered_timestamps),
            total_observation_count=len(x),
            estimator_parameters={
                "alpha": alpha,
                "min_periods": min_periods,
            },
            value=series[-1] if series else None,
        )
    raise ValueError("estimator must be 'rolling' or 'ewma'.")


def reconstruct_point_in_time_correlation(
    x: Sequence[float],
    y: Sequence[float],
    observation_timestamps: Sequence[Any],
    *,
    cutoff_time: Any,
    estimator: str,
    min_periods: int,
    window: int | None = None,
    alpha: float | None = None,
) -> dict[str, Any]:
    """Reconstruct the correlation available at a historical cutoff."""
    filtered_x, filtered_y, filtered_timestamps, normalized_cutoff = _point_in_time_series(
        x,
        y,
        observation_timestamps,
        cutoff_time=cutoff_time,
    )
    estimator_key = _normalize_text(estimator).lower()
    if estimator_key == "rolling":
        if window is None:
            raise ValueError("window is required for rolling point-in-time correlation.")
        series = rolling_correlation(
            filtered_x,
            filtered_y,
            window=window,
            min_periods=min_periods,
        )
        return _point_in_time_result(
            metric="correlation",
            estimator="rolling",
            cutoff_time=normalized_cutoff,
            included_observation_count=len(filtered_timestamps),
            total_observation_count=len(x),
            estimator_parameters={
                "window": window,
                "min_periods": min_periods,
            },
            value=series[-1] if series else None,
        )
    if estimator_key == "ewma":
        if alpha is None:
            raise ValueError("alpha is required for EWMA point-in-time correlation.")
        series = ewma_correlation(
            filtered_x,
            filtered_y,
            alpha=alpha,
            min_periods=min_periods,
        )
        return _point_in_time_result(
            metric="correlation",
            estimator="ewma",
            cutoff_time=normalized_cutoff,
            included_observation_count=len(filtered_timestamps),
            total_observation_count=len(x),
            estimator_parameters={
                "alpha": alpha,
                "min_periods": min_periods,
            },
            value=series[-1] if series else None,
        )
    raise ValueError("estimator must be 'rolling' or 'ewma'.")


def reconstruct_point_in_time_covariance_matrix(
    series_by_position: Mapping[str, Sequence[float]],
    observation_timestamps: Sequence[Any],
    *,
    cutoff_time: Any,
    estimator: str,
    min_periods: int,
    window: int | None = None,
    ddof: int = 1,
    alpha: float | None = None,
) -> dict[str, Any]:
    """Reconstruct the covariance matrix available at a historical cutoff.

    The caller owns return construction and timestamp alignment. This function
    owns cutoff exclusion and pairwise matrix composition only.
    """
    if not isinstance(series_by_position, Mapping):
        raise ValueError("series_by_position must be a mapping.")

    cutoff = _parse_iso(cutoff_time)
    if cutoff is None:
        raise ValueError("cutoff_time must be a valid ISO-8601 timestamp.")
    normalized_cutoff = _to_iso8601_utc(cutoff)

    ordered_position_ids = list(series_by_position.keys())
    if any(not isinstance(position_id, str) or not position_id for position_id in ordered_position_ids):
        raise ValueError("Position identifiers must be non-empty strings.")
    if not ordered_position_ids:
        estimator_key = _normalize_text(estimator).lower()
        if estimator_key not in {"rolling", "ewma"}:
            raise ValueError("estimator must be 'rolling' or 'ewma'.")
        return {
            "ok": True,
            "status": "ready",
            "metric": "covariance_matrix",
            "estimator": estimator_key,
            "cutoff_time": normalized_cutoff,
            "ordered_position_ids": [],
            "included_observation_count": 0,
            "excluded_future_observation_count": 0,
            "point_in_time_safe": True,
            "estimator_parameters": {
                "window": window,
                "min_periods": min_periods,
                "ddof": ddof,
                "alpha": alpha,
            },
            "matrix": [],
            "value": [],
        }

    series = {position_id: list(series_by_position[position_id]) for position_id in ordered_position_ids}
    expected_count = len(series[ordered_position_ids[0]])
    for position_id in ordered_position_ids[1:]:
        if len(series[position_id]) != expected_count:
            raise ValueError("All position series must have the same length.")

    timestamps = _ordered_observation_timestamps(
        observation_timestamps,
        expected_count=expected_count,
    )
    included_observation_count = sum(1 for timestamp in timestamps if timestamp <= cutoff)
    estimator_key = _normalize_text(estimator).lower()
    if estimator_key not in {"rolling", "ewma"}:
        raise ValueError("estimator must be 'rolling' or 'ewma'.")

    estimator_parameters = {
        "window": window,
        "min_periods": min_periods,
        "ddof": ddof,
        "alpha": alpha,
    }
    matrix: list[list[float]] = [[0.0 for _ in ordered_position_ids] for _ in ordered_position_ids]
    pairwise_statuses: dict[str, str] = {}
    for row_index, row_position_id in enumerate(ordered_position_ids):
        for column_index in range(row_index, len(ordered_position_ids)):
            column_position_id = ordered_position_ids[column_index]
            result = reconstruct_point_in_time_covariance(
                series[row_position_id],
                series[column_position_id],
                observation_timestamps,
                cutoff_time=cutoff,
                estimator=estimator_key,
                min_periods=min_periods,
                window=window,
                ddof=ddof,
                alpha=alpha,
            )
            pair_key = f"{row_position_id}|{column_position_id}"
            pairwise_statuses[pair_key] = str(result["status"])
            value = result["value"]
            if value is None:
                return {
                    "ok": False,
                    "status": "insufficient_history",
                    "metric": "covariance_matrix",
                    "estimator": estimator_key,
                    "cutoff_time": normalized_cutoff,
                    "ordered_position_ids": ordered_position_ids,
                    "included_observation_count": included_observation_count,
                    "excluded_future_observation_count": max(0, expected_count - included_observation_count),
                    "point_in_time_safe": True,
                    "estimator_parameters": estimator_parameters,
                    "pairwise_statuses": pairwise_statuses,
                    "matrix": None,
                    "value": None,
                }
            matrix[row_index][column_index] = float(value)
            matrix[column_index][row_index] = float(value)

    return {
        "ok": True,
        "status": "ready",
        "metric": "covariance_matrix",
        "estimator": estimator_key,
        "cutoff_time": normalized_cutoff,
        "ordered_position_ids": ordered_position_ids,
        "included_observation_count": included_observation_count,
        "excluded_future_observation_count": max(0, expected_count - included_observation_count),
        "point_in_time_safe": True,
        "estimator_parameters": estimator_parameters,
        "pairwise_statuses": pairwise_statuses,
        "matrix": matrix,
        "value": matrix,
    }


def _edge_bucket_label(pricing_gap: float | None) -> str:
    if pricing_gap is None:
        return "unknown"
    gap = abs(pricing_gap)
    if gap < 0.01:
        return "0.000-0.010"
    if gap < 0.025:
        return "0.010-0.025"
    return "0.025+"


def _calibration_bucket_label(probability: float) -> str:
    if probability < 0.45:
        return "0.00-0.45"
    if probability < 0.50:
        return "0.45-0.50"
    if probability < 0.55:
        return "0.50-0.55"
    if probability < 0.65:
        return "0.55-0.65"
    return "0.65-1.00"


def _build_calibration(rows: Sequence[Mapping[str, Any]], *, label: str) -> Mapping[str, Any]:
    probability_rows = [
        row
        for row in rows
        if row.get("market_implied_probability") not in (None, "")
        and row.get("actual_outcome") not in (None, "")
        and not bool(row.get("push_flag"))
    ]
    if not probability_rows:
        return build_calibration_summary(
            label=label,
            sample_count=0,
            calibration_error=0.0,
            calibration_score=0.0,
            buckets={},
            metadata={"available": False},
        )

    absolute_errors = [
        abs(
            _normalize_float(row.get("market_implied_probability"), 0.0)
            - _normalize_float(row.get("actual_outcome"), 0.0)
        )
        for row in probability_rows
    ]
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in probability_rows:
        probability = _normalize_float(row.get("market_implied_probability"), 0.0)
        buckets[_calibration_bucket_label(probability)].append(
            _normalize_float(row.get("actual_outcome"), 0.0)
        )
    return build_calibration_summary(
        label=label,
        sample_count=len(probability_rows),
        calibration_error=_mean(absolute_errors),
        calibration_score=round(max(0.0, 1.0 - _mean(absolute_errors)), 6),
        buckets={
            bucket_label: round(sum(values) / len(values), 6)
            for bucket_label, values in sorted(buckets.items())
            if values
        },
        metadata={"available": True},
    )


def _drawdown_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    equity = 100.0
    peak = equity
    trough = equity
    max_drawdown_percent = 0.0
    for row in rows:
        equity += _normalize_float(row.get("profit_loss_units"), 0.0)
        peak = max(peak, equity)
        trough = min(trough, equity)
        if peak > 0:
            drawdown = ((peak - equity) / peak) * 100.0
            max_drawdown_percent = max(max_drawdown_percent, drawdown)
    return {
        "starting_equity": 100.0,
        "ending_equity": round(equity, 6),
        "peak_equity": round(peak, 6),
        "trough_equity": round(trough, 6),
        "max_drawdown_percent": round(max_drawdown_percent, 6),
    }


def _performance_bucket(
    label: str,
    rows: Sequence[Mapping[str, Any]],
) -> BacktestPerformanceBucketContract:
    settled_rows = [
        row
        for row in rows
        if row.get("outcome_status") in {"win", "loss", "push"}
    ]
    wins = sum(1 for row in settled_rows if row.get("outcome_status") == "win")
    losses = sum(1 for row in settled_rows if row.get("outcome_status") == "loss")
    pushes = sum(1 for row in settled_rows if row.get("outcome_status") == "push")
    sample_size = len(settled_rows)
    profit_loss_units = round(
        sum(_normalize_float(row.get("profit_loss_units"), 0.0) for row in settled_rows),
        6,
    )
    brier_values = [
        value
        for value in (
            _brier_score(
                _clamp_probability(row.get("market_implied_probability")),
                row.get("actual_outcome"),
            )
            for row in settled_rows
        )
        if value is not None
    ]
    log_loss_values = [
        value
        for value in (
            _log_loss(
                _clamp_probability(row.get("market_implied_probability")),
                row.get("actual_outcome"),
            )
            for row in settled_rows
        )
        if value is not None
    ]
    warnings: list[str] = []
    if 0 < sample_size < RECOMMENDED_MIN_SAMPLE_SIZE:
        warnings.append("low_sample_size")
    return BacktestPerformanceBucketContract(
        label=label,
        sample_size=sample_size,
        wins=wins,
        losses=losses,
        pushes=pushes,
        roi_percent=round((profit_loss_units / sample_size) * 100.0, 6)
        if sample_size
        else 0.0,
        brier_score=_mean(brier_values) if brier_values else None,
        log_loss=_mean(log_loss_values) if log_loss_values else None,
        calibration_summary=_build_calibration(settled_rows, label=f"{label}_calibration"),
        drawdown_summary=_drawdown_summary(settled_rows),
        warnings=tuple(warnings),
        metadata={"profit_loss_units": profit_loss_units},
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _path_exists(path_value: Any) -> bool:
    path_text = _normalize_text(path_value)
    return bool(path_text) and Path(path_text).exists()


def _write_artifacts(
    *,
    artifact_root: Path,
    backtest_run_id: str,
    report: BacktestReportContract,
    benchmark_comparison: Mapping[str, Any],
    validation: Mapping[str, Any],
    dashboard_output: Mapping[str, Any],
) -> dict[str, str]:
    run_root = artifact_root / backtest_run_id
    run_root.mkdir(parents=True, exist_ok=True)
    report_json_path = run_root / "report.json"
    report_markdown_path = run_root / "summary.md"
    dashboard_json_path = run_root / "dashboard.json"
    report_payload = {
        "backtest_report": report.as_dict(),
        "benchmark_comparison": dict(benchmark_comparison),
        "validation": dict(validation),
        "dashboard_output": dict(dashboard_output),
    }
    _write_text(report_json_path, json.dumps(report_payload, indent=2, sort_keys=True) + "\n")
    markdown = "\n".join(
        [
            f"# Phase 5.5 Baseline Backtest `{backtest_run_id}`",
            "",
            f"- Decisions replayed: `{report.sample_size}`",
            f"- Wins / losses / pushes: `{report.wins}` / `{report.losses}` / `{report.pushes}`",
            f"- ROI percent: `{report.roi_percent}`",
            f"- Validation status: `{'validated' if validation.get('ok') else 'blocked'}`",
            f"- No-trade benchmark ROI percent: `{benchmark_comparison.get('no_trade', {}).get('roi_percent', 0.0)}`",
            f"- Market-implied benchmark brier score: `{benchmark_comparison.get('market_implied', {}).get('brier_score')}`",
        ]
    )
    _write_text(report_markdown_path, markdown + "\n")
    _write_text(dashboard_json_path, json.dumps(dashboard_output, indent=2, sort_keys=True) + "\n")
    return {
        "artifact_root": str(run_root),
        "report_json_path": str(report_json_path),
        "report_markdown_path": str(report_markdown_path),
        "dashboard_json_path": str(dashboard_json_path),
    }


def _backtest_missing_snapshot(
    *,
    storage: LocalStorageEngine,
    decision_batch_id: str,
    status: str,
    warnings: Sequence[str],
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "readiness": "blocked",
        "lifecycle_state": "missing",
        "dataset_id": DEFAULT_BASELINE_BACKTEST_DATASET_ID,
        "dataset_name": DEFAULT_BASELINE_BACKTEST_DATASET_NAME,
        "decision_batch_id": decision_batch_id,
        "backtest_run_id": "",
        "validation_state": "missing",
        "dataset_certification_status": "missing",
        "dataset_certification_id": "",
        "source_decision_dataset_id": "",
        "source_decision_population_summary_id": "",
        "source_decision_batch_lineage_id": "",
        "sample_size": 0,
        "backtest_rows": [],
        "backtest_report": {},
        "benchmark_comparison": {},
        "validation": {"ok": False},
        "artifact_references": {},
        "artifact_integrity_ok": False,
        "artifact_integrity_checks": {},
        "storage": storage.health(),
        "warnings": list(warnings),
        "idempotent_reuse": False,
        "unresolved_blockers": list(warnings),
    }


def _load_backtest_snapshot(
    storage: LocalStorageEngine,
    *,
    backtest_run_id: str = "",
    decision_batch_id: str = "",
) -> dict[str, Any]:
    if not storage.table_exists(BACKTEST_RUN_TABLE):
        return {}
    if backtest_run_id:
        run_rows = storage.fetch(
            BACKTEST_RUN_TABLE,
            where="backtest_run_id = ?",
            params=[backtest_run_id],
            limit=1,
        )
    elif decision_batch_id:
        run_rows = storage.fetch(
            BACKTEST_RUN_TABLE,
            where="decision_batch_id = ? AND strategy_name = ?",
            params=[decision_batch_id, DEFAULT_BASELINE_BACKTEST_STRATEGY_NAME],
            order_by="created_at ASC, backtest_run_id ASC",
            limit=1,
        )
    else:
        run_rows = storage.fetch(
            BACKTEST_RUN_TABLE,
            where="strategy_name = ?",
            params=[DEFAULT_BASELINE_BACKTEST_STRATEGY_NAME],
            order_by="created_at ASC, backtest_run_id ASC",
            limit=1,
        )
    if not run_rows:
        return {}
    run_row = dict(run_rows[0])
    run_id = _normalize_text(run_row.get("backtest_run_id"))
    backtest_rows = (
        storage.fetch(
            BACKTEST_ROW_TABLE,
            where="backtest_run_id = ?",
            params=[run_id],
            order_by="decision_cutoff_time ASC, dataset_row_id ASC, backtest_row_id ASC",
        )
        if storage.table_exists(BACKTEST_ROW_TABLE)
        else []
    )
    results = _load_json_mapping(run_row.get("results_json"))
    return {
        "run_row": run_row,
        "backtest_rows": [dict(row) for row in backtest_rows],
        "results": results,
    }


def build_baseline_backtest_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    backtest_run_id: str | None = None,
    decision_batch_id: str | None = None,
    idempotent_reuse: bool = False,
) -> dict[str, Any]:
    storage = create_local_storage_engine(
        storage_path or DEFAULT_BASELINE_BACKTEST_STORAGE_PATH,
        backend=backend,
    )
    try:
        snapshot = _load_backtest_snapshot(
            storage,
            backtest_run_id=_normalize_text(backtest_run_id),
            decision_batch_id=_normalize_text(decision_batch_id),
        )
        if not snapshot:
            return _backtest_missing_snapshot(
                storage=storage,
                decision_batch_id=_normalize_text(decision_batch_id),
                status="missing_backtest_run",
                warnings=["persisted baseline backtest run is required"],
            )
        run_row = snapshot["run_row"]
        backtest_rows = snapshot["backtest_rows"]
        results = snapshot["results"]
        report = dict(results.get("backtest_report") or {})
        benchmark_comparison = dict(results.get("benchmark_comparison") or {})
        validation = dict(results.get("validation") or {})
        artifact_references = dict(results.get("artifact_references") or {})
        warnings = list(results.get("warnings") or [])
        artifact_integrity_checks = {
            "report_json_exists": _path_exists(artifact_references.get("report_json_path")),
            "report_markdown_exists": _path_exists(artifact_references.get("report_markdown_path")),
            "dashboard_json_exists": _path_exists(artifact_references.get("dashboard_json_path")),
        } if artifact_references else {}
        artifact_integrity_ok = bool(artifact_integrity_checks) and all(artifact_integrity_checks.values())
        source_decision_dataset_certification_id = _normalize_text(run_row.get("source_decision_dataset_certification_id"))
        settled_rows = [
            dict(row)
            for row in backtest_rows
            if _normalize_text(row.get("outcome_status")) in {"win", "loss", "push"}
        ]
        return {
            "ok": bool(validation.get("ok")) and bool(report.get("sample_size", 0)),
            "status": _normalize_text(run_row.get("status"), "blocked"),
            "readiness": _normalize_text(run_row.get("readiness"), "blocked"),
            "lifecycle_state": _normalize_text(run_row.get("readiness"), "missing"),
            "dataset_id": _normalize_text(run_row.get("dataset_id"), DEFAULT_BASELINE_BACKTEST_DATASET_ID),
            "dataset_name": _normalize_text(run_row.get("dataset_name"), DEFAULT_BASELINE_BACKTEST_DATASET_NAME),
            "decision_batch_id": _normalize_text(run_row.get("decision_batch_id")),
            "backtest_run_id": _normalize_text(run_row.get("backtest_run_id")),
            "validation_state": _normalize_text(run_row.get("validation_state"), "missing"),
            "dataset_certification_status": "certified" if source_decision_dataset_certification_id else "missing",
            "dataset_certification_id": source_decision_dataset_certification_id,
            "source_decision_dataset_id": _normalize_text(run_row.get("source_decision_dataset_id")),
            "source_decision_population_summary_id": _normalize_text(run_row.get("source_decision_population_summary_id")),
            "source_decision_batch_lineage_id": _normalize_text(run_row.get("source_decision_batch_lineage_id")),
            "strategy_name": _normalize_text(run_row.get("strategy_name"), DEFAULT_BASELINE_BACKTEST_STRATEGY_NAME),
            "sample_size": _normalize_int(run_row.get("sample_size"), 0),
            "wins": _normalize_int(run_row.get("wins"), 0),
            "losses": _normalize_int(run_row.get("losses"), 0),
            "pushes": _normalize_int(run_row.get("pushes"), 0),
            "profit_loss_units": _normalize_float(run_row.get("profit_loss_units"), 0.0),
            "roi_percent": _normalize_float(run_row.get("roi_percent"), 0.0),
            "point_in_time_ok": bool(_normalize_int(run_row.get("point_in_time_ok"), 0)),
            "backtest_report": report,
            "benchmark_comparison": benchmark_comparison,
            "validation": validation,
            "backtest_run_row": run_row,
            "backtest_rows": backtest_rows,
            "settled_backtest_rows": settled_rows,
            "artifact_references": artifact_references,
            "artifact_integrity_ok": artifact_integrity_ok,
            "artifact_integrity_checks": artifact_integrity_checks,
            "storage": storage.health(),
            "warnings": warnings,
            "idempotent_reuse": bool(idempotent_reuse),
            "unresolved_blockers": [] if validation.get("ok") else list(validation.get("warnings", warnings)),
        }
    finally:
        storage.close()


def get_baseline_backtest_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    backtest_run_id: str | None = None,
    decision_batch_id: str | None = None,
) -> dict[str, Any]:
    return build_baseline_backtest_dashboard_snapshot(
        storage_path=storage_path,
        backend=backend,
        backtest_run_id=backtest_run_id,
        decision_batch_id=decision_batch_id,
    )


def run_baseline_backtest(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    decision_dataset_id: str = DEFAULT_DECISION_DATASET_ID,
    decision_batch_id: str | None = None,
    artifact_root: str | Path | None = None,
) -> dict[str, Any]:
    storage = create_local_storage_engine(
        storage_path or DEFAULT_BASELINE_BACKTEST_STORAGE_PATH,
        backend=backend,
    )
    try:
        decision_snapshot = build_decision_row_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=decision_dataset_id,
            batch_id=decision_batch_id,
        )
        if not decision_snapshot.get("ok"):
            return _backtest_missing_snapshot(
                storage=storage,
                decision_batch_id=_normalize_text(decision_batch_id),
                status="missing_certified_decision_rows",
                warnings=list(decision_snapshot.get("warnings") or ["certified decision rows are required"]),
            )
        decision_rows = sorted(
            [dict(row) for row in decision_snapshot.get("decision_rows") or []],
            key=_decision_row_sort_key,
        )
        decision_summary = dict(decision_snapshot.get("decision_population_summary") or {})
        effective_decision_batch_id = _normalize_text(
            decision_snapshot.get("batch_id") or decision_summary.get("batch_id") or decision_batch_id
        )
        if not decision_rows or not effective_decision_batch_id:
            return _backtest_missing_snapshot(
                storage=storage,
                decision_batch_id=effective_decision_batch_id,
                status="missing_certified_decision_rows",
                warnings=["certified decision rows are required"],
            )

        backtest_run_id = _stable_id(
            "baseline_backtest_run",
            DEFAULT_BASELINE_BACKTEST_DATASET_ID,
            effective_decision_batch_id,
            decision_summary.get("snapshot_id"),
            decision_summary.get("source_signal_batch_id"),
            BASELINE_BACKTEST_SCHEMA_VERSION,
            BASELINE_BACKTEST_TRANSFORMATION_VERSION,
        )
        existing_snapshot = _load_backtest_snapshot(
            storage,
            backtest_run_id=backtest_run_id,
        )
        if existing_snapshot and len(existing_snapshot.get("backtest_rows", [])) == len(decision_rows):
            return build_baseline_backtest_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
                backtest_run_id=backtest_run_id,
                idempotent_reuse=True,
            )

        dataset_rows = {
            _normalize_text(row.get("dataset_row_id")): dict(row)
            for row in (
                storage.fetch(
                    "historical_dataset_rows",
                    order_by="dataset_row_id ASC",
                )
                if storage.table_exists("historical_dataset_rows")
                else []
            )
            if _normalize_text(row.get("dataset_row_id"))
        }
        created_at = _utc_now_iso()
        resolved_artifact_root = _resolve_artifact_root(storage.path, artifact_root)
        settled_rows: list[dict[str, Any]] = []
        backtest_rows: list[dict[str, Any]] = []
        rejection_reasons: Counter[str] = Counter()
        missingness_summary: Counter[str] = Counter()

        for decision_row in decision_rows:
            decision_dataset_row_id = _normalize_text(decision_row.get("dataset_row_id"))
            dataset_row = dict(dataset_rows.get(decision_dataset_row_id) or {})
            market_context = _market_selection_context(decision_row, dataset_row)
            signal_values = _load_json_mapping(
                _load_json_mapping(decision_row.get("decision_context_json")).get("source_signal_values")
            )
            point_in_time = _point_in_time_validation(decision_row, dataset_row, market_context) if dataset_row else {
                "ok": False,
                "checks": {"missing_dataset_row": False},
            }
            settlement = _settle_market(market_context, dataset_row) if dataset_row else {
                "settlement_status": "missing_dataset_row",
                "outcome_status": "rejected",
                "actual_outcome": None,
                "push_flag": False,
                "resolution_detail": "missing_dataset_row",
            }
            replay_status = "replayed"
            rejection_reason = ""
            if not dataset_row:
                replay_status = "rejected"
                rejection_reason = "missing_dataset_row"
            elif not point_in_time.get("ok"):
                replay_status = "rejected"
                rejection_reason = "point_in_time_validation_failed"
            elif settlement.get("outcome_status") == "unsettled":
                replay_status = "rejected"
                rejection_reason = "unsettled_result"
            elif settlement.get("outcome_status") == "rejected":
                replay_status = "rejected"
                rejection_reason = _normalize_text(settlement.get("resolution_detail"), "unsupported_market_type")
            if replay_status == "rejected":
                rejection_reasons[rejection_reason or "unknown_rejection"] += 1

            decimal_odds = _normalize_float(
                dataset_row.get("decimal_odds"),
                _decimal_from_american(dataset_row.get("american_odds")),
            )
            market_probability = _clamp_probability(dataset_row.get("implied_probability"))
            actual_outcome = settlement.get("actual_outcome")
            push_flag = bool(settlement.get("push_flag"))
            profit_loss_units = 0.0
            stake_units = 0.0
            roi_percent = 0.0
            if replay_status == "replayed":
                stake_units = DEFAULT_UNIT_STAKE
                profit_loss_units = _profit_loss_units(
                    decimal_odds=decimal_odds,
                    actual_outcome=_normalize_float(actual_outcome, 0.0),
                    push_flag=push_flag,
                )
                roi_percent = round((profit_loss_units / stake_units) * 100.0, 6) if stake_units else 0.0
            else:
                actual_outcome = None

            pricing_gap = signal_values.get(SIGNAL_PRICING_GAP_ID)
            consensus_probability = signal_values.get(SIGNAL_CONSENSUS_PROBABILITY_ID)
            fair_american_odds = signal_values.get(SIGNAL_FAIR_AMERICAN_ODDS_ID)
            fair_decimal_odds = signal_values.get(SIGNAL_FAIR_DECIMAL_ODDS_ID)
            confidence_score = signal_values.get(SIGNAL_CONFIDENCE_SCORE_ID)
            confidence_grade = signal_values.get(SIGNAL_CONFIDENCE_GRADE_ID)
            benchmark_market_expected_profit = 0.0
            if market_probability is not None and decimal_odds > 0:
                benchmark_market_expected_profit = round(
                    (market_probability * (decimal_odds - 1.0)) - (1.0 - market_probability),
                    6,
                )
            if market_probability is None:
                missingness_summary["market_implied_probability"] += 1
            if decimal_odds <= 0:
                missingness_summary["decimal_odds"] += 1

            backtest_row_id = _stable_id(
                "baseline_backtest_row",
                backtest_run_id,
                decision_row.get("snapshot_id"),
                decision_dataset_row_id,
            )
            row_payload = {
                "backtest_row_id": backtest_row_id,
                "backtest_run_id": backtest_run_id,
                "decision_dataset_id": decision_dataset_id,
                "decision_batch_id": effective_decision_batch_id,
                "source_decision_snapshot_id": _normalize_text(decision_row.get("snapshot_id")),
                "source_decision_context_id": _normalize_text(decision_row.get("decision_context_id")),
                "source_signal_context_id": _normalize_text(decision_row.get("source_signal_context_id")),
                "source_dataset_snapshot_id": _normalize_text(dataset_row.get("snapshot_id")),
                "source_dataset_lineage_id": _normalize_text(dataset_row.get("lineage_id")),
                "dataset_row_id": decision_dataset_row_id,
                "event_id": _normalize_text(dataset_row.get("event_id") or decision_row.get("event_id")),
                "game_id": _normalize_text(dataset_row.get("game_id") or decision_row.get("game_id")),
                "season": _normalize_int(dataset_row.get("season") or decision_row.get("season"), 0),
                "week": _normalize_int(dataset_row.get("week") or decision_row.get("week"), 0),
                "market_type": market_context["market_type"],
                "selection": market_context["selection"],
                "book": market_context["book"],
                "home_team_id": market_context["home_team_id"],
                "away_team_id": market_context["away_team_id"],
                "target_team_id": market_context["target_team_id"],
                "opponent_team_id": market_context["opponent_team_id"],
                "decision_cutoff_time": _to_iso8601_utc(decision_row.get("decision_cutoff_time")),
                "scheduled_kickoff_time": _to_iso8601_utc(decision_row.get("scheduled_kickoff_time")),
                "settlement_recorded_time": _to_iso8601_utc(dataset_row.get("label_result_recorded_time")),
                "decision_readiness_status": _normalize_text(
                    decision_row.get("decision_readiness_status"),
                    "EXCLUDED",
                ),
                "replay_status": replay_status,
                "rejection_reason": rejection_reason,
                "point_in_time_valid": int(bool(point_in_time.get("ok"))),
                "point_in_time_validation_json": _as_json(point_in_time),
                "settlement_status": _normalize_text(settlement.get("settlement_status")),
                "outcome_status": _normalize_text(settlement.get("outcome_status")),
                "actual_outcome": actual_outcome,
                "push_flag": int(push_flag),
                "stake_units": stake_units,
                "profit_loss_units": profit_loss_units,
                "roi_percent": roi_percent,
                "line_value": _normalize_float(dataset_row.get("line_value"), 0.0),
                "american_odds": _normalize_float(dataset_row.get("american_odds"), 0.0),
                "decimal_odds": decimal_odds,
                "market_implied_probability": market_probability,
                "consensus_probability": _clamp_probability(consensus_probability),
                "pricing_gap": None if pricing_gap in (None, "") else _normalize_float(pricing_gap, 0.0),
                "fair_american_odds": None if fair_american_odds in (None, "") else _normalize_float(fair_american_odds, 0.0),
                "fair_decimal_odds": None if fair_decimal_odds in (None, "") else _normalize_float(fair_decimal_odds, 0.0),
                "confidence_score": None if confidence_score in (None, "") else _normalize_float(confidence_score, 0.0),
                "confidence_grade": _normalize_text(confidence_grade),
                "benchmark_no_trade_profit_loss_units": 0.0,
                "benchmark_market_expected_profit_loss_units": benchmark_market_expected_profit,
                "benchmark_market_brier_score": _brier_score(market_probability, actual_outcome),
                "benchmark_market_log_loss": _log_loss(market_probability, actual_outcome),
                "schema_version": BASELINE_BACKTEST_SCHEMA_VERSION,
                "created_at": created_at,
                "updated_at": created_at,
                "source": "decision_rows",
                "provider": "repository",
                "market": DEFAULT_BASELINE_BACKTEST_MARKET,
                "asset_class": "backtest",
                "snapshot_id": backtest_row_id,
                "lineage_id": _stable_id(
                    "baseline_backtest_lineage",
                    backtest_run_id,
                    decision_row.get("snapshot_id"),
                    decision_dataset_row_id,
                ),
                "version_id": _stable_id(
                    "baseline_backtest_version",
                    backtest_run_id,
                    decision_row.get("snapshot_id"),
                    BASELINE_BACKTEST_TRANSFORMATION_VERSION,
                ),
                "quality_score": 1.0 if replay_status == "replayed" else 0.0,
            }
            row_payload["payload_json"] = _as_json(
                {
                    **row_payload,
                    "resolution_detail": settlement.get("resolution_detail"),
                    "market_context": market_context,
                    "source_signal_values": signal_values,
                }
            )
            backtest_rows.append(row_payload)
            if replay_status == "replayed":
                settled_rows.append(row_payload)

        wins = sum(1 for row in settled_rows if row.get("outcome_status") == "win")
        losses = sum(1 for row in settled_rows if row.get("outcome_status") == "loss")
        pushes = sum(1 for row in settled_rows if row.get("outcome_status") == "push")
        sample_size = len(settled_rows)
        total_profit_loss_units = round(
            sum(_normalize_float(row.get("profit_loss_units"), 0.0) for row in settled_rows),
            6,
        )
        roi_percent = round((total_profit_loss_units / sample_size) * 100.0, 6) if sample_size else 0.0
        market_probabilities = [
            _normalize_float(row.get("market_implied_probability"), 0.0)
            for row in settled_rows
            if row.get("market_implied_probability") not in (None, "")
            and not bool(row.get("push_flag"))
        ]
        brier_values = [
            _normalize_float(row.get("benchmark_market_brier_score"), 0.0)
            for row in settled_rows
            if row.get("benchmark_market_brier_score") not in (None, "")
        ]
        log_loss_values = [
            _normalize_float(row.get("benchmark_market_log_loss"), 0.0)
            for row in settled_rows
            if row.get("benchmark_market_log_loss") not in (None, "")
        ]
        evaluation_times = [
            _normalize_text(row.get("decision_cutoff_time"))
            for row in settled_rows
            if _normalize_text(row.get("decision_cutoff_time"))
        ]
        season_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        market_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        edge_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in settled_rows:
            season_groups[str(_normalize_int(row.get("season"), 0))].append(row)
            market_groups[_normalize_text(row.get("market_type"), "unknown")].append(row)
            edge_groups[_edge_bucket_label(row.get("pricing_gap"))].append(row)

        warnings: list[str] = []
        if sample_size < RECOMMENDED_MIN_SAMPLE_SIZE:
            warnings.append("low_sample_size")
        if rejection_reasons:
            warnings.append("rejected_rows_present")
        validation = {
            "ok": bool(sample_size) and not rejection_reasons,
            "input_surface": "certified_decision_rows_only",
            "total_decision_rows": len(decision_rows),
            "replayed_rows": sample_size,
            "rejected_rows": len(decision_rows) - sample_size,
            "point_in_time_ok": all(bool(row.get("point_in_time_valid")) for row in backtest_rows if row.get("replay_status") == "replayed"),
            "missing_dataset_rows": int(rejection_reasons.get("missing_dataset_row", 0)),
            "unsettled_rows": int(rejection_reasons.get("unsettled_result", 0)),
            "point_in_time_failures": int(rejection_reasons.get("point_in_time_validation_failed", 0)),
            "warnings": list(warnings),
            "rejection_reasons": dict(rejection_reasons),
        }
        benchmark_comparison = {
            "no_trade": {
                "sample_size": sample_size,
                "profit_loss_units": 0.0,
                "roi_percent": 0.0,
            },
            "market_implied": {
                "sample_size": len(market_probabilities),
                "expected_profit_loss_units": round(
                    sum(
                        _normalize_float(row.get("benchmark_market_expected_profit_loss_units"), 0.0)
                        for row in settled_rows
                    ),
                    6,
                ),
                "mean_probability": _mean(market_probabilities),
                "brier_score": _mean(brier_values) if brier_values else None,
                "log_loss": _mean(log_loss_values) if log_loss_values else None,
            },
            "strategy_vs_benchmarks": {
                "profit_loss_units_vs_no_trade": total_profit_loss_units,
                "roi_percent_vs_no_trade": roi_percent,
                "hit_rate_minus_market_probability": round(
                    ((wins / max(wins + losses, 1)) - _mean(market_probabilities)),
                    6,
                )
                if market_probabilities
                else 0.0,
            },
        }
        backtest_report = BacktestReportContract(
            experiment_id=backtest_run_id,
            report_version=BACKTEST_REPORT_SCHEMA_VERSION,
            created_at=created_at,
            total_decisions=len(decision_rows),
            eligible_decisions=sample_size,
            rejected_decisions=len(decision_rows) - sample_size,
            wins=wins,
            losses=losses,
            pushes=pushes,
            sample_size=sample_size,
            roi_percent=roi_percent,
            evaluation_start=min(evaluation_times) if evaluation_times else None,
            evaluation_end=max(evaluation_times) if evaluation_times else None,
            brier_score=_mean(brier_values) if brier_values else None,
            log_loss=_mean(log_loss_values) if log_loss_values else None,
            calibration_summary=_build_calibration(settled_rows, label="market_implied"),
            drawdown_summary=_drawdown_summary(settled_rows),
            performance_by_season={
                label: _performance_bucket(label, rows)
                for label, rows in sorted(season_groups.items())
            },
            performance_by_market={
                label: _performance_bucket(label, rows)
                for label, rows in sorted(market_groups.items())
            },
            performance_by_edge_bucket={
                label: _performance_bucket(label, rows)
                for label, rows in sorted(edge_groups.items())
            },
            rejection_reasons=dict(rejection_reasons),
            missingness_summary=dict(missingness_summary),
            warnings=tuple(warnings),
            metrics_reference={"uri": ""},
            artifact_reference={"uri": ""},
        )
        dashboard_output = {
            "backtest_run_id": backtest_run_id,
            "decision_batch_id": effective_decision_batch_id,
            "summary_cards": {
                "sample_size": sample_size,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "profit_loss_units": total_profit_loss_units,
                "roi_percent": roi_percent,
                "max_drawdown_percent": backtest_report.drawdown_summary.get("max_drawdown_percent", 0.0),
                "point_in_time_ok": validation["point_in_time_ok"],
            },
            "benchmark_comparison": benchmark_comparison,
            "validation": validation,
            "preview_rows": [
                {
                    "dataset_row_id": row.get("dataset_row_id"),
                    "market_type": row.get("market_type"),
                    "selection": row.get("selection"),
                    "outcome_status": row.get("outcome_status"),
                    "profit_loss_units": row.get("profit_loss_units"),
                    "roi_percent": row.get("roi_percent"),
                }
                for row in backtest_rows[:200]
            ],
        }
        artifact_references = _write_artifacts(
            artifact_root=resolved_artifact_root,
            backtest_run_id=backtest_run_id,
            report=backtest_report,
            benchmark_comparison=benchmark_comparison,
            validation=validation,
            dashboard_output=dashboard_output,
        )
        report_reference = {
            "uri": artifact_references["report_json_path"],
            "markdown_uri": artifact_references["report_markdown_path"],
            "dashboard_uri": artifact_references["dashboard_json_path"],
        }
        backtest_report = BacktestReportContract(
            experiment_id=backtest_report.experiment_id,
            report_version=backtest_report.report_version,
            created_at=backtest_report.created_at,
            total_decisions=backtest_report.total_decisions,
            eligible_decisions=backtest_report.eligible_decisions,
            rejected_decisions=backtest_report.rejected_decisions,
            wins=backtest_report.wins,
            losses=backtest_report.losses,
            pushes=backtest_report.pushes,
            sample_size=backtest_report.sample_size,
            roi_percent=backtest_report.roi_percent,
            evaluation_start=backtest_report.evaluation_start,
            evaluation_end=backtest_report.evaluation_end,
            brier_score=backtest_report.brier_score,
            log_loss=backtest_report.log_loss,
            calibration_summary=backtest_report.calibration_summary,
            drawdown_summary=backtest_report.drawdown_summary,
            performance_by_season=backtest_report.performance_by_season,
            performance_by_market=backtest_report.performance_by_market,
            performance_by_edge_bucket=backtest_report.performance_by_edge_bucket,
            rejection_reasons=backtest_report.rejection_reasons,
            missingness_summary=backtest_report.missingness_summary,
            warnings=backtest_report.warnings,
            metrics_reference={"uri": artifact_references["dashboard_json_path"]},
            artifact_reference=report_reference,
        )
        results_payload = {
            "backtest_report": backtest_report.as_dict(),
            "benchmark_comparison": benchmark_comparison,
            "validation": validation,
            "artifact_references": artifact_references,
            "warnings": warnings,
            "lineage": {
                "input_surface": "certified_decision_rows_only",
                "decision_dataset_id": decision_dataset_id,
                "decision_batch_id": effective_decision_batch_id,
                "decision_population_summary_id": _normalize_text(decision_summary.get("snapshot_id")),
                "source_signal_population_summary_id": _normalize_text(
                    decision_summary.get("source_signal_population_summary_id")
                ),
            },
        }
        run_row = {
            "backtest_run_id": backtest_run_id,
            "dataset_id": DEFAULT_BASELINE_BACKTEST_DATASET_ID,
            "dataset_name": DEFAULT_BASELINE_BACKTEST_DATASET_NAME,
            "owner": DEFAULT_BASELINE_BACKTEST_OWNER,
            "sport": "football",
            "feature_pack": DEFAULT_DECISION_RESEARCH_ASSET_ID,
            "storage_location": str(storage.path),
            "readiness": "backtest_ready" if validation["ok"] else "blocked",
            "update_frequency": "manual",
            "validation_state": "validated" if validation["ok"] else "rejected",
            "status": "completed" if sample_size else "blocked",
            "strategy_name": DEFAULT_BASELINE_BACKTEST_STRATEGY_NAME,
            "decision_batch_id": effective_decision_batch_id,
            "source_decision_dataset_id": decision_dataset_id,
            "source_decision_population_summary_id": _normalize_text(decision_summary.get("snapshot_id")),
            "source_decision_dataset_certification_id": _normalize_text(
                decision_snapshot.get("dataset_certification_id")
            ),
            "source_decision_batch_lineage_id": _normalize_text(decision_summary.get("lineage_id")),
            "sample_size": sample_size,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "profit_loss_units": total_profit_loss_units,
            "roi_percent": roi_percent,
            "point_in_time_ok": int(bool(validation["point_in_time_ok"])),
            "artifact_root": artifact_references["artifact_root"],
            "report_json_path": artifact_references["report_json_path"],
            "report_markdown_path": artifact_references["report_markdown_path"],
            "dashboard_json_path": artifact_references["dashboard_json_path"],
            "results_json": _as_json(results_payload),
            "payload_json": _as_json(
                {
                    "backtest_run_id": backtest_run_id,
                    "decision_batch_id": effective_decision_batch_id,
                    "decision_row_count": len(decision_rows),
                    "settled_row_count": sample_size,
                    "benchmark_comparison": benchmark_comparison,
                    "validation": validation,
                }
            ),
            "schema_version": BASELINE_BACKTEST_SCHEMA_VERSION,
            "created_at": created_at,
            "updated_at": created_at,
            "source": "decision_rows",
            "provider": "repository",
            "market": DEFAULT_BASELINE_BACKTEST_MARKET,
            "market_type": DEFAULT_BASELINE_BACKTEST_MARKET_TYPE,
            "asset_class": "backtest",
            "snapshot_id": backtest_run_id,
            "lineage_id": _stable_id(
                "baseline_backtest_run_lineage",
                backtest_run_id,
                effective_decision_batch_id,
                decision_summary.get("snapshot_id"),
            ),
            "version_id": _stable_id(
                "baseline_backtest_run_version",
                backtest_run_id,
                BASELINE_BACKTEST_TRANSFORMATION_VERSION,
            ),
            "quality_score": 1.0 if validation["ok"] else 0.0,
        }

        for row in backtest_rows:
            storage.upsert(BACKTEST_ROW_TABLE, row, key_columns=("backtest_row_id",))
        storage.upsert(BACKTEST_RUN_TABLE, run_row, key_columns=("backtest_run_id",))
        return build_baseline_backtest_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            backtest_run_id=backtest_run_id,
            idempotent_reuse=False,
        )
    finally:
        storage.close()


__all__ = [
    "BASELINE_BACKTEST_SCHEMA_VERSION",
    "DEFAULT_BASELINE_BACKTEST_DATASET_ID",
    "DEFAULT_BASELINE_BACKTEST_DATASET_NAME",
    "DEFAULT_BASELINE_BACKTEST_STORAGE_PATH",
    "DEFAULT_BASELINE_BACKTEST_STRATEGY_NAME",
    "build_baseline_backtest_dashboard_snapshot",
    "get_baseline_backtest_snapshot_for_dashboard",
    "reconstruct_point_in_time_correlation",
    "reconstruct_point_in_time_covariance",
    "reconstruct_point_in_time_covariance_matrix",
    "run_baseline_backtest",
]
