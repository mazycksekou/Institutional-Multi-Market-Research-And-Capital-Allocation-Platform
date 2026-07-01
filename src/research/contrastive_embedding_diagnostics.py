from __future__ import annotations

from typing import Any, Mapping

from src.security.policy import locked_safety_flags


def _outcome_label(row: Mapping[str, Any]) -> str | None:
    value = str(row.get("final_outcome") or row.get("outcome") or row.get("label") or row.get("paper_result") or "").strip().lower()
    if value in {"win", "yes", "true", "1", "profitable", "profit"}:
        return "profitable"
    if value in {"loss", "no", "false", "0", "losing", "negative"}:
        return "losing"
    return None


def run_nonlinear_embedding_diagnostics(
    candidate: Mapping[str, Any] | None = None,
    *,
    historical_records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    from src.analytics.advanced_shape_diagnostics import vector_context

    context = vector_context(candidate or {}, historical_records or [])
    count = int(context["record_count"])
    nearest = context["nearest_distance"]
    if count < 3:
        density = "data_insufficient"
        isolated = True
        extrapolation = True
        confidence = 0.0
    elif nearest is None or nearest > 25.0:
        density = "isolated"
        isolated = True
        extrapolation = True
        confidence = 15.0
    elif int(context["neighbor_density"]) <= 2:
        density = "sparse_region"
        isolated = False
        extrapolation = False
        confidence = 35.0
    else:
        density = "dense_cluster"
        isolated = False
        extrapolation = False
        confidence = min(100.0, float(context["neighbor_density"]) * 12.0)
    return {
        "ok": True,
        "status": "embedding_diagnostics_complete",
        "manifold_density": density,
        "embedding_method": "deterministic_vector_similarity_fallback",
        "embedding_coordinates_redacted": [round(float(value), 6) for value in list(context["candidate_vector"][:2])],
        "nearest_cluster_distance": round(float(nearest), 6) if nearest is not None else None,
        "isolated_candidate": bool(isolated),
        "extrapolation_zone": bool(extrapolation),
        "bifurcation_risk": "moderate" if density == "sparse_region" else ("high" if density == "isolated" else "low"),
        "embedding_status": "deterministic_fallback",
        "embedding_confidence_score": round(confidence, 4),
        "red_team_only": True,
        **locked_safety_flags(),
    }


def run_contrastive_embedding_diagnostics(
    candidate: Mapping[str, Any] | None = None,
    *,
    labeled_records: list[Mapping[str, Any]] | None = None,
    minimum_labeled: int = 30,
) -> dict[str, Any]:
    from src.analytics.advanced_shape_diagnostics import vector_context, vector_similarity

    rows = [row for row in (labeled_records or []) if isinstance(row, Mapping) and _outcome_label(row)]
    if len(rows) < int(minimum_labeled):
        return {
            "ok": True,
            "status": "blocked_insufficient_data",
            "similarity_to_profitable_neighbors": 0.0,
            "similarity_to_losing_neighbors": 0.0,
            "contrastive_edge_signal": 0.0,
            "nearest_profitable_neighbor_count": 0,
            "nearest_losing_neighbor_count": 0,
            "contrastive_status": "blocked_insufficient_data",
            "contrastive_trap_risk": "data_insufficient",
            "insufficient_sample": True,
            "blocked_reason": "labeled_settled_record_count_below_minimum",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    context = vector_context(candidate or {}, rows)
    candidate_vector = list(context["candidate_vector"])
    paired = []
    for row, vec in zip(rows, context["record_vectors"]):
        paired.append((_outcome_label(row), vector_similarity(candidate_vector, vec)))
    profitable = sorted([sim for label, sim in paired if label == "profitable"], reverse=True)[:10]
    losing = sorted([sim for label, sim in paired if label == "losing"], reverse=True)[:10]
    prof_score = sum(profitable) / len(profitable) if profitable else 0.0
    loss_score = sum(losing) / len(losing) if losing else 0.0
    signal = prof_score - loss_score
    return {
        "ok": True,
        "status": "contrastive_diagnostics_complete",
        "similarity_to_profitable_neighbors": round(prof_score, 6),
        "similarity_to_losing_neighbors": round(loss_score, 6),
        "contrastive_edge_signal": round(signal, 6),
        "nearest_profitable_neighbor_count": len(profitable),
        "nearest_losing_neighbor_count": len(losing),
        "contrastive_status": "deterministic_similarity_fallback",
        "contrastive_trap_risk": "high" if signal < -0.05 else ("moderate" if abs(signal) <= 0.05 else "low"),
        "insufficient_sample": False,
        "blocked_reason": None,
        "red_team_only": True,
        **locked_safety_flags(),
    }
