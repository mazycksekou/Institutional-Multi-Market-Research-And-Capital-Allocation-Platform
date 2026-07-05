from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.data_paths import get_storage_health, resolve_base_data_dir
from .manifold_feature_builder import FEATURE_NAMES, FEATURE_VECTOR_VERSION
from src.services.scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso


MANIFOLD_CLUSTER_SCHEMA_VERSION = f"{SCHEMA_VERSION}.market_state_manifold.cluster_registry.v1"


def _manifold_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "manifold"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _clusters_dir(base_data_dir: str = "data") -> Path:
    path = _manifold_dir(base_data_dir) / "clusters"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _history_dir(base_data_dir: str = "data") -> Path:
    path = _clusters_dir(base_data_dir) / "history"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _clusters_dir(base_data_dir) / "latest.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _base_profile(asset_type: str, market_group: str) -> dict[str, float]:
    values = {name: 0.0 for name in FEATURE_NAMES}
    for name in FEATURE_NAMES:
        if name.startswith("asset_type_"):
            values[name] = 1.0 if name == f"asset_type_{asset_type}" else 0.0
        elif name.startswith("market_group_"):
            values[name] = 1.0 if name == f"market_group_{market_group}" else 0.0
    values.update(
        {
            "liquidity_score": 0.50,
            "spread_score": 0.50,
            "volume_score": 0.50,
            "volatility_score": 0.50,
            "price_momentum_score": 0.50,
            "trend_score": 0.50,
            "catalyst_score": 0.50,
            "time_context_score": 0.50,
            "risk_score": 0.50,
            "model_probability": 0.50,
            "market_implied_probability": 0.50,
            "estimated_edge": 0.50,
            "confidence_score": 0.50,
            "calibration_score": 0.30,
            "outcome_coverage_score": 0.30,
            "stale_data_risk": 0.0,
            "outlier_score": 0.0,
            "pricing_quality_score": 0.50,
        }
    )
    return values


def _cluster(
    cluster_id: str,
    name: str,
    family: str,
    asset_type: str,
    market_group: str,
    profile: dict[str, float],
    *,
    market_types: list[str] | None = None,
) -> dict[str, Any]:
    centroid = _base_profile(asset_type, market_group)
    centroid.update({key: max(0.0, min(1.0, float(value))) for key, value in profile.items() if key in centroid})
    return {
        "manifold_cluster_id": cluster_id,
        "manifold_cluster_name": name,
        "manifold_family": family,
        "asset_type": asset_type,
        "market_group": market_group,
        "market_types": market_types or [],
        "feature_vector_version": FEATURE_VECTOR_VERSION,
        "centroid": centroid,
        "prototype_only": True,
        "historical_stats": {
            "sample_size": 0,
            "outcome_coverage": 0.0,
            "insufficient_sample": True,
        },
    }


def default_cluster_definitions() -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    clusters.extend(
        [
            _cluster(
                "prediction_low_liquidity_stale_pricing_001",
                "low_liquidity_stale_pricing_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "liquidity_score": 0.12,
                    "spread_score": 0.18,
                    "volume_score": 0.12,
                    "stale_data_risk": 0.85,
                    "stale_market_score": 0.85,
                    "pricing_quality_score": 0.25,
                    "estimated_edge": 0.70,
                },
            ),
            _cluster(
                "prediction_adequate_liquidity_review_001",
                "adequate_liquidity_review_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "liquidity_score": 0.78,
                    "spread_score": 0.76,
                    "volume_score": 0.68,
                    "pricing_quality_score": 0.82,
                    "risk_score": 0.35,
                    "calibration_score": 0.55,
                },
            ),
            _cluster(
                "prediction_close_soon_settlement_001",
                "close_soon_settlement_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "time_context_score": 0.18,
                    "time_to_close_score": 0.08,
                    "close_time_pressure_score": 0.88,
                    "settlement_uncertainty_score": 0.45,
                    "risk_score": 0.70,
                },
            ),
            _cluster(
                "prediction_wide_spread_fake_edge_001",
                "wide_spread_fake_edge_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "spread_score": 0.12,
                    "liquidity_score": 0.25,
                    "estimated_edge": 0.88,
                    "pricing_quality_score": 0.30,
                    "risk_score": 0.82,
                },
            ),
            _cluster(
                "prediction_high_confidence_poor_liquidity_001",
                "high_confidence_poor_liquidity_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "confidence_score": 0.86,
                    "liquidity_score": 0.18,
                    "spread_score": 0.28,
                    "risk_score": 0.75,
                },
            ),
            _cluster(
                "prediction_late_information_repricing_001",
                "late_information_repricing_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "price_momentum_score": 0.88,
                    "catalyst_score": 0.88,
                    "line_movement_score": 0.82,
                    "volume_score": 0.72,
                    "risk_score": 0.50,
                },
            ),
            _cluster(
                "prediction_settlement_uncertainty_001",
                "settlement_uncertainty_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "settlement_uncertainty_score": 0.92,
                    "risk_score": 0.86,
                    "confidence_score": 0.30,
                    "pricing_quality_score": 0.35,
                },
            ),
            _cluster(
                "prediction_data_insufficient_001",
                "data_insufficient_zone",
                "prediction_market",
                "prediction_market",
                "prediction_market",
                {
                    "liquidity_score": 0.05,
                    "volume_score": 0.05,
                    "calibration_score": 0.0,
                    "outcome_coverage_score": 0.0,
                    "pricing_quality_score": 0.05,
                },
            ),
        ]
    )
    sportsbook_profiles = {
        "pace_up_offensive_environment": {"game_script_score": 0.88, "trend_score": 0.72, "weather_score": 0.20, "line_movement_score": 0.76},
        "defensive_grind": {"game_script_score": 0.25, "trend_score": 0.30, "weather_score": 0.45, "risk_score": 0.45},
        "blowout_risk": {"risk_score": 0.78, "volatility_score": 0.72, "correlation_score": 0.70},
        "foul_heavy_environment": {"game_script_score": 0.72, "volatility_score": 0.70, "prop_context_score": 0.68},
        "injury_usage_shift": {"injury_news_score": 0.90, "lineup_confirmation_score": 0.35, "prop_context_score": 0.82},
        "weather_suppressed_total": {"weather_score": 0.88, "game_script_score": 0.22, "risk_score": 0.70},
        "sharp_total_upward_repricing": {"steam_score": 0.82, "line_movement_score": 0.86, "public_sharp_split_score": 0.78},
        "stale_prop_line": {"stale_data_risk": 0.80, "prop_context_score": 0.82, "live_latency_score": 0.72},
        "live_momentum_shift": {"live_latency_score": 0.70, "price_momentum_score": 0.88, "volatility_score": 0.74},
        "correlated_sgp_candidate": {"correlation_score": 0.88, "game_script_score": 0.78, "prop_context_score": 0.78},
        "public_trap_zone": {"public_sharp_split_score": 0.90, "reverse_line_movement_score": 0.82, "risk_score": 0.76},
        "no_bet_volatile_script": {"volatility_score": 0.90, "risk_score": 0.90, "live_latency_score": 0.80},
    }
    for idx, (name, profile) in enumerate(sportsbook_profiles.items(), start=1):
        clusters.append(_cluster(f"sportsbook_{name}_{idx:03d}", name, "sportsbook_game_script", "sportsbook", "sports", profile))

    stock_profiles = {
        "liquid_breakout_continuation": {"liquidity_score": 0.84, "spread_score": 0.82, "trend_score": 0.82, "price_momentum_score": 0.78, "relative_volume_score": 0.76},
        "low_float_high_demand_momentum": {"float_rotation_score": 0.86, "relative_volume_score": 0.90, "liquidity_score": 0.58, "volatility_score": 0.76},
        "bull_flag_high_relative_volume": {"pattern_quality_score": 0.82, "relative_volume_score": 0.84, "trend_score": 0.78, "risk_score": 0.42},
        "vwap_reclaim_liquid_trend": {"vwap_context_score": 0.88, "liquidity_score": 0.76, "trend_score": 0.78, "spread_score": 0.76},
        "parabolic_extension_high_reversal_risk": {"price_momentum_score": 0.95, "volatility_score": 0.90, "risk_score": 0.88, "outlier_score": 0.70},
        "liquidity_sweep_recovery": {"price_momentum_score": 0.72, "volume_score": 0.80, "bid_ask_depth_score": 0.70, "risk_score": 0.48},
        "fake_breakout_spread_trap": {"spread_score": 0.14, "price_momentum_score": 0.82, "risk_score": 0.84, "breakout_failure_score": 0.82},
        "low_volume_candle_noise": {"volume_score": 0.10, "relative_volume_score": 0.12, "pattern_quality_score": 0.35, "risk_score": 0.74},
        "dilution_risk_momentum_trap": {"dilution_risk_score": 0.90, "price_momentum_score": 0.82, "risk_score": 0.90, "balance_sheet_quality_score": 0.18},
        "out_of_distribution_setup": {"outlier_score": 0.92, "risk_score": 0.85, "calibration_score": 0.0, "outcome_coverage_score": 0.0},
    }
    for idx, (name, profile) in enumerate(stock_profiles.items(), start=1):
        clusters.append(_cluster(f"stock_{name}_{idx:03d}", name, "stock_crypto_liquidity_pattern", "stock", "equity", profile))

    crypto_profiles = dict(stock_profiles)
    crypto_profiles.update(
        {
            "liquid_breakout_continuation": {"liquidity_score": 0.86, "spread_score": 0.84, "volume_24h_score": 0.82, "orderbook_depth_1pct_score": 0.78, "trend_score": 0.80},
            "fake_breakout_spread_trap": {"spread_score": 0.16, "liquidation_cluster_risk": 0.76, "breakout_failure_score": 0.82, "risk_score": 0.84},
        }
    )
    for idx, (name, profile) in enumerate(crypto_profiles.items(), start=1):
        clusters.append(_cluster(f"crypto_{name}_{idx:03d}", name, "stock_crypto_liquidity_pattern", "crypto", "spot", profile))

    macro_profiles = {
        "macro_event_repricing": {"macro_event_score": 0.90, "volatility_score": 0.74, "risk_score": 0.66},
        "rate_shock_reaction": {"yield_change_score": 0.86, "rate_volatility_score": 0.86, "risk_score": 0.78},
        "risk_on_rotation": {"risk_on_risk_off_score": 0.78, "trend_score": 0.72, "credit_spread_score": 0.28},
        "risk_off_rotation": {"risk_on_risk_off_score": 0.20, "liquidity_stress_score": 0.74, "credit_spread_score": 0.76},
        "duration_squeeze": {"duration_sensitivity_score": 0.90, "yield_change_score": 0.72, "rate_volatility_score": 0.72},
        "liquidity_stress": {"liquidity_stress_score": 0.92, "liquidity_score": 0.18, "spread_score": 0.22, "risk_score": 0.90},
        "credit_spread_widening": {"credit_spread_score": 0.88, "risk_score": 0.82, "risk_on_risk_off_score": 0.18},
        "inflation_repricing": {"inflation_repricing_score": 0.90, "yield_change_score": 0.72, "macro_event_score": 0.70},
        "policy_repricing": {"policy_repricing_score": 0.90, "yield_change_score": 0.74, "macro_event_score": 0.76},
        "event_window_anomaly": {"macro_event_score": 0.86, "outlier_score": 0.82, "risk_score": 0.82},
    }
    for idx, (name, profile) in enumerate(macro_profiles.items(), start=1):
        clusters.append(_cluster(f"bond_rate_{name}_{idx:03d}", name, "bond_rate_macro", "bond_rate", "rates", profile))
        clusters.append(_cluster(f"etf_{name}_{idx:03d}", name, "bond_rate_macro", "etf", "equity", profile))
        clusters.append(_cluster(f"major_asset_{name}_{idx:03d}", name, "bond_rate_macro", "major_asset", "macro", profile))
    return clusters


def default_cluster_registry() -> dict[str, Any]:
    clusters = default_cluster_definitions()
    return {
        "ok": True,
        "schema_version": MANIFOLD_CLUSTER_SCHEMA_VERSION,
        "feature_vector_version": FEATURE_VECTOR_VERSION,
        "created_at": utc_now_iso(),
        "storage_backend": "file",
        "cluster_count": len(clusters),
        "clusters": clusters,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def write_cluster_registry(registry: dict[str, Any] | None = None, *, base_data_dir: str = "data") -> dict[str, Any]:
    payload = dict(registry or default_cluster_registry())
    payload["schema_version"] = payload.get("schema_version") or MANIFOLD_CLUSTER_SCHEMA_VERSION
    payload["feature_vector_version"] = FEATURE_VECTOR_VERSION
    payload["cluster_count"] = len([row for row in payload.get("clusters", []) if isinstance(row, dict)])
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    payload["auto_execution"] = False
    payload["auto_execution_enabled"] = False
    payload["human_approval_required"] = True
    payload["actual_orders_submitted"] = 0
    payload["actual_bets_submitted"] = 0
    payload["actual_trades_submitted"] = 0
    payload["raw_payload_included"] = False
    payload["secrets_included"] = False
    latest = _latest_path(base_data_dir)
    history = _history_dir(base_data_dir) / f"{sanitize_filename(utc_now_iso()[:10])}.json"
    _atomic_write_json(latest, payload)
    _atomic_write_json(history, payload)
    return {
        "storage_backend": "file",
        "cluster_registry_path": _project_relative_path(base_data_dir, latest),
        "cluster_registry_history_path": _project_relative_path(base_data_dir, history),
        "cluster_count": payload["cluster_count"],
    }


def load_cluster_registry(*, base_data_dir: str = "data", create_if_missing: bool = True) -> dict[str, Any]:
    latest = _latest_path(base_data_dir)
    payload = _read_json(latest)
    if isinstance(payload, dict) and isinstance(payload.get("clusters"), list):
        payload["provider_write"] = False
        payload["execution_allowed"] = False
        payload["live_execution_enabled"] = False
        payload["auto_execution"] = False
        payload["auto_execution_enabled"] = False
        payload["human_approval_required"] = True
        payload["actual_orders_submitted"] = 0
        payload["actual_bets_submitted"] = 0
        payload["actual_trades_submitted"] = 0
        payload["raw_payload_included"] = False
        payload["secrets_included"] = False
        payload["storage_health"] = get_storage_health()
        return payload
    payload = default_cluster_registry()
    if create_if_missing:
        payload.update(write_cluster_registry(payload, base_data_dir=base_data_dir))
    payload["storage_health"] = get_storage_health()
    return payload


def find_clusters(
    registry: dict[str, Any],
    *,
    asset_type: str | None = None,
    manifold_family: str | None = None,
) -> list[dict[str, Any]]:
    rows = [row for row in registry.get("clusters", []) if isinstance(row, dict)]
    if asset_type:
        rows = [row for row in rows if str(row.get("asset_type")) == str(asset_type)]
    if manifold_family:
        rows = [row for row in rows if str(row.get("manifold_family")) == str(manifold_family)]
    return rows


def compact_cluster_registry(registry: dict[str, Any], *, limit: int = 25) -> dict[str, Any]:
    cap = max(1, min(int(limit or 25), 100))
    clusters = []
    for row in [item for item in registry.get("clusters", []) if isinstance(item, dict)][:cap]:
        stats = row.get("historical_stats") if isinstance(row.get("historical_stats"), dict) else {}
        clusters.append(
            {
                "manifold_cluster_id": row.get("manifold_cluster_id"),
                "manifold_cluster_name": row.get("manifold_cluster_name"),
                "manifold_family": row.get("manifold_family"),
                "asset_type": row.get("asset_type"),
                "feature_vector_version": row.get("feature_vector_version", FEATURE_VECTOR_VERSION),
                "sample_size": int(stats.get("sample_size", 0) or 0),
                "insufficient_sample": bool(stats.get("insufficient_sample", True)),
                "prototype_only": bool(row.get("prototype_only", True)),
            }
        )
    return {
        "ok": bool(registry.get("ok", True)),
        "status": "ok",
        "schema_version": registry.get("schema_version", MANIFOLD_CLUSTER_SCHEMA_VERSION),
        "feature_vector_version": registry.get("feature_vector_version", FEATURE_VECTOR_VERSION),
        "cluster_count": int(registry.get("cluster_count", len(registry.get("clusters", [])))),
        "clusters": clusters,
        "storage_backend": registry.get("storage_backend", "file"),
        "storage": registry.get("storage_health"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }
