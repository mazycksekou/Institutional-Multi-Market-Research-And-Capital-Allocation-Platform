from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import ResearchLaneDescriptor


def build_research_lane_descriptor(
    lane_id: str,
    name: str,
    *,
    topic: str = "",
    owner: str = "research",
    status: str = "planned",
    tags: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ResearchLaneDescriptor:
    cleaned_tags = tuple(str(tag).strip() for tag in (tags or ()) if str(tag).strip())
    return ResearchLaneDescriptor(
        lane_id=str(lane_id).strip() or "lane",
        name=str(name).strip() or "research lane",
        topic=str(topic).strip(),
        owner=str(owner).strip() or "research",
        status=str(status).strip() or "planned",
        tags=cleaned_tags,
        metadata=dict(metadata or {}),
    )


def list_research_lane_tags(descriptor: ResearchLaneDescriptor) -> tuple[str, ...]:
    return tuple(descriptor.tags)


TABULAR_FEATURE_SET_VERSION = "cross_asset_tabular_features_v1"
TABULAR_REQUIRED_SAMPLE_SIZE = 500

DEEP_RESEARCH_LANES = (
    {
        "model_family": "lstm",
        "model_name": "LSTM Sequence Research Lane",
        "research_question": "Can ordered market-state sequences improve review diagnostics after enough labeled history exists?",
        "data_required": "longitudinal labeled market-state sequences",
        "minimum_dataset_size_estimate": 10000,
        "dependency_requirement": "optional_deep_learning_stack_not_installed",
    },
    {
        "model_family": "transformer",
        "model_name": "Transformer Sequence Research Lane",
        "research_question": "Can attention-based sequence models detect cross-market context shifts without leakage?",
        "data_required": "large labeled cross-asset sequence corpus",
        "minimum_dataset_size_estimate": 50000,
        "dependency_requirement": "optional_deep_learning_stack_not_installed",
    },
    {
        "model_family": "autoencoder",
        "model_name": "Autoencoder OOD Research Lane",
        "research_question": "Can reconstruction error improve out-of-distribution diagnostics?",
        "data_required": "broad unlabeled feature snapshots plus labeled holdout outcomes",
        "minimum_dataset_size_estimate": 25000,
        "dependency_requirement": "optional_deep_learning_stack_not_installed",
    },
    {
        "model_family": "deep_manifold_learning",
        "model_name": "Deep Manifold Learning Research Lane",
        "research_question": "Can learned latent spaces outperform deterministic manifolds after calibration?",
        "data_required": "large cross-asset feature and outcome history",
        "minimum_dataset_size_estimate": 50000,
        "dependency_requirement": "optional_deep_learning_stack_not_installed",
    },
    {
        "model_family": "full_graph_neural_network",
        "model_name": "Full Graph Neural Network Research Lane",
        "research_question": "Can graph message passing add value over compact relationship maps?",
        "data_required": "validated event-entity graph with labeled outcomes",
        "minimum_dataset_size_estimate": 100000,
        "dependency_requirement": "optional_graph_deep_learning_stack_not_installed",
    },
    {
        "model_family": "graph_neural_network",
        "model_name": "Graph Neural Network Research Lane",
        "research_question": "Can smaller GNN diagnostics improve relationship scoring after graph labels mature?",
        "data_required": "relationship graph snapshots with outcome labels",
        "minimum_dataset_size_estimate": 50000,
        "dependency_requirement": "optional_graph_deep_learning_stack_not_installed",
    },
    {
        "model_family": "deep_metric_learning",
        "model_name": "Deep Metric Learning Research Lane",
        "research_question": "Can learned distance metrics improve nearest-neighbor state mapping?",
        "data_required": "large labeled positive and negative market-state pairs",
        "minimum_dataset_size_estimate": 50000,
        "dependency_requirement": "optional_deep_learning_stack_not_installed",
    },
)


def _locked_safety_flags() -> dict[str, Any]:
    return {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "dry_run": True,
        "simulation_only": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "secrets_detected": False,
    }


def _lane(template: dict[str, Any]) -> dict[str, Any]:
    payload = {
        **template,
        "compute_requirement_level": "high",
        "blocked_reason": "research_only_disabled_until_dataset_safety_and_calibration_review",
        "current_status": "research_only_disabled",
        "model_maturity_status": "research_only",
        "disabled": True,
        "research_only": True,
        "allowed_outputs": "documentation_only",
        "training_enabled": False,
        "affects_review_queue": False,
        "affects_execution": False,
    }
    payload.update(_locked_safety_flags())
    return payload


def build_deep_learning_research_lanes() -> dict[str, Any]:
    lanes = [_lane(dict(template)) for template in DEEP_RESEARCH_LANES]
    payload = {
        "ok": True,
        "status": "deep_learning_research_lanes",
        "total_lanes": len(lanes),
        "training_enabled": False,
        "heavy_dependencies_added": False,
        "lanes": lanes,
    }
    payload.update(_locked_safety_flags())
    return payload


def build_deep_learning_maturity_records() -> list[dict[str, Any]]:
    records = []
    for lane in build_deep_learning_research_lanes()["lanes"]:
        records.append(
            {
                "model_family": lane["model_family"],
                "model_name": lane["model_name"],
                "asset_type": "cross_asset",
                "market_type": "research",
                "model_maturity_status": "research_only",
                "data_requirement_level": "very_high",
                "compute_requirement_level": lane["compute_requirement_level"],
                "interpretability_score": 35,
                "current_sample_size": 0,
                "required_sample_size": lane["minimum_dataset_size_estimate"],
                "outcome_coverage": 0.0,
                "calibration_status": "disabled_research_only",
                "insufficient_sample": True,
                "blocked_reason": lane["blocked_reason"],
                "research_only": True,
                "affects_review_queue": False,
                "affects_execution": False,
                **_locked_safety_flags(),
            }
        )
    return records


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
    payload.update(_locked_safety_flags())
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
    payload.update(_locked_safety_flags())
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
                **_locked_safety_flags(),
            }
        )
    return records
