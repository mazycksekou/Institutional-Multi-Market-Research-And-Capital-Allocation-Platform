from __future__ import annotations

from typing import Any

from src.market_intelligence.institutional_cross_asset_scores import clamp_score, risk_tier, to_float


RISK_CATEGORIES = (
    "market_risk",
    "liquidity_risk",
    "model_risk",
    "operational_risk",
    "settlement_risk",
    "execution_risk",
    "compliance_policy_risk",
)

SUPPORTED_PROVIDERS = {
    "kalshi_prediction_market",
    "sharp_sportsbook",
    "sportsbook",
    "stock_sidecar",
    "bond_sidecar",
    "major_asset_sidecar",
}

SUPPORTED_ASSET_CLASSES = {"prediction_market", "stock", "bond", "major_asset", "sportsbook"}


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def assess_institutional_risk(
    record: dict[str, Any],
    *,
    calibration_report: dict[str, Any] | None = None,
    limits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blocks: list[str] = []
    warnings: list[str] = []
    categories = {category: [] for category in RISK_CATEGORIES}
    asset_class = str(record.get("asset_class") or "unknown")
    provider = str(record.get("provider") or "unknown")

    if asset_class not in SUPPORTED_ASSET_CLASSES:
        _append_unique(blocks, "unsupported_asset_class")
        categories["compliance_policy_risk"].append("unsupported_asset_class")
    if provider not in SUPPORTED_PROVIDERS and provider not in {"stock_sidecar", "bond_sidecar", "major_asset_sidecar"}:
        _append_unique(blocks, "unsupported_provider")
        categories["compliance_policy_risk"].append("unsupported_provider")

    liquidity = to_float(record.get("liquidity_score"))
    pricing = to_float(record.get("pricing_quality_score"))
    structure = to_float(record.get("market_structure_score"))
    confidence = to_float(record.get("confidence_score"))
    settlement = to_float(record.get("settlement_quality_score"))
    risk = to_float(record.get("risk_score"))

    if liquidity is None:
        _append_unique(blocks, "missing_liquidity")
        categories["liquidity_risk"].append("missing_liquidity")
    elif liquidity < float((limits or {}).get("min_liquidity_score", 45.0)):
        _append_unique(blocks, "low_liquidity")
        categories["liquidity_risk"].append("low_liquidity")

    if pricing is None:
        _append_unique(blocks, "missing_quote")
        categories["execution_risk"].append("missing_quote")
    elif pricing < float((limits or {}).get("min_pricing_quality_score", 45.0)):
        _append_unique(blocks, "low_pricing_quality")
        categories["execution_risk"].append("low_pricing_quality")

    if structure is None or structure < float((limits or {}).get("min_market_structure_score", 45.0)):
        _append_unique(blocks, "weak_market_structure")
        categories["market_risk"].append("weak_market_structure")

    if confidence is None:
        _append_unique(blocks, "missing_confidence")
        categories["model_risk"].append("missing_confidence")
    elif confidence < float((limits or {}).get("min_confidence_score", 45.0)):
        _append_unique(blocks, "low_confidence")
        categories["model_risk"].append("low_confidence")

    if settlement is None or settlement < 50.0:
        _append_unique(blocks, "missing_outcome_path")
        categories["settlement_risk"].append("missing_outcome_path")

    if risk is not None and risk_tier(risk) == "high_fragility":
        _append_unique(blocks, "high_risk_tier")
        categories["market_risk"].append("high_fragility")

    for reason in record.get("reason_codes") or []:
        text = str(reason)
        if text in {"stale_price", "stale_line", "missing_timestamp"}:
            _append_unique(blocks, "stale_price")
            categories["operational_risk"].append(text)
        elif text in {"settlement_unknown", "ambiguous_contract"}:
            _append_unique(blocks, "settlement_ambiguity")
            categories["settlement_risk"].append(text)
        elif text in {"wide_spread", "extreme_spread", "inverted_quote"}:
            categories["execution_risk"].append(text)
            warnings.append(text)
        elif text in {"insufficient_calibration_sample", "missing_edge"}:
            categories["model_risk"].append(text)
            warnings.append(text)

    asset_calibration = None
    if calibration_report and isinstance(calibration_report.get("asset_classes"), dict):
        asset_calibration = calibration_report["asset_classes"].get(asset_class)
    elif calibration_report and calibration_report.get("asset_class") == asset_class:
        asset_calibration = calibration_report
    matched = int((asset_calibration or {}).get("matched_outcomes_count", 0) or 0)
    if matched < int((limits or {}).get("min_calibration_sample", 30)):
        _append_unique(blocks, "insufficient_calibration_sample")
        categories["model_risk"].append("insufficient_calibration_sample")

    score_components = [
        100.0 - (liquidity if liquidity is not None else 20.0),
        100.0 - (pricing if pricing is not None else 20.0),
        100.0 - (structure if structure is not None else 45.0),
        100.0 - (confidence if confidence is not None else 30.0),
        risk if risk is not None else 70.0,
    ]
    risk_score = clamp_score(sum(score_components) / len(score_components) + min(25.0, len(blocks) * 4.0))
    tier = risk_tier(risk_score)
    return {
        "risk_score": risk_score,
        "risk_tier": tier,
        "risk_blocks": blocks,
        "warnings": sorted(set(warnings)),
        "risk_categories": categories,
        "execution_blocked": True,
        "block_reason": "simulation_only",
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
    }


def sample_risk_output() -> dict[str, Any]:
    return assess_institutional_risk(
        {
            "asset_class": "prediction_market",
            "provider": "kalshi_prediction_market",
            "liquidity_score": 20,
            "pricing_quality_score": 40,
            "market_structure_score": 55,
            "confidence_score": 35,
            "settlement_quality_score": 45,
            "risk_score": 70,
            "reason_codes": ["missing_liquidity", "settlement_unknown"],
        }
    )
