from __future__ import annotations

import math
from typing import Any

from .scheduler_config import utc_now_iso


FEATURE_VECTOR_VERSION = "cross_asset_manifold_features_v1"

RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
    "raw_broker_payload",
    "full_provider_response",
}
SENSITIVE_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")

ASSET_TYPES = (
    "prediction_market",
    "sportsbook",
    "stock",
    "crypto",
    "etf",
    "bond_rate",
    "major_asset",
)

MARKET_GROUPS = (
    "prediction_market",
    "sports",
    "equity",
    "spot",
    "derivative",
    "rates",
    "macro",
    "unknown",
)

COMMON_NUMERIC_FEATURES = (
    "liquidity_score",
    "spread_score",
    "volume_score",
    "volatility_score",
    "price_momentum_score",
    "trend_score",
    "catalyst_score",
    "time_context_score",
    "risk_score",
    "model_probability",
    "market_implied_probability",
    "estimated_edge",
    "confidence_score",
    "calibration_score",
    "outcome_coverage_score",
    "stale_data_risk",
    "outlier_score",
)

ASSET_NUMERIC_FEATURES = (
    "contract_price",
    "bid_ask_spread",
    "open_interest_score",
    "time_to_close_score",
    "settlement_uncertainty_score",
    "stale_market_score",
    "close_time_pressure_score",
    "pricing_quality_score",
    "line_movement_score",
    "steam_score",
    "reverse_line_movement_score",
    "injury_news_score",
    "lineup_confirmation_score",
    "weather_score",
    "game_script_score",
    "public_sharp_split_score",
    "prop_context_score",
    "live_latency_score",
    "correlation_score",
    "price_band_score",
    "float_rotation_score",
    "relative_volume_score",
    "dollar_volume_score",
    "bid_ask_depth_score",
    "pattern_quality_score",
    "vwap_context_score",
    "opening_range_score",
    "time_of_day_score",
    "balance_sheet_quality_score",
    "dilution_risk_score",
    "halt_risk_score",
    "catalyst_quality_score",
    "market_cap_score",
    "volume_24h_score",
    "orderbook_depth_1pct_score",
    "funding_rate_score",
    "liquidation_cluster_risk",
    "exchange_dislocation_score",
    "volatility_regime_score",
    "breakout_failure_score",
    "yield_change_score",
    "curve_steepening_score",
    "curve_flattening_score",
    "rate_volatility_score",
    "credit_spread_score",
    "macro_event_score",
    "inflation_repricing_score",
    "policy_repricing_score",
    "risk_on_risk_off_score",
    "duration_sensitivity_score",
    "liquidity_stress_score",
)

FEATURE_NAMES = (
    tuple(f"asset_type_{asset_type}" for asset_type in ASSET_TYPES)
    + tuple(f"market_group_{market_group}" for market_group in MARKET_GROUPS)
    + COMMON_NUMERIC_FEATURES
    + ASSET_NUMERIC_FEATURES
)

FEATURE_WEIGHTS = {
    **{f"asset_type_{asset_type}": 2.0 for asset_type in ASSET_TYPES},
    **{f"market_group_{market_group}": 1.2 for market_group in MARKET_GROUPS},
    "liquidity_score": 1.25,
    "spread_score": 1.1,
    "volume_score": 1.0,
    "volatility_score": 0.9,
    "price_momentum_score": 0.95,
    "trend_score": 0.95,
    "catalyst_score": 0.8,
    "time_context_score": 0.9,
    "risk_score": 1.25,
    "model_probability": 1.0,
    "market_implied_probability": 1.0,
    "estimated_edge": 1.25,
    "confidence_score": 1.05,
    "calibration_score": 1.25,
    "outcome_coverage_score": 1.15,
    "stale_data_risk": 1.15,
    "outlier_score": 1.35,
    "settlement_uncertainty_score": 1.2,
    "pricing_quality_score": 1.1,
    "line_movement_score": 0.95,
    "public_sharp_split_score": 0.9,
    "correlation_score": 0.95,
    "pattern_quality_score": 0.9,
    "dilution_risk_score": 1.2,
    "halt_risk_score": 1.1,
    "liquidation_cluster_risk": 1.15,
    "macro_event_score": 1.05,
    "liquidity_stress_score": 1.15,
}


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _score_unit(value: Any, *, missing: float | None = None, invert: bool = False) -> float | None:
    parsed = _num(value)
    if parsed is None:
        return missing
    if 0.0 <= parsed <= 1.0:
        unit = parsed
    else:
        unit = _clamp(parsed / 100.0)
    return round(1.0 - unit if invert else unit, 6)


def _probability_unit(value: Any) -> float | None:
    parsed = _num(value)
    if parsed is None:
        return None
    if parsed > 1.0:
        parsed = parsed / 100.0
    return round(_clamp(parsed), 6)


def _signed_edge_unit(value: Any) -> float | None:
    parsed = _num(value)
    if parsed is None:
        return None
    if abs(parsed) > 1.0:
        parsed = parsed / 100.0
    return round(_clamp((parsed + 0.20) / 0.40), 6)


def _log_unit(value: Any, high: float) -> float | None:
    parsed = _num(value)
    if parsed is None or parsed <= 0:
        return None
    return round(_clamp(math.log10(parsed + 1.0) / math.log10(high + 1.0)), 6)


def _spread_quality_unit(value: Any) -> float | None:
    parsed = _num(value)
    if parsed is None:
        return None
    if parsed < 0:
        return None
    if parsed <= 1.0:
        return round(_clamp(1.0 - parsed), 6)
    percent = parsed
    if percent <= 0.10:
        return 0.96
    if percent <= 0.30:
        return 0.88
    if percent <= 0.75:
        return 0.72
    if percent <= 1.50:
        return 0.52
    if percent <= 3.00:
        return 0.30
    return 0.10


def _risk_unit(value: Any, *, missing: float | None = None) -> float | None:
    return _score_unit(value, missing=missing)


def _inverse_seconds_unit(value: Any, high_seconds: float = 604800.0) -> float | None:
    parsed = _num(value)
    if parsed is None or parsed < 0:
        return None
    return round(_clamp(parsed / high_seconds), 6)


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        lower = key_text.lower()
        if lower in RAW_PAYLOAD_KEYS or any(part in lower for part in SENSITIVE_KEY_PARTS):
            continue
        if isinstance(value, dict):
            out[key_text] = _safe_payload(value)
        elif isinstance(value, list):
            safe_list: list[Any] = []
            for item in value[:25]:
                if isinstance(item, dict):
                    safe_list.append(_safe_payload(item))
                elif isinstance(item, (str, int, float, bool)) or item is None:
                    safe_list.append(item)
            out[key_text] = safe_list
        elif isinstance(value, (str, int, float, bool)) or value is None:
            out[key_text] = value
    return out


def infer_asset_type(row: dict[str, Any]) -> str:
    explicit = str(row.get("asset_type") or row.get("asset_class") or "").strip().lower()
    aliases = {
        "prediction": "prediction_market",
        "prediction_market": "prediction_market",
        "kalshi": "prediction_market",
        "sports": "sportsbook",
        "sportsbook": "sportsbook",
        "sport": "sportsbook",
        "equity": "stock",
        "stock": "stock",
        "crypto": "crypto",
        "cryptocurrency": "crypto",
        "etf": "etf",
        "bond": "bond_rate",
        "bonds": "bond_rate",
        "rate": "bond_rate",
        "rates": "bond_rate",
        "fixed_income": "bond_rate",
        "major_asset": "major_asset",
        "macro": "major_asset",
    }
    if explicit in aliases:
        return aliases[explicit]
    market_type = str(row.get("market_type") or row.get("source_type") or "").lower()
    provider = str(row.get("provider_name") or row.get("provider") or row.get("provider_id") or "").lower()
    if "prediction" in market_type or "kalshi" in provider or "polymarket" in provider:
        return "prediction_market"
    if row.get("sport") or row.get("league") or row.get("odds") is not None or "sportsbook" in provider:
        return "sportsbook"
    if row.get("funding_rate") is not None or row.get("volume_24h") is not None or row.get("orderbook_depth_1pct") is not None:
        return "crypto"
    if row.get("yield_change") is not None or row.get("rate_volatility_score") is not None or row.get("curve_steepening_score") is not None:
        return "bond_rate"
    if "etf" in market_type:
        return "etf"
    return "stock"


def infer_market_group(row: dict[str, Any], asset_type: str) -> str:
    market_type = str(row.get("market_type") or "").lower()
    if asset_type == "prediction_market":
        return "prediction_market"
    if asset_type == "sportsbook":
        return "sports"
    if asset_type in {"stock", "etf"}:
        return "equity" if market_type not in {"option", "future", "swap"} else "derivative"
    if asset_type == "crypto":
        return "derivative" if market_type in {"perp", "futures", "option"} else "spot"
    if asset_type == "bond_rate":
        return "rates"
    if asset_type == "major_asset":
        return "macro"
    return "unknown"


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if row.get(key) is not None:
            return row.get(key)
    return None


def _common_features(row: dict[str, Any], asset_type: str) -> tuple[dict[str, float], list[str]]:
    missing: list[str] = []
    implied = _first(row, "market_implied_probability", "implied_probability", "no_vig_probability")
    model_probability = _first(row, "model_probability", "estimated_fair_probability", "fair_probability")
    edge = _first(row, "estimated_edge", "edge", "probability_edge", "ev_percent", "estimated_roi_percent")
    bid_ask_spread = _first(row, "bid_ask_spread", "spread", "spread_percent")
    volume = _first(row, "volume", "daily_volume", "volume_24h")
    liquidity = _first(row, "liquidity_score", "liquidity")
    if liquidity is None:
        liquidity = _log_unit(_first(row, "dollar_volume", "volume_24h", "volume"), 100_000_000)
        if liquidity is not None:
            liquidity = liquidity * 100.0

    values = {
        "liquidity_score": _score_unit(liquidity),
        "spread_score": _score_unit(row.get("spread_score")) or _spread_quality_unit(bid_ask_spread),
        "volume_score": _score_unit(row.get("volume_score")) or _log_unit(volume, 1_000_000),
        "volatility_score": _score_unit(_first(row, "volatility_score", "rate_volatility_score", "volatility_regime_score"), missing=0.50),
        "price_momentum_score": _score_unit(_first(row, "price_momentum_score", "momentum_score", "line_movement_score"), missing=0.50),
        "trend_score": _score_unit(_first(row, "trend_score", "macro_regime_score"), missing=0.50),
        "catalyst_score": _score_unit(_first(row, "catalyst_score", "catalyst_quality_score", "macro_event_score"), missing=0.50),
        "time_context_score": _score_unit(_first(row, "time_context_score", "close_time_score", "time_of_day_score"), missing=0.50),
        "risk_score": _risk_unit(_first(row, "risk_score", "settlement_rule_risk"), missing=0.50),
        "model_probability": _probability_unit(model_probability),
        "market_implied_probability": _probability_unit(implied),
        "estimated_edge": _signed_edge_unit(edge),
        "confidence_score": _score_unit(_first(row, "confidence_score", "confidence"), missing=0.50),
        "calibration_score": _score_unit(_first(row, "calibration_score", "calibration_readiness_score"), missing=0.0),
        "outcome_coverage_score": _score_unit(_first(row, "outcome_coverage_score", "coverage_rate"), missing=0.0),
        "stale_data_risk": _risk_unit(_first(row, "stale_data_risk", "stale_market_score", "stale_market"), missing=0.0),
        "outlier_score": _risk_unit(_first(row, "outlier_score"), missing=0.0),
    }
    for key, value in values.items():
        if value is None:
            values[key] = 0.0
            missing.append(key)
    if asset_type == "prediction_market" and values["market_implied_probability"] == 0.0:
        yes_price = _probability_unit(row.get("yes_price") or row.get("contract_price"))
        if yes_price is not None:
            values["market_implied_probability"] = yes_price
    return {key: round(_clamp(float(value)), 6) for key, value in values.items()}, missing


def _asset_features(row: dict[str, Any]) -> tuple[dict[str, float], list[str]]:
    missing: list[str] = []
    values = {
        "contract_price": _probability_unit(_first(row, "contract_price", "yes_price", "price")),
        "bid_ask_spread": _spread_quality_unit(_first(row, "bid_ask_spread", "spread", "spread_percent")),
        "open_interest_score": _score_unit(row.get("open_interest_score")) or _log_unit(row.get("open_interest"), 1_000_000),
        "time_to_close_score": _inverse_seconds_unit(row.get("time_to_close_seconds")),
        "settlement_uncertainty_score": _score_unit(row.get("settlement_uncertainty_score"), missing=0.0),
        "stale_market_score": _score_unit(row.get("stale_market_score"), missing=0.0),
        "close_time_pressure_score": _score_unit(row.get("close_time_pressure_score"), missing=0.0),
        "pricing_quality_score": _score_unit(row.get("pricing_quality_score"), missing=0.50),
        "line_movement_score": _score_unit(row.get("line_movement_score"), missing=0.50),
        "steam_score": _score_unit(row.get("steam_score"), missing=0.0),
        "reverse_line_movement_score": _score_unit(row.get("reverse_line_movement_score"), missing=0.0),
        "injury_news_score": _score_unit(row.get("injury_news_score"), missing=0.0),
        "lineup_confirmation_score": _score_unit(row.get("lineup_confirmation_score"), missing=0.50),
        "weather_score": _score_unit(row.get("weather_score"), missing=0.0),
        "game_script_score": _score_unit(row.get("game_script_score"), missing=0.50),
        "public_sharp_split_score": _score_unit(row.get("public_sharp_split_score"), missing=0.50),
        "prop_context_score": _score_unit(row.get("prop_context_score"), missing=0.50),
        "live_latency_score": _score_unit(row.get("live_latency_score"), missing=0.50),
        "correlation_score": _score_unit(row.get("correlation_score"), missing=0.0),
        "price_band_score": _score_unit(row.get("price_band_score"), missing=0.50),
        "float_rotation_score": _score_unit(row.get("float_rotation_score")) or _clamp((_num(row.get("float_rotation")) or 0.0) / 3.0),
        "relative_volume_score": _score_unit(row.get("relative_volume_score")) or _clamp((_num(row.get("relative_volume")) or 0.0) / 10.0),
        "dollar_volume_score": _score_unit(row.get("dollar_volume_score")) or _log_unit(row.get("dollar_volume"), 100_000_000),
        "bid_ask_depth_score": _score_unit(row.get("bid_ask_depth_score")) or _log_unit(row.get("bid_ask_depth"), 1_000_000),
        "pattern_quality_score": _score_unit(row.get("pattern_quality_score"), missing=0.0),
        "vwap_context_score": _score_unit(row.get("vwap_context_score"), missing=0.50),
        "opening_range_score": _score_unit(row.get("opening_range_score"), missing=0.50),
        "time_of_day_score": _score_unit(row.get("time_of_day_score"), missing=0.50),
        "balance_sheet_quality_score": _score_unit(row.get("balance_sheet_quality_score"), missing=0.50),
        "dilution_risk_score": _score_unit(row.get("dilution_risk_score"), missing=0.0),
        "halt_risk_score": _score_unit(row.get("halt_risk_score"), missing=0.0),
        "catalyst_quality_score": _score_unit(row.get("catalyst_quality_score"), missing=0.50),
        "market_cap_score": _log_unit(row.get("market_cap"), 1_000_000_000_000),
        "volume_24h_score": _log_unit(row.get("volume_24h"), 1_000_000_000),
        "orderbook_depth_1pct_score": _log_unit(_first(row, "orderbook_depth_1pct", "order_book_depth_1pct"), 100_000_000),
        "funding_rate_score": _clamp(((_num(row.get("funding_rate")) or 0.0) + 0.05) / 0.10),
        "liquidation_cluster_risk": _score_unit(row.get("liquidation_cluster_risk"), missing=0.0),
        "exchange_dislocation_score": _score_unit(row.get("exchange_dislocation_score"), missing=0.0),
        "volatility_regime_score": _score_unit(row.get("volatility_regime_score"), missing=0.50),
        "breakout_failure_score": _score_unit(row.get("breakout_failure_score"), missing=0.0),
        "yield_change_score": _clamp(abs(_num(row.get("yield_change")) or 0.0) / 2.0),
        "curve_steepening_score": _score_unit(row.get("curve_steepening_score"), missing=0.0),
        "curve_flattening_score": _score_unit(row.get("curve_flattening_score"), missing=0.0),
        "rate_volatility_score": _score_unit(row.get("rate_volatility_score"), missing=0.50),
        "credit_spread_score": _score_unit(row.get("credit_spread_score"), missing=0.0),
        "macro_event_score": _score_unit(row.get("macro_event_score"), missing=0.0),
        "inflation_repricing_score": _score_unit(row.get("inflation_repricing_score"), missing=0.0),
        "policy_repricing_score": _score_unit(row.get("policy_repricing_score"), missing=0.0),
        "risk_on_risk_off_score": _score_unit(row.get("risk_on_risk_off_score"), missing=0.50),
        "duration_sensitivity_score": _score_unit(row.get("duration_sensitivity_score"), missing=0.50),
        "liquidity_stress_score": _score_unit(row.get("liquidity_stress_score"), missing=0.0),
    }
    for key, value in values.items():
        if value is None:
            values[key] = 0.0
            missing.append(key)
    return {key: round(_clamp(float(value)), 6) for key, value in values.items()}, missing


def _provider_name(row: dict[str, Any]) -> str:
    value = row.get("provider_name") or row.get("provider") or row.get("provider_id") or row.get("book") or row.get("bookmaker") or "unknown"
    return str(value)[:80]


def build_manifold_feature_vector(row: dict[str, Any] | None) -> dict[str, Any]:
    source = _safe_payload(row or {})
    asset_type = infer_asset_type(source)
    market_type = str(source.get("market_type") or ("spot" if asset_type == "crypto" else asset_type))
    market_group = infer_market_group(source, asset_type)
    normalized: dict[str, float] = {name: 0.0 for name in FEATURE_NAMES}
    for value in ASSET_TYPES:
        normalized[f"asset_type_{value}"] = 1.0 if value == asset_type else 0.0
    for value in MARKET_GROUPS:
        normalized[f"market_group_{value}"] = 1.0 if value == market_group else 0.0

    common, common_missing = _common_features(source, asset_type)
    asset, asset_missing = _asset_features(source)
    normalized.update(common)
    normalized.update(asset)

    feature_vector = [round(normalized.get(name, 0.0), 6) for name in FEATURE_NAMES]
    weights = [round(float(FEATURE_WEIGHTS.get(name, 0.65)), 6) for name in FEATURE_NAMES]
    weighted_feature_vector = [round(value * weight, 6) for value, weight in zip(feature_vector, weights)]
    missing_features = sorted(set(common_missing + asset_missing))
    return {
        "feature_vector_version": FEATURE_VECTOR_VERSION,
        "asset_type": asset_type,
        "market_type": market_type,
        "market_group": market_group,
        "provider_name": _provider_name(source),
        "timestamp": source.get("timestamp") or source.get("observed_at") or source.get("created_at") or utc_now_iso(),
        "data_resolution": str(source.get("data_resolution") or "unknown"),
        "latency_tier": str(source.get("latency_tier") or "unknown"),
        "feature_names": list(FEATURE_NAMES),
        "feature_vector": feature_vector,
        "feature_weights": weights,
        "weighted_feature_vector": weighted_feature_vector,
        "normalized_features": normalized,
        "missing_features": missing_features,
        "missing_feature_count": len(missing_features),
        "source_summary": {
            "asset_symbol": source.get("asset_symbol") or source.get("symbol") or source.get("ticker") or source.get("contract_id"),
            "sport": source.get("sport"),
            "league": source.get("league"),
            "market_type": market_type,
            "provider_name": _provider_name(source),
        },
        "raw_payload_included": False,
        "secrets_included": False,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
    }
