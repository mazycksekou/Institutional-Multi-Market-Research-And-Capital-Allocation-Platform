from __future__ import annotations

import math
from typing import Any, Mapping

from .advanced_red_team_provider_policy import evaluate_advanced_red_team_provider
from .bayesian_structural_baseline import run_bayesian_structural_baseline
from .causal_discovery_research import run_causal_discovery_research
from .conformal_uncertainty import run_conformal_uncertainty
from .contrastive_embedding_diagnostics import run_contrastive_embedding_diagnostics, run_nonlinear_embedding_diagnostics
from .dynamical_systems_diagnostics import run_dynamical_systems_diagnostics, run_sliding_window_topology
from .information_theory_diagnostics import run_information_theory_diagnostics
from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import detect_execution_authority_violations, locked_safety_flags
from .topological_red_team import run_topological_red_team


ADVANCED_DIAGNOSTIC_IDS = (
    "topological_persistent_homology",
    "nonlinear_embedding_shape",
    "sliding_window_topology",
    "graph_density_clustering",
    "information_theory",
    "conformal_uncertainty",
    "contrastive_embedding",
    "dynamical_systems_s_map",
    "causal_discovery_research",
    "bayesian_structural_baseline",
)


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isfinite(parsed):
        return parsed
    return None


def _safe_flags() -> dict[str, Any]:
    return {"red_team_only": True, **locked_safety_flags()}


def get_advanced_diagnostic_registry() -> dict[str, dict[str, Any]]:
    rows = [
        ("topological_persistent_homology", "Topological Data Analysis", "research_only", "blocked_missing_dependency"),
        ("nonlinear_embedding_shape", "UMAP/Laplacian Fallback Shape Diagnostics", "research_only", "deterministic_fallback_ready"),
        ("sliding_window_topology", "Sliding Window Time-Series Topology", "calibration_only", "deterministic_fallback_ready"),
        ("graph_density_clustering", "Graph Density Clustering", "calibration_only", "deterministic_fallback_ready"),
        ("information_theory", "Information-Theory Diagnostics", "active_calibration", "deterministic_fallback_ready"),
        ("conformal_uncertainty", "Conformal Prediction", "blocked_insufficient_data", "needs_calibration_outcomes"),
        ("contrastive_embedding", "Contrastive Embedding Diagnostics", "research_only", "needs_labeled_outcomes"),
        ("dynamical_systems_s_map", "Empirical Dynamic Modeling S-map", "research_only", "deterministic_fallback_ready"),
        ("causal_discovery_research", "Causal Discovery Research", "research_only", "not_ready"),
        ("bayesian_structural_baseline", "Bayesian Structural Baseline", "calibration_only", "needs_baseline_data"),
    ]
    return {
        diagnostic_id: {
            "diagnostic_id": diagnostic_id,
            "diagnostic_name": name,
            "maturity_status": maturity,
            "diagnostic_status": status,
            "enabled": True,
            "affects_review_queue": True,
            "affects_ranking": False,
            "affects_execution": False,
            "red_team_only": True,
            **locked_safety_flags(),
        }
        for diagnostic_id, name, maturity, status in rows
    }


def _vector_from_record(record: Mapping[str, Any], *, feature_names: list[str] | None = None) -> list[float]:
    safe = redact_sensitive(dict(record or {}))
    keys = feature_names or sorted(
        key
        for key, value in safe.items()
        if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}
    )
    return [float(_num(safe.get(key)) or 0.0) for key in keys]


def _feature_names(candidate: Mapping[str, Any], records: list[Mapping[str, Any]]) -> list[str]:
    keys: set[str] = set()
    for row in [candidate, *records[:100]]:
        for key, value in dict(row or {}).items():
            if _num(value) is not None and key.lower() not in {"final_outcome", "outcome", "label", "target"}:
                keys.add(str(key))
    return sorted(keys)[:30]


def euclidean_distance(left: list[float], right: list[float]) -> float:
    length = max(len(left), len(right))
    a = left + [0.0] * (length - len(left))
    b = right + [0.0] * (length - len(right))
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(length)))


def vector_similarity(left: list[float], right: list[float]) -> float:
    dist = euclidean_distance(left, right)
    return 1.0 / (1.0 + dist)


def vector_context(candidate: Mapping[str, Any], records: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    rows = [redact_sensitive(dict(row)) for row in (records or []) if isinstance(row, Mapping)]
    names = _feature_names(candidate, rows)
    candidate_vector = _vector_from_record(candidate, feature_names=names)
    record_vectors = [_vector_from_record(row, feature_names=names) for row in rows]
    distances = sorted(euclidean_distance(candidate_vector, vec) for vec in record_vectors)
    nearest = distances[0] if distances else None
    density = sum(1 for dist in distances[:20] if dist <= max(1.0, (nearest or 0.0) * 1.5)) if distances else 0
    return {
        "feature_names": names,
        "candidate_vector": candidate_vector,
        "record_vectors": record_vectors,
        "nearest_distance": nearest,
        "neighbor_density": density,
        "record_count": len(record_vectors),
    }


def run_graph_density_diagnostics(
    candidate: Mapping[str, Any] | None = None,
    *,
    historical_records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    context = vector_context(safe_candidate, historical_records or [])
    count = int(context["record_count"])
    if count < 5:
        return {
            "ok": True,
            "status": "blocked_insufficient_data",
            "graph_cluster_id": None,
            "graph_cluster_density": 0.0,
            "graph_noise_point": True,
            "sparse_region_risk": "data_insufficient",
            "transition_region_risk": "data_insufficient",
            "hdbscan_status": "knn_fallback_insufficient_data",
            "cluster_confidence_score": 0.0,
            "insufficient_sample": True,
            "blocked_reason": "historical_record_count_below_5",
            **_safe_flags(),
        }
    density = int(context["neighbor_density"])
    nearest = float(context["nearest_distance"] or 0.0)
    sparse = density <= 2 or nearest > 25.0
    transition = 2 < density <= 5
    return {
        "ok": True,
        "status": "graph_density_complete",
        "graph_cluster_id": "knn_dense_region" if not sparse else "knn_sparse_region",
        "graph_cluster_density": round(min(1.0, density / 10.0), 6),
        "graph_noise_point": bool(sparse),
        "sparse_region_risk": "high" if sparse else ("moderate" if transition else "low"),
        "transition_region_risk": "moderate" if transition else "low",
        "hdbscan_status": "knn_graph_density_fallback",
        "cluster_confidence_score": round(min(100.0, density * 10.0), 4),
        "insufficient_sample": False,
        "blocked_reason": None,
        **_safe_flags(),
    }


def _series_from_inputs(candidate: Mapping[str, Any], sequences: Mapping[str, Any] | None) -> list[float]:
    if isinstance(sequences, Mapping):
        for key in ("odds_sequence", "liquidity_sequence", "volume_sequence", "line_movement_sequence", "price_sequence"):
            values = sequences.get(key)
            if isinstance(values, list):
                parsed = [_num(item) for item in values]
                return [float(item) for item in parsed if item is not None]
    for key in ("odds_sequence", "liquidity_sequence", "volume_sequence", "line_movement_sequence", "price_sequence", "sequence"):
        values = candidate.get(key)
        if isinstance(values, list):
            parsed = [_num(item) for item in values]
            return [float(item) for item in parsed if item is not None]
    return []


def run_advanced_shape_diagnostics(
    candidate: Mapping[str, Any] | None = None,
    *,
    historical_records: list[Mapping[str, Any]] | None = None,
    labeled_records: list[Mapping[str, Any]] | None = None,
    calibration_records: list[Mapping[str, Any]] | None = None,
    sequences: Mapping[str, Any] | None = None,
    provider: str | None = None,
    fatal_safety_blocker: bool = False,
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    policy = evaluate_advanced_red_team_provider(provider)
    if not bool(policy.get("ok")):
        return policy

    records = [redact_sensitive(dict(row)) for row in (historical_records or []) if isinstance(row, Mapping)]
    labeled = [redact_sensitive(dict(row)) for row in (labeled_records or []) if isinstance(row, Mapping)]
    calibration = [redact_sensitive(dict(row)) for row in (calibration_records or []) if isinstance(row, Mapping)]
    series = _series_from_inputs(safe_candidate, sequences)
    tda = run_topological_red_team(safe_candidate, historical_records=records)
    embedding = run_nonlinear_embedding_diagnostics(safe_candidate, historical_records=records)
    sliding = run_sliding_window_topology(series)
    graph = run_graph_density_diagnostics(safe_candidate, historical_records=records)
    info = run_information_theory_diagnostics(records=labeled or records, candidate=safe_candidate)
    conformal = run_conformal_uncertainty(safe_candidate, calibration_records=calibration)
    contrastive = run_contrastive_embedding_diagnostics(safe_candidate, labeled_records=labeled)
    dynamics = run_dynamical_systems_diagnostics(series)
    causal = run_causal_discovery_research(safe_candidate, records=labeled or records)
    baseline = run_bayesian_structural_baseline(safe_candidate, baseline_records=records)
    violations = detect_execution_authority_violations({"candidate": safe_candidate})

    no_bet_reasons: list[str] = []
    no_trade_reasons: list[str] = []
    missing_inputs: list[str] = []
    if tda.get("topological_risk") in {"high", "extreme"}:
        no_bet_reasons.append("high_topological_risk")
    if embedding.get("isolated_candidate") or graph.get("sparse_region_risk") == "high":
        no_bet_reasons.append("sparse_or_isolated_manifold_region")
    if conformal.get("uncertainty_too_wide"):
        no_bet_reasons.append(conformal.get("conformal_no_bet_reason") or "conformal_interval_too_wide")
        missing_inputs.append("more_calibration_outcomes")
    if info.get("fake_edge_information_risk"):
        no_bet_reasons.append("static_correlation_not_predictive")
    if dynamics.get("stochastic_warning"):
        no_bet_reasons.append("forecast_skill_not_above_surrogate")
    if causal.get("causal_graph_support") in {"no", "not_ready"}:
        no_bet_reasons.extend(list(causal.get("causal_no_bet_reasons") or [])[:5])
    if baseline.get("counterfactual_no_edge_warning"):
        no_bet_reasons.append("counterfactual_baseline_does_not_support_edge")
    if contrastive.get("contrastive_edge_signal", 0.0) > 0 and (info.get("fake_edge_information_risk") or causal.get("causal_graph_support") in {"no", "not_ready"}):
        no_bet_reasons.append("profitable_neighbor_but_causal_information_checks_failed")
    if fatal_safety_blocker or violations:
        no_bet_reasons.append("fatal_safety_blocker")
        no_trade_reasons.append("fatal_safety_blocker")

    insufficient = any(
        bool(row.get("insufficient_sample") or row.get("insufficient_sequence_length"))
        for row in (tda, sliding, conformal, contrastive, causal, baseline)
    )
    blocked_reasons = [
        str(row.get("blocked_reason"))
        for row in (tda, embedding, sliding, graph, conformal, contrastive, dynamics, causal, baseline)
        if row.get("blocked_reason")
    ]
    adjustment = "NONE"
    if fatal_safety_blocker or violations:
        adjustment = "NO_BET" if str(safe_candidate.get("asset_type") or safe_candidate.get("market_type") or "").lower() in {"sportsbook", "prediction_market"} else "NO_TRADE"
    elif conformal.get("uncertainty_too_wide") or insufficient:
        adjustment = "DATA_INSUFFICIENT"
    elif no_bet_reasons:
        adjustment = "LOWER_CONFIDENCE"

    return {
        "ok": True,
        "status": "advanced_shape_diagnostics_complete",
        "candidate_id": safe_candidate.get("candidate_id") or safe_candidate.get("id") or safe_candidate.get("ticker"),
        "provider_policy": policy,
        "deepseek_used": False,
        "openai_used": False,
        "external_ai_call_performed": False,
        "diagnostic_registry": get_advanced_diagnostic_registry(),
        "topology": tda,
        "embedding": embedding,
        "sliding_window_topology": sliding,
        "graph_density": graph,
        "information_theory": info,
        "conformal_uncertainty": conformal,
        "contrastive_embedding": contrastive,
        "dynamical_systems": dynamics,
        "causal_discovery": causal,
        "bayesian_structural_baseline": baseline,
        "topological_risk": tda.get("topological_risk", "data_insufficient"),
        "manifold_density": embedding.get("manifold_density", "data_insufficient"),
        "conformal_interval_width": conformal.get("conformal_interval_width"),
        "transfer_entropy_score": info.get("transfer_entropy_score"),
        "mutual_information_score": info.get("mutual_information_score"),
        "causal_graph_support": causal.get("causal_graph_support", "not_ready"),
        "dynamical_predictability": dynamics.get("dynamical_predictability", "data_insufficient"),
        "contrastive_edge_signal": contrastive.get("contrastive_edge_signal"),
        "graph_cluster_density": graph.get("graph_cluster_density"),
        "sparse_region_risk": graph.get("sparse_region_risk"),
        "counterfactual_significance": baseline.get("counterfactual_significance"),
        "advanced_red_team_status": "fatal_safety_blocked" if fatal_safety_blocker or violations else ("data_insufficient" if insufficient else "diagnostics_complete"),
        "recommended_action_adjustment": adjustment,
        "no_bet_reasons": sorted(set(reason for reason in no_bet_reasons if reason))[:25],
        "no_trade_reasons": sorted(set(reason for reason in no_trade_reasons if reason))[:25],
        "missing_inputs": sorted(set(missing_inputs + blocked_reasons))[:25],
        "insufficient_sample": bool(insufficient),
        "blocked_reason": ";".join(sorted(set(blocked_reasons))) if blocked_reasons else None,
        "fatal_safety_blocker": bool(fatal_safety_blocker or violations),
        **secret_safety_fields(source_payload=candidate, redacted_payload=safe_candidate),
        **_safe_flags(),
    }
