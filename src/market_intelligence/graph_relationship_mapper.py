from __future__ import annotations

from typing import Any

from .manifold import GRAPH_RELATIONSHIP_VERSION, infer_graph_asset_type, relationship_templates_for_item
from src.security.policy import locked_safety_flags


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed > 1.0:
        parsed = parsed / 100.0
    return max(0.0, min(1.0, parsed))


def _field_score(item: dict[str, Any], fields: list[str]) -> tuple[float, list[str]]:
    scores = []
    missing = []
    for field in fields:
        value = _num(item.get(field))
        if value is None:
            missing.append(field)
        else:
            scores.append(value)
    if not scores:
        return 0.0, missing
    return round(sum(scores) / len(scores), 6), missing


def map_graph_relationships(item: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(item or {})
    asset_type = infer_graph_asset_type(source)
    templates = relationship_templates_for_item(source)
    relationship_paths = []
    causal_hypotheses = []
    correlation_warnings = []
    graph_risk_flags = []
    for template in templates:
        fields = list(template.get("fields") or [])
        strength, missing = _field_score(source, fields)
        path = list(template.get("path") or [])
        risk_flags = []
        path_text = " -> ".join(path)
        if "fake_edge_risk" in path or "momentum_trap" in path or "slippage" in path:
            if strength >= 0.55 or missing:
                risk_flags.append(path[-1])
        if missing:
            correlation_warnings.append(
                {
                    "relationship_path": path_text,
                    "warning": "missing_inputs_prevent_causal_or_directional_claim",
                    "missing_fields": missing[:10],
                }
            )
        relationship_paths.append(
            {
                "relationship_path": path_text,
                "nodes": path,
                "edge_count": max(0, len(path) - 1),
                "relationship_strength": strength,
                "missing_fields": missing[:10],
                "hypothesis": template.get("hypothesis"),
                "risk_flags": risk_flags,
            }
        )
        causal_hypotheses.append(template.get("hypothesis"))
        graph_risk_flags.extend(risk_flags)
    strongest = sorted(relationship_paths, key=lambda row: row["relationship_strength"], reverse=True)[:5]
    node_count = len({node for row in relationship_paths for node in row["nodes"]})
    edge_count = sum(row["edge_count"] for row in relationship_paths)
    average_strength = round(sum(row["relationship_strength"] for row in relationship_paths) / len(relationship_paths), 6) if relationship_paths else 0.0
    missing_penalty = min(0.45, len(correlation_warnings) * 0.05)
    graph_confidence = round(max(0.0, min(1.0, average_strength * 0.75 + 0.25 - missing_penalty)), 6)
    review_adjustment = 0.0
    if graph_risk_flags:
        review_adjustment -= min(12.0, len(set(graph_risk_flags)) * 4.0)
    elif graph_confidence >= 0.70:
        review_adjustment += 2.0
    payload = {
        "ok": True,
        "status": "graph_relationships_mapped",
        "graph_version": GRAPH_RELATIONSHIP_VERSION,
        "asset_type": asset_type,
        "market_type": source.get("market_type") or asset_type,
        "graph_node_count": node_count,
        "graph_edge_count": edge_count,
        "relationship_paths": relationship_paths,
        "strongest_relationships": strongest,
        "causal_hypotheses": [value for value in causal_hypotheses if value],
        "correlation_warnings": correlation_warnings[:10],
        "graph_confidence_score": graph_confidence,
        "graph_review_adjustment": round(review_adjustment, 2),
        "graph_risk_flags": sorted(set(graph_risk_flags)),
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
