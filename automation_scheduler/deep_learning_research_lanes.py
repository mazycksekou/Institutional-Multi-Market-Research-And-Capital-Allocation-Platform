from __future__ import annotations

from typing import Any

from .security_policy import locked_safety_flags


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
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
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
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
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
                **locked_safety_flags(),
            }
        )
    return records
