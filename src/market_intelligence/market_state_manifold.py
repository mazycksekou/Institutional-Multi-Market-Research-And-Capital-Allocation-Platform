from __future__ import annotations

import math
from typing import Any

from src.analytics.manifold_calibration import MIN_CLUSTER_SAMPLE, calibration_status_for_sample
from .manifold_cluster_registry import find_clusters, load_cluster_registry
from .manifold_feature_builder import COMMON_NUMERIC_FEATURES, FEATURE_NAMES, FEATURE_VECTOR_VERSION, build_manifold_feature_vector
from src.services.execution_service import detect_manifold_trap


MIN_NEIGHBOR_SAMPLE = 10


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def cosine_distance(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 1.0
    similarity = dot / (norm_a * norm_b)
    return round(max(0.0, min(2.0, 1.0 - similarity)), 6)


def euclidean_distance(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 1.0
    return round(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))) / math.sqrt(len(a)), 6)


def _centroid_weighted_vector(cluster: dict[str, Any], weights: list[float]) -> list[float]:
    centroid = cluster.get("centroid") if isinstance(cluster.get("centroid"), dict) else {}
    values = [float(centroid.get(name, 0.0) or 0.0) for name in FEATURE_NAMES]
    return [round(value * weight, 6) for value, weight in zip(values, weights)]


def nearest_clusters(feature_payload: dict[str, Any], registry: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    asset_type = str(feature_payload.get("asset_type") or "")
    clusters = find_clusters(registry, asset_type=asset_type)
    if not clusters:
        clusters = [row for row in registry.get("clusters", []) if isinstance(row, dict)]
    vector = list(feature_payload.get("weighted_feature_vector") or [])
    weights = list(feature_payload.get("feature_weights") or [1.0 for _ in FEATURE_NAMES])
    ranked = []
    for cluster in clusters:
        centroid = _centroid_weighted_vector(cluster, weights)
        cosine = cosine_distance(vector, centroid)
        euclidean = euclidean_distance(vector, centroid)
        ranked.append(
            {
                "cluster": cluster,
                "centroid_distance": round((cosine * 0.72) + (euclidean * 0.28), 6),
                "cosine_distance": cosine,
                "euclidean_distance": euclidean,
            }
        )
    return sorted(ranked, key=lambda row: (row["centroid_distance"], str(row["cluster"].get("manifold_cluster_id"))))[: max(1, limit)]


def nearest_historical_neighbors(
    feature_payload: dict[str, Any],
    records: list[dict[str, Any]] | None,
    *,
    distance_threshold: float = 0.28,
    limit: int = 50,
) -> dict[str, Any]:
    vector = list(feature_payload.get("weighted_feature_vector") or [])
    ranked = []
    for row in records or []:
        if not isinstance(row, dict):
            continue
        if not _has_labeled_outcome(row):
            continue
        candidate = row.get("weighted_feature_vector") or row.get("feature_vector")
        if not isinstance(candidate, list) or len(candidate) != len(vector):
            continue
        candidate_vector = [float(value or 0.0) for value in candidate]
        if row.get("feature_vector") and not row.get("weighted_feature_vector"):
            weights = list(feature_payload.get("feature_weights") or [1.0 for _ in FEATURE_NAMES])
            candidate_vector = [round(value * weight, 6) for value, weight in zip(candidate_vector, weights)]
        distance = cosine_distance(vector, candidate_vector)
        ranked.append({"distance": distance, "record": row})
    ranked = sorted(ranked, key=lambda item: item["distance"])[: max(1, limit)]
    within = [row for row in ranked if row["distance"] <= distance_threshold]
    return {
        "nearest_historical_neighbors": len(within),
        "nearest_neighbor_distance": round(ranked[0]["distance"], 6) if ranked else None,
        "neighbors": [row["record"] for row in within],
    }


def _has_labeled_outcome(row: dict[str, Any]) -> bool:
    for key in ("final_outcome", "paper_result", "settlement_result", "return_or_result"):
        value = row.get(key)
        if isinstance(value, bool):
            return True
        text = str(value or "").strip().lower()
        if text in {"yes", "win", "true", "hit", "profitable", "1", "no", "loss", "false", "miss", "unprofitable", "0"}:
            return True
    for key in ("paper_roi_estimate", "return_pct", "return"):
        value = row.get(key)
        try:
            if value not in (None, ""):
                float(value)
                return True
        except (TypeError, ValueError):
            continue
    return False


def _stats_for_cluster(cluster_id: str, calibration_report: dict[str, Any] | None, cluster: dict[str, Any]) -> dict[str, Any]:
    report_clusters = {}
    if isinstance(calibration_report, dict) and isinstance(calibration_report.get("clusters"), dict):
        report_clusters = calibration_report.get("clusters", {})
    stats = report_clusters.get(cluster_id)
    if isinstance(stats, dict):
        return dict(stats)
    # Registry clusters are prototypes, not evidence. Do not surface any historical
    # metric unless it came from the calibration report built from labeled outcomes.
    return {"sample_size": 0, "outcome_coverage": 0.0, "insufficient_sample": True}


def _liquidity_quality(features: dict[str, float]) -> str:
    liquidity = float(features.get("liquidity_score", 0.0) or 0.0)
    spread = float(features.get("spread_score", 0.0) or 0.0)
    combined = (liquidity * 0.65) + (spread * 0.35)
    if combined >= 0.75:
        return "strong"
    if combined >= 0.55:
        return "adequate"
    if combined >= 0.35:
        return "thin"
    return "poor"


def _ood_score(centroid_distance: float, nearest_neighbor_distance: float | None, features: dict[str, float], missing_features: list[str]) -> float:
    outlier = float(features.get("outlier_score", 0.0) or 0.0)
    stale = float(features.get("stale_data_risk", 0.0) or 0.0)
    critical_missing = len([name for name in missing_features if name in COMMON_NUMERIC_FEATURES])
    neighbor_component = 0.0
    if nearest_neighbor_distance is not None:
        neighbor_component = nearest_neighbor_distance * 55.0
    score = (centroid_distance * 210.0) + neighbor_component + (outlier * 35.0) + (stale * 8.0) + (critical_missing * 2.0)
    return round(_clamp(score), 2)


def _ood_risk(score: float) -> str:
    if score >= 75.0:
        return "extreme"
    if score >= 50.0:
        return "high"
    if score >= 28.0:
        return "moderate"
    return "low"


def _cluster_reliability(stats: dict[str, Any], ood_score: float, liquidity_quality: str) -> float:
    sample_size = int(stats.get("sample_size", 0) or 0)
    if sample_size < MIN_CLUSTER_SAMPLE or bool(stats.get("insufficient_sample", True)):
        return 0.0
    coverage = float(stats.get("outcome_coverage", 0.0) or 0.0)
    calibration_error = stats.get("calibration_error")
    sample_component = min(40.0, sample_size / MIN_CLUSTER_SAMPLE * 40.0)
    coverage_component = min(25.0, coverage * 25.0)
    liquidity_component = {"strong": 15.0, "adequate": 11.0, "thin": 5.0, "poor": 0.0}.get(liquidity_quality, 0.0)
    error_component = 10.0
    if calibration_error is not None:
        error_component = max(0.0, 10.0 - float(calibration_error) * 20.0)
    ood_penalty = min(20.0, ood_score * 0.20)
    return round(_clamp(sample_component + coverage_component + liquidity_component + error_component - ood_penalty), 2)


def _historical_field(stats: dict[str, Any], *keys: str) -> Any:
    if bool(stats.get("insufficient_sample", True)):
        return None
    for key in keys:
        if stats.get(key) is not None:
            return stats.get(key)
    return None


def _review_adjustment(
    *,
    reliability: float,
    ood_score: float,
    no_bet_score: float,
    no_trade_score: float,
    insufficient_sample: bool,
    liquidity_quality: str,
) -> float:
    adjustment = (reliability - 50.0) * 0.12
    adjustment -= ood_score * 0.08
    adjustment -= max(no_bet_score, no_trade_score) * 0.12
    if insufficient_sample:
        adjustment -= 6.0
    if liquidity_quality == "poor":
        adjustment -= 7.0
    elif liquidity_quality == "strong":
        adjustment += 3.0
    return round(max(-30.0, min(18.0, adjustment)), 2)


def _has_critical_missing(feature_payload: dict[str, Any]) -> bool:
    missing = set(feature_payload.get("missing_features") or [])
    common_missing = missing.intersection(COMMON_NUMERIC_FEATURES)
    features = feature_payload.get("normalized_features") or {}
    no_liquidity = "liquidity_score" in common_missing and float(features.get("liquidity_score", 0.0) or 0.0) <= 0.0
    no_price_context = "market_implied_probability" in common_missing and "contract_price" in missing
    no_spread = "spread_score" in common_missing and float(features.get("spread_score", 0.0) or 0.0) <= 0.0
    return bool(no_liquidity and no_price_context and no_spread)


def _recommended_action(
    *,
    asset_type: str,
    ood_risk: str,
    insufficient_sample: bool,
    trap: dict[str, Any],
    reliability: float,
    liquidity_quality: str,
    critical_missing: bool,
    fatal_blockers: list[str],
) -> str:
    if fatal_blockers:
        return "NO_TRADE" if asset_type in {"stock", "crypto", "etf", "bond_rate", "major_asset"} else "NO_BET"
    trap_action = str(trap.get("recommended_action") or "")
    if trap_action in {"NO_BET", "NO_TRADE"}:
        return trap_action
    if critical_missing:
        return "DATA_INSUFFICIENT"
    if ood_risk == "extreme":
        return "DATA_INSUFFICIENT"
    if ood_risk == "high":
        return "WATCHLIST_REVIEW" if liquidity_quality in {"adequate", "strong"} else "NO_REVIEW"
    if trap.get("trap_cluster_detected"):
        return "LOW_PRIORITY_REVIEW"
    if insufficient_sample:
        return "WATCHLIST_REVIEW" if liquidity_quality in {"adequate", "strong"} else "LOW_PRIORITY_REVIEW"
    if reliability >= 70.0 and liquidity_quality in {"adequate", "strong"}:
        return "ACTIVE_REVIEW"
    if reliability >= 45.0:
        return "WATCHLIST_REVIEW"
    if reliability >= 25.0:
        return "LOW_PRIORITY_REVIEW"
    return "NO_REVIEW"


def map_market_state(
    item: dict[str, Any] | None,
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    source = dict(item or {})
    feature_payload = build_manifold_feature_vector(source)
    registry_payload = registry or load_cluster_registry(base_data_dir=base_data_dir, create_if_missing=True)
    ranked = nearest_clusters(feature_payload, registry_payload, limit=5)
    best = ranked[0] if ranked else {"cluster": {}, "centroid_distance": 1.0}
    cluster = best.get("cluster") or {}
    cluster_id = str(cluster.get("manifold_cluster_id") or "unknown_cluster")
    neighbor_result = nearest_historical_neighbors(feature_payload, historical_records)
    stats = _stats_for_cluster(cluster_id, calibration_report, cluster)
    sample_size = int(stats.get("sample_size", 0) or 0)
    neighbor_count = int(neighbor_result.get("nearest_historical_neighbors", 0) or 0)
    neighbor_sample_size = sample_size if sample_size > 0 else neighbor_count
    insufficient_sample = sample_size < MIN_CLUSTER_SAMPLE
    features = feature_payload.get("normalized_features") or {}
    liquidity_quality = _liquidity_quality(features)
    centroid_distance = float(best.get("centroid_distance", 1.0) or 1.0)
    nearest_neighbor_distance = neighbor_result.get("nearest_neighbor_distance")
    ood_score = _ood_score(centroid_distance, nearest_neighbor_distance, features, list(feature_payload.get("missing_features") or []))
    ood_risk = _ood_risk(ood_score)
    reliability = _cluster_reliability(stats, ood_score, liquidity_quality)
    calibration_status = calibration_status_for_sample(sample_size)
    trap = detect_manifold_trap(
        asset_type=str(feature_payload.get("asset_type") or "unknown"),
        cluster_id=cluster_id,
        cluster_name=cluster.get("manifold_cluster_name"),
        normalized_features=features,
        cluster_stats=stats,
        source_item=source,
    )
    no_bet_score = float(trap.get("no_bet_trap_score", 0.0) or 0.0)
    no_trade_score = float(trap.get("no_trade_trap_score", 0.0) or 0.0)
    adjustment = _review_adjustment(
        reliability=reliability,
        ood_score=ood_score,
        no_bet_score=no_bet_score,
        no_trade_score=no_trade_score,
        insufficient_sample=insufficient_sample,
        liquidity_quality=liquidity_quality,
    )
    fatal_blockers = [
        str(reason)
        for reason in source.get("blockers", [])
        if "fatal" in str(reason).lower() or "execution" in str(reason).lower() or "provider_write" in str(reason).lower()
    ]
    critical_missing = _has_critical_missing(feature_payload)
    action = _recommended_action(
        asset_type=str(feature_payload.get("asset_type") or "unknown"),
        ood_risk=ood_risk,
        insufficient_sample=insufficient_sample,
        trap=trap,
        reliability=reliability,
        liquidity_quality=liquidity_quality,
        critical_missing=critical_missing,
        fatal_blockers=fatal_blockers,
    )
    if ood_risk in {"high", "extreme"}:
        confidence_adjustment = -min(35.0, ood_score * 0.35)
    else:
        confidence_adjustment = -min(15.0, ood_score * 0.12)
    result = {
        "manifold_cluster_id": cluster_id,
        "manifold_cluster_name": cluster.get("manifold_cluster_name", "unknown"),
        "manifold_family": cluster.get("manifold_family", "unknown"),
        "asset_type": feature_payload.get("asset_type"),
        "market_type": feature_payload.get("market_type"),
        "provider_name": feature_payload.get("provider_name"),
        "feature_vector_version": feature_payload.get("feature_vector_version", FEATURE_VECTOR_VERSION),
        "nearest_historical_neighbors": neighbor_count,
        "neighbor_sample_size": neighbor_sample_size,
        "calibration_sample_size": sample_size,
        "centroid_distance": round(centroid_distance, 6),
        "nearest_neighbor_distance": nearest_neighbor_distance,
        "out_of_distribution_score": ood_score,
        "out_of_distribution_risk": ood_risk,
        "historical_win_rate": _historical_field(stats, "win_rate"),
        "historical_roi": _historical_field(stats, "historical_roi", "average_return"),
        "historical_edge": _historical_field(stats, "expected_value"),
        "historical_profit_factor": _historical_field(stats, "profit_factor"),
        "historical_max_adverse_excursion": _historical_field(stats, "average_mae"),
        "historical_max_favorable_excursion": _historical_field(stats, "average_mfe"),
        "calibration_status": calibration_status,
        "insufficient_sample": bool(insufficient_sample),
        "liquidity_quality": liquidity_quality,
        "cluster_reliability_score": reliability,
        "cluster_trap_risk_score": round(max(no_bet_score, no_trade_score), 2),
        "no_bet_trap_score": round(no_bet_score, 2),
        "no_trade_trap_score": round(no_trade_score, 2),
        "trap_cluster_detected": bool(trap.get("trap_cluster_detected", False)),
        "trap_cluster_id": trap.get("trap_cluster_id"),
        "trap_reasons": list(trap.get("trap_reasons") or [])[:10],
        "review_priority_adjustment": adjustment,
        "confidence_adjustment": round(confidence_adjustment, 2),
        "recommended_action": action,
        "recommended_unit_size": 0,
        "nearest_cluster_candidates": [
            {
                "manifold_cluster_id": row["cluster"].get("manifold_cluster_id"),
                "manifold_cluster_name": row["cluster"].get("manifold_cluster_name"),
                "centroid_distance": row.get("centroid_distance"),
            }
            for row in ranked[:5]
        ],
        "markov_hmm_context": {
            "observed_state": cluster.get("manifold_cluster_name", "unknown"),
            "hidden_regime": None,
            "manifold_cluster_id": cluster_id,
            "transition_matrix_bucket": cluster_id,
            "next_window_follow_through_probability": None,
            "next_window_failure_probability": None,
            "next_window_liquidity_trap_probability": None,
            "integration_status": "not_configured",
        },
        "missing_features": list(feature_payload.get("missing_features") or [])[:25],
        "normalized_feature_summary": {
            "liquidity_score": features.get("liquidity_score"),
            "spread_score": features.get("spread_score"),
            "risk_score": features.get("risk_score"),
            "estimated_edge": features.get("estimated_edge"),
            "confidence_score": features.get("confidence_score"),
            "outlier_score": features.get("outlier_score"),
        },
        "source_summary": feature_payload.get("source_summary", {}),
        "fatal_safety_blockers": fatal_blockers,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    return result
