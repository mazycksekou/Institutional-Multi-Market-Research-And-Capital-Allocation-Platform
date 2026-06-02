from __future__ import annotations

from typing import Any, Mapping

from .security_policy import locked_safety_flags


TABULAR_FEATURE_SET_VERSION = "cross_asset_tabular_features_v1"
TABULAR_REQUIRED_SAMPLE_SIZE = 500


def _safe_status(total_labeled_outcomes: int) -> str:
    return "calibration_only" if int(total_labeled_outcomes or 0) >= TABULAR_REQUIRED_SAMPLE_SIZE else "blocked_insufficient_data"


def _tabular_lane(
    *,
    model_name: str,
    total_labeled_outcomes: int,
    label_coverage: float,
    target_variable: str = "settled_outcome_or_forward_return",
    foundation: bool = False,
) -> dict[str, Any]:
    sample = max(0, int(total_labeled_outcomes or 0))
    if foundation:
        status = "research_only"
        blocked_reason = "research_only_no_training_lane"
        feature_importance = False
        calibration_error = None
    else:
        status = _safe_status(sample)
        blocked_reason = "needs_500_labeled_outcomes_and_leakage_tests" if sample < TABULAR_REQUIRED_SAMPLE_SIZE else None
        feature_importance = sample >= TABULAR_REQUIRED_SAMPLE_SIZE
        calibration_error = None
    payload = {
        "model_name": model_name,
        "feature_set_version": TABULAR_FEATURE_SET_VERSION,
        "training_sample_size": 0 if sample < TABULAR_REQUIRED_SAMPLE_SIZE else int(sample * 0.8),
        "validation_sample_size": 0 if sample < TABULAR_REQUIRED_SAMPLE_SIZE else sample - int(sample * 0.8),
        "label_coverage": round(float(label_coverage or 0.0), 6),
        "target_variable": target_variable,
        "feature_importance_available": bool(feature_importance),
        "calibration_error": calibration_error,
        "overfitting_risk_score": 95.0 if sample < TABULAR_REQUIRED_SAMPLE_SIZE else 70.0,
        "model_status": status,
        "blocked_reason": blocked_reason,
        "promotion_requirements": [
            "enough_labeled_outcomes",
            "train_validation_split_exists",
            "calibration_error_measured",
            "feature_leakage_tests_pass",
            "no_raw_payloads_or_secrets_exposed",
            "compact_outputs_pass",
            "safety_tests_prove_no_execution_path",
            "baselines_compared",
        ],
        "research_only": foundation,
        "affects_review_queue": False,
        "affects_execution": False,
        "training_enabled": False,
        "heavy_dependency_required": False,
        "dependency_status": "not_required_for_scaffold",
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def build_tabular_ml_research_lanes(
    *,
    total_labeled_outcomes: int = 0,
    label_coverage: float = 0.0,
) -> dict[str, Any]:
    sample = max(0, int(total_labeled_outcomes or 0))
    lanes = [
        _tabular_lane(model_name="XGBoost Calibration Lane", total_labeled_outcomes=sample, label_coverage=label_coverage),
        _tabular_lane(model_name="LightGBM Calibration Lane", total_labeled_outcomes=sample, label_coverage=label_coverage),
        _tabular_lane(
            model_name="Tabular Foundation Model Research Lane",
            total_labeled_outcomes=sample,
            label_coverage=label_coverage,
            foundation=True,
        ),
    ]
    payload = {
        "ok": True,
        "status": "tabular_ml_research_lanes",
        "feature_set_version": TABULAR_FEATURE_SET_VERSION,
        "total_lanes": len(lanes),
        "training_enabled": False,
        "heavy_dependencies_added": False,
        "lanes": lanes,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def build_tabular_maturity_records(
    *,
    total_labeled_outcomes: int = 0,
    outcome_coverage_by_asset_type: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    sample = max(0, int(total_labeled_outcomes or 0))
    label_coverage = round(min(1.0, sample / 1000.0), 6)
    lanes = build_tabular_ml_research_lanes(total_labeled_outcomes=sample, label_coverage=label_coverage)["lanes"]
    records = []
    families = {
        "XGBoost Calibration Lane": "xgboost",
        "LightGBM Calibration Lane": "lightgbm",
        "Tabular Foundation Model Research Lane": "tabular_foundation_model",
    }
    for lane in lanes:
        status = lane["model_status"]
        records.append(
            {
                "model_family": families.get(lane["model_name"], lane["model_name"].lower().replace(" ", "_")),
                "model_name": lane["model_name"],
                "asset_type": "cross_asset",
                "market_type": "*",
                "model_maturity_status": status,
                "data_requirement_level": "high",
                "compute_requirement_level": "medium" if not lane["research_only"] else "high",
                "interpretability_score": 72 if not lane["research_only"] else 45,
                "current_sample_size": sample,
                "required_sample_size": TABULAR_REQUIRED_SAMPLE_SIZE if not lane["research_only"] else 5000,
                "outcome_coverage": label_coverage,
                "calibration_status": "not_ready" if sample < TABULAR_REQUIRED_SAMPLE_SIZE else "calibration_ready",
                "insufficient_sample": sample < TABULAR_REQUIRED_SAMPLE_SIZE,
                "blocked_reason": lane["blocked_reason"],
                "research_only": lane["research_only"],
                "affects_review_queue": False,
                "affects_execution": False,
                **locked_safety_flags(),
            }
        )
    return records
