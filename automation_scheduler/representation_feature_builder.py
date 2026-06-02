from __future__ import annotations

from typing import Any

from .manifold_feature_builder import FEATURE_VECTOR_VERSION, build_manifold_feature_vector
from .security_policy import locked_safety_flags


REPRESENTATION_VECTOR_VERSION = "cross_asset_representation_vector_v1"

COMMON_VECTOR_FIELDS = (
    "asset_type",
    "market_type",
    "provider_name",
    "timestamp",
    "data_resolution",
    "latency_tier",
    "liquidity_score",
    "spread_score",
    "volume_score",
    "volatility_score",
    "momentum_score",
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

PREDICTION_MARKET_VECTOR_FIELDS = (
    "contract_price",
    "yes_price",
    "no_price",
    "implied_probability",
    "bid_ask_spread",
    "volume",
    "open_interest",
    "time_to_close_seconds",
    "settlement_uncertainty_score",
    "stale_market_score",
    "close_time_pressure_score",
    "liquidity_tier",
    "pricing_quality_score",
)

SPORTSBOOK_VECTOR_FIELDS = (
    "sport",
    "league",
    "market_type",
    "odds",
    "implied_probability",
    "no_vig_probability",
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
)

STOCK_ETF_VECTOR_FIELDS = (
    "price",
    "price_band_score",
    "float_shares",
    "float_rotation",
    "relative_volume",
    "dollar_volume",
    "spread_percent",
    "bid_ask_depth",
    "candlestick_pattern_id",
    "pattern_quality_score",
    "vwap_context_score",
    "opening_range_score",
    "time_of_day_score",
    "balance_sheet_quality_score",
    "dilution_risk_score",
    "halt_risk_score",
    "catalyst_quality_score",
)

CRYPTO_VECTOR_FIELDS = (
    "market_cap",
    "volume_24h",
    "relative_volume",
    "spread_percent",
    "orderbook_depth_1pct",
    "funding_rate",
    "open_interest",
    "liquidation_cluster_risk",
    "exchange_dislocation_score",
    "volatility_regime_score",
    "trend_score",
    "breakout_failure_score",
)

BOND_RATE_VECTOR_FIELDS = (
    "yield_change",
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

ASSET_FIELD_MAP = {
    "prediction_market": PREDICTION_MARKET_VECTOR_FIELDS,
    "sportsbook": SPORTSBOOK_VECTOR_FIELDS,
    "stock": STOCK_ETF_VECTOR_FIELDS,
    "etf": STOCK_ETF_VECTOR_FIELDS + BOND_RATE_VECTOR_FIELDS,
    "crypto": CRYPTO_VECTOR_FIELDS,
    "bond_rate": BOND_RATE_VECTOR_FIELDS,
    "major_asset": BOND_RATE_VECTOR_FIELDS,
}

_SENSITIVE_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")
_RAW_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
    "order_payload",
    "execution_payload",
}


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _safe_field(row: dict[str, Any], key: str) -> Any:
    lower = str(key).lower()
    if lower in _RAW_KEYS or any(part in lower for part in _SENSITIVE_KEY_PARTS):
        return None
    return _safe_scalar(row.get(key))


def _feature(row: dict[str, Any], normalized: dict[str, float], key: str) -> Any:
    if key == "momentum_score":
        return normalized.get("price_momentum_score")
    if key in normalized:
        return normalized.get(key)
    aliases = {
        "implied_probability": ("implied_probability", "market_implied_probability"),
        "contract_price": ("contract_price", "yes_price", "price"),
        "bid_ask_spread": ("bid_ask_spread", "spread", "spread_percent"),
        "market_type": ("market_type",),
    }
    for alias in aliases.get(key, (key,)):
        value = _safe_field(row, alias)
        if value is not None:
            return value
    return None


def build_representation_vector(row: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(row or {})
    manifold = build_manifold_feature_vector(source)
    asset_type = str(manifold.get("asset_type") or "unknown")
    normalized = dict(manifold.get("normalized_features") or {})
    fields = list(COMMON_VECTOR_FIELDS)
    fields.extend(name for name in ASSET_FIELD_MAP.get(asset_type, ()) if name not in fields)
    values = {
        "asset_type": asset_type,
        "market_type": manifold.get("market_type"),
        "provider_name": manifold.get("provider_name"),
        "timestamp": manifold.get("timestamp"),
        "data_resolution": manifold.get("data_resolution"),
        "latency_tier": manifold.get("latency_tier"),
    }
    for field in fields:
        if field in values:
            continue
        values[field] = _feature(source, normalized, field)

    embedding = list(manifold.get("weighted_feature_vector") or [])
    payload = {
        "representation_version": REPRESENTATION_VECTOR_VERSION,
        "feature_vector_version": FEATURE_VECTOR_VERSION,
        "asset_type": asset_type,
        "market_type": manifold.get("market_type"),
        "provider_name": manifold.get("provider_name"),
        "timestamp": manifold.get("timestamp"),
        "data_resolution": manifold.get("data_resolution"),
        "latency_tier": manifold.get("latency_tier"),
        "feature_fields": fields,
        "feature_values": values,
        "normalized_scores": {
            "liquidity_score": normalized.get("liquidity_score"),
            "spread_score": normalized.get("spread_score"),
            "volume_score": normalized.get("volume_score"),
            "volatility_score": normalized.get("volatility_score"),
            "momentum_score": normalized.get("price_momentum_score"),
            "trend_score": normalized.get("trend_score"),
            "risk_score": normalized.get("risk_score"),
            "estimated_edge": normalized.get("estimated_edge"),
            "confidence_score": normalized.get("confidence_score"),
            "stale_data_risk": normalized.get("stale_data_risk"),
            "outlier_score": normalized.get("outlier_score"),
        },
        "embedding_dimension": len(embedding),
        "embedding_vector": embedding,
        "embedding_kind": "deterministic_weighted_feature_vector",
        "missing_features": list(manifold.get("missing_features") or [])[:50],
        "missing_feature_count": int(manifold.get("missing_feature_count", 0) or 0),
        "source_summary": manifold.get("source_summary", {}),
        "deterministic": True,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def build_representation_batch(rows: list[dict[str, Any]] | None, *, limit: int = 250) -> dict[str, Any]:
    cap = max(1, min(int(limit or 250), 1000))
    vectors = [build_representation_vector(row) for row in (rows or [])[:cap] if isinstance(row, dict)]
    payload = {
        "ok": True,
        "status": "representation_vectors_built",
        "representation_version": REPRESENTATION_VECTOR_VERSION,
        "items_received": len(rows or []),
        "items_vectorized": len(vectors),
        "vectors": vectors,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
