from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCORE_FIELDS = (
    "quick_quality_score",
    "broad_quality_score",
    "liquidity_score",
    "pricing_quality_score",
    "market_structure_score",
    "valuation_score",
    "edge_quality_score",
    "financial_quality_score",
    "macro_quality_score",
    "settlement_quality_score",
    "calibration_readiness_score",
    "execution_readiness_score",
    "risk_score",
    "confidence_score",
    "review_priority_score",
)

QUALITY_TIERS = ("unusable", "fragile", "reviewable", "strong", "institutional")
LIQUIDITY_TIERS = (
    "missing",
    "very_low_liquidity",
    "low_liquidity",
    "moderate_liquidity",
    "adequate_liquidity",
    "high_liquidity",
)
RISK_TIERS = ("unknown", "high_fragility", "elevated", "normal", "controlled")
EXECUTION_READINESS_TIERS = (
    "prohibited",
    "incomplete",
    "simulation_only",
    "command_review_required",
    "theoretically_ready_but_disabled",
)

REQUIRED_FIELDS_BY_ASSET_CLASS = {
    "prediction_market": ("provider", "market_type", "observed_at", "contract_id"),
    "stock": ("provider", "symbol_or_ticker", "observed_at", "observed_price"),
    "bond": ("provider", "symbol_or_ticker", "observed_at", "observed_price"),
    "major_asset": ("provider", "symbol_or_ticker", "observed_at", "observed_price"),
    "sportsbook": ("provider", "market_type", "observed_at", "selection"),
}


def to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp_score(value: Any, default: float = 0.0) -> float:
    parsed = to_float(value)
    if parsed is None:
        parsed = default
    return round(max(0.0, min(100.0, parsed)), 4)


def normalize_probability(value: Any) -> float | None:
    parsed = to_float(value)
    if parsed is None:
        return None
    if parsed > 1.0:
        parsed = parsed / 100.0
    if not 0.0 <= parsed <= 1.0:
        return None
    return parsed


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _age_minutes(observed_at: Any) -> float | None:
    parsed = _parse_time(observed_at)
    if parsed is None:
        return None
    return max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 60.0)


def _spread(record: dict[str, Any]) -> float | None:
    spread = to_float(record.get("spread"))
    if spread is not None:
        return spread
    bid = to_float(record.get("bid"))
    ask = to_float(record.get("ask"))
    if bid is None or ask is None:
        return None
    return ask - bid


def _spread_score(record: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    bid = to_float(record.get("bid"))
    ask = to_float(record.get("ask"))
    spread = _spread(record)
    mid = to_float(record.get("mid"))
    observed_price = to_float(record.get("observed_price"))
    price_ref = mid if mid and mid > 0 else observed_price
    if bid is None or ask is None:
        if observed_price is None:
            return 35.0, ["missing_quote"]
        return 62.0, ["missing_bid_ask"]
    if spread is None:
        return 45.0, ["missing_spread"]
    if spread < 0:
        return 10.0, ["inverted_quote"]
    if price_ref and price_ref > 1.0:
        pct = spread / price_ref
    else:
        pct = spread
    if pct <= 0.005:
        score = 98.0
    elif pct <= 0.02:
        score = 90.0
    elif pct <= 0.05:
        score = 78.0
    elif pct <= 0.10:
        score = 58.0
        reasons.append("wide_spread")
    elif pct <= 0.20:
        score = 38.0
        reasons.append("wide_spread")
    else:
        score = 18.0
        reasons.append("extreme_spread")
    return score, reasons


def _volume_score(record: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    volume = to_float(record.get("volume"))
    open_interest = to_float(record.get("open_interest"))
    dollar_volume = to_float(record.get("dollar_volume") or record.get("average_dollar_volume"))
    book_count = to_float(record.get("book_count") or record.get("books_compared"))
    liquidity_inputs = [x for x in (volume, open_interest, dollar_volume, book_count) if x is not None]
    if not liquidity_inputs:
        return 20.0, ["missing_liquidity"]

    score = 0.0
    if dollar_volume is not None:
        if dollar_volume >= 250_000_000:
            score = max(score, 96.0)
        elif dollar_volume >= 50_000_000:
            score = max(score, 86.0)
        elif dollar_volume >= 5_000_000:
            score = max(score, 70.0)
        elif dollar_volume >= 500_000:
            score = max(score, 50.0)
        else:
            score = max(score, 30.0)
            reasons.append("low_dollar_volume")
    if volume is not None:
        if volume >= 50_000:
            score = max(score, 92.0)
        elif volume >= 10_000:
            score = max(score, 82.0)
        elif volume >= 1_000:
            score = max(score, 68.0)
        elif volume >= 100:
            score = max(score, 48.0)
        elif volume > 0:
            score = max(score, 30.0)
            reasons.append("low_volume")
        else:
            score = max(score, 15.0)
            reasons.append("zero_volume")
    if open_interest is not None:
        if open_interest >= 50_000:
            score = max(score, 94.0)
        elif open_interest >= 10_000:
            score = max(score, 86.0)
        elif open_interest >= 1_000:
            score = max(score, 70.0)
        elif open_interest >= 100:
            score = max(score, 50.0)
        elif open_interest > 0:
            score = max(score, 30.0)
            reasons.append("low_open_interest")
        else:
            reasons.append("zero_open_interest")
    if book_count is not None:
        if book_count >= 8:
            score = max(score, 88.0)
        elif book_count >= 4:
            score = max(score, 74.0)
        elif book_count >= 2:
            score = max(score, 55.0)
        elif book_count >= 1:
            score = max(score, 35.0)
            reasons.append("low_book_count")
    return score or 20.0, reasons


def _freshness_score(record: dict[str, Any]) -> tuple[float, list[str]]:
    age = _age_minutes(record.get("observed_at"))
    if age is None:
        return 50.0, ["missing_timestamp"]
    asset_class = str(record.get("asset_class") or "")
    if asset_class in {"stock", "bond", "major_asset"}:
        limits = (5, 30, 240)
    elif asset_class == "sportsbook":
        limits = (15, 120, 720)
    else:
        limits = (30, 240, 1440)
    if age <= limits[0]:
        return 96.0, []
    if age <= limits[1]:
        return 82.0, []
    if age <= limits[2]:
        return 58.0, ["stale_price"]
    return 25.0, ["stale_price"]


def missing_fields(record: dict[str, Any]) -> list[str]:
    required = REQUIRED_FIELDS_BY_ASSET_CLASS.get(str(record.get("asset_class") or ""), ())
    missing = [field for field in required if record.get(field) in (None, "")]
    asset_class = str(record.get("asset_class") or "")
    if asset_class == "prediction_market":
        if record.get("bid") is None or record.get("ask") is None:
            missing.append("bid_ask")
    elif asset_class == "sportsbook":
        if record.get("observed_price") is None and record.get("implied_probability") is None:
            missing.append("odds_or_probability")
    return sorted(set(missing))


def quality_tier(score: Any) -> str:
    parsed = to_float(score)
    if parsed is None:
        return "unusable"
    if parsed < 35:
        return "unusable"
    if parsed < 55:
        return "fragile"
    if parsed < 75:
        return "reviewable"
    if parsed < 90:
        return "strong"
    return "institutional"


def liquidity_tier(score: Any) -> str:
    parsed = to_float(score)
    if parsed is None:
        return "missing"
    if parsed < 25:
        return "very_low_liquidity"
    if parsed < 45:
        return "low_liquidity"
    if parsed < 65:
        return "moderate_liquidity"
    if parsed < 85:
        return "adequate_liquidity"
    return "high_liquidity"


def risk_tier(score: Any) -> str:
    parsed = to_float(score)
    if parsed is None:
        return "unknown"
    if parsed <= 20:
        return "controlled"
    if parsed <= 40:
        return "normal"
    if parsed <= 65:
        return "elevated"
    return "high_fragility"


def execution_readiness_tier(score: Any) -> str:
    parsed = to_float(score)
    if parsed is None or parsed <= 0:
        return "prohibited"
    if parsed < 45:
        return "incomplete"
    if parsed < 70:
        return "simulation_only"
    if parsed < 90:
        return "command_review_required"
    return "theoretically_ready_but_disabled"


def _existing_score(record: dict[str, Any], field: str) -> float | None:
    parsed = to_float(record.get(field))
    if parsed is None:
        return None
    return clamp_score(parsed)


def _valuation_score(record: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    edge = to_float(record.get("edge"))
    model_probability = normalize_probability(record.get("model_probability"))
    implied_probability = normalize_probability(record.get("implied_probability") or record.get("no_vig_probability"))
    if edge is None and model_probability is not None and implied_probability is not None:
        edge = model_probability - implied_probability
    if edge is None:
        return 50.0, ["missing_edge"]
    if abs(edge) < 0.005:
        return 52.0, []
    if edge > 0:
        score = 55.0 + min(35.0, edge * 250.0)
    else:
        score = 45.0 + max(-35.0, edge * 250.0)
        reasons.append("negative_edge")
    return clamp_score(score), reasons


def complete_institutional_scores(record: dict[str, Any]) -> dict[str, Any]:
    """Fill missing institutional fields without overwriting upstream scores."""
    row = dict(record)
    reasons = list(row.get("reason_codes") or [])

    missing = missing_fields(row)
    row["missing_fields"] = sorted(set(list(row.get("missing_fields") or []) + missing))

    spread_score, spread_reasons = _spread_score(row)
    freshness_score, freshness_reasons = _freshness_score(row)
    liquidity_score_value, liquidity_reasons = _volume_score(row)
    valuation_score_value, valuation_reasons = _valuation_score(row)
    reasons.extend(spread_reasons + freshness_reasons + liquidity_reasons + valuation_reasons)
    if missing:
        reasons.extend(f"missing_{field}" for field in missing)

    pricing_quality = _existing_score(row, "pricing_quality_score")
    if pricing_quality is None:
        pricing_quality = clamp_score((spread_score * 0.75) + (freshness_score * 0.25))
        row["pricing_quality_score"] = pricing_quality

    liquidity = _existing_score(row, "liquidity_score")
    if liquidity is None:
        liquidity = clamp_score(liquidity_score_value)
        row["liquidity_score"] = liquidity

    quick = _existing_score(row, "quick_quality_score")
    if quick is None:
        completeness_penalty = min(35.0, len(missing) * 8.0)
        quick = clamp_score((pricing_quality * 0.55) + (freshness_score * 0.25) + (liquidity * 0.20) - completeness_penalty)
        row["quick_quality_score"] = quick

    market_structure = _existing_score(row, "market_structure_score")
    if market_structure is None:
        provider = str(row.get("provider") or "")
        base = 78.0
        if provider in {"kalshi_prediction_market", "sharp_sportsbook"}:
            base = 82.0
        if row.get("settlement_rule_status") in {"missing", "unknown"}:
            base -= 18.0
            reasons.append("settlement_unknown")
        if row.get("asset_class") == "sportsbook" and not row.get("book_count"):
            base -= 12.0
        market_structure = clamp_score(base)
        row["market_structure_score"] = market_structure

    broad = _existing_score(row, "broad_quality_score")
    if broad is None:
        broad = clamp_score((quick * 0.35) + (liquidity * 0.35) + (market_structure * 0.30))
        row["broad_quality_score"] = broad

    if _existing_score(row, "valuation_score") is None:
        row["valuation_score"] = valuation_score_value
    if _existing_score(row, "edge_quality_score") is None:
        cost_penalty = max(0.0, 70.0 - pricing_quality) * 0.35 + max(0.0, 60.0 - liquidity) * 0.25
        row["edge_quality_score"] = clamp_score(row["valuation_score"] - cost_penalty)

    if _existing_score(row, "financial_quality_score") is None:
        row["financial_quality_score"] = _financial_quality(row)
    if _existing_score(row, "macro_quality_score") is None:
        row["macro_quality_score"] = _macro_quality(row)
    if _existing_score(row, "settlement_quality_score") is None:
        row["settlement_quality_score"] = _settlement_quality(row)
    if _existing_score(row, "calibration_readiness_score") is None:
        row["calibration_readiness_score"] = _calibration_readiness(row)

    risk = _existing_score(row, "risk_score")
    if risk is None:
        risk = _risk_from_quality(row, reasons)
        row["risk_score"] = risk
    confidence = _existing_score(row, "confidence_score")
    if confidence is None:
        confidence = clamp_score((quick * 0.25) + (broad * 0.25) + (row["calibration_readiness_score"] * 0.25) + ((100.0 - risk) * 0.25))
        row["confidence_score"] = confidence
    if _existing_score(row, "review_priority_score") is None:
        row["review_priority_score"] = clamp_score((row["edge_quality_score"] * 0.30) + (confidence * 0.35) + (liquidity * 0.20) + ((100.0 - risk) * 0.15))

    if _existing_score(row, "execution_readiness_score") is None:
        row["execution_readiness_score"] = _execution_readiness(row)

    row["quality_tier"] = row.get("quality_tier") or quality_tier(row.get("broad_quality_score"))
    row["liquidity_tier"] = row.get("liquidity_tier") or liquidity_tier(row.get("liquidity_score"))
    row["risk_tier"] = row.get("risk_tier") or risk_tier(row.get("risk_score"))
    row["execution_readiness_tier"] = row.get("execution_readiness_tier") or execution_readiness_tier(row.get("execution_readiness_score"))
    row["reason_codes"] = sorted({str(reason) for reason in reasons if reason})
    row["execution_allowed"] = False
    row["paper_only"] = True
    row["review_only"] = True
    row["simulation_only"] = True
    return row


def _financial_quality(record: dict[str, Any]) -> float | None:
    if record.get("asset_class") != "stock":
        return None
    quick_ratio = to_float(record.get("quick_ratio"))
    current_ratio = to_float(record.get("current_ratio"))
    debt_to_cash = to_float(record.get("debt_to_cash"))
    score = 55.0
    if quick_ratio is not None:
        score += min(20.0, max(-20.0, (quick_ratio - 1.0) * 20.0))
    if current_ratio is not None:
        score += min(15.0, max(-15.0, (current_ratio - 1.2) * 12.0))
    if debt_to_cash is not None:
        score -= min(25.0, max(0.0, (debt_to_cash - 1.0) * 10.0))
    return clamp_score(score)


def _macro_quality(record: dict[str, Any]) -> float | None:
    if record.get("asset_class") not in {"bond", "major_asset", "stock"}:
        return None
    risk_flags = {str(flag) for flag in record.get("risk_flags") or []}
    score = 70.0
    for flag in (
        "duration_risk",
        "curve_risk",
        "credit_spread_risk",
        "inflation_risk",
        "central_bank_event_risk",
        "liquidity_stress",
        "volatility_spike_risk",
        "geopolitical_risk",
    ):
        if flag in risk_flags:
            score -= 7.0
    return clamp_score(score)


def _settlement_quality(record: dict[str, Any]) -> float:
    status = str(record.get("settlement_rule_status") or record.get("outcome_status") or "unknown").lower()
    if status in {"settled", "completed"}:
        return 90.0
    if status in {"pending", "active", "known", "clear"}:
        return 75.0
    if status in {"void", "cancelled"}:
        return 40.0
    return 45.0


def _calibration_readiness(record: dict[str, Any]) -> float:
    has_prediction = normalize_probability(record.get("model_probability") or record.get("implied_probability")) is not None
    has_outcome = str(record.get("outcome_status") or "").lower() in {"settled", "completed"} and record.get("final_outcome") is not None
    has_horizon_price = record.get("final_price") is not None and record.get("observed_price") is not None
    if record.get("asset_class") in {"stock", "bond", "major_asset"}:
        return 88.0 if has_horizon_price else 48.0
    if has_prediction and has_outcome:
        return 90.0
    if has_prediction:
        return 58.0
    return 35.0


def _risk_from_quality(record: dict[str, Any], reasons: list[str]) -> float:
    risk = 100.0 - clamp_score(record.get("broad_quality_score"), 50.0)
    if record.get("pricing_quality_score") is not None:
        risk += max(0.0, 55.0 - clamp_score(record.get("pricing_quality_score"))) * 0.25
    if record.get("liquidity_score") is not None:
        risk += max(0.0, 55.0 - clamp_score(record.get("liquidity_score"))) * 0.35
    for reason in reasons:
        if reason in {"stale_price", "settlement_unknown", "missing_quote", "missing_liquidity"}:
            risk += 8.0
        if reason in {"extreme_spread", "inverted_quote"}:
            risk += 15.0
    return clamp_score(risk)


def _execution_readiness(record: dict[str, Any]) -> float:
    components = [
        to_float(record.get("liquidity_score")),
        to_float(record.get("pricing_quality_score")),
        to_float(record.get("market_structure_score")),
        to_float(record.get("confidence_score")),
        to_float(record.get("settlement_quality_score")),
    ]
    available = [value for value in components if value is not None]
    if len(available) < 3:
        return 0.0
    readiness = sum(available) / len(available)
    if record.get("missing_fields"):
        readiness -= min(30.0, len(record["missing_fields"]) * 6.0)
    if risk_tier(record.get("risk_score")) == "high_fragility":
        readiness -= 25.0
    return clamp_score(readiness)
