from __future__ import annotations

from typing import Any, Mapping

from src.security.secret_safety import redact_sensitive
from src.security.policy import locked_safety_flags


CONTEXT_BUCKET_FIELDS = (
    "asset_type",
    "market_type",
    "provider",
    "sport",
    "league",
    "timeframe",
    "session",
    "time_of_day",
    "liquidity_tier",
    "volatility_regime",
    "manifold_cluster",
    "hidden_regime",
    "data_resolution",
    "latency_tier",
    "outcome_window",
    "catalyst_type",
    "balance_sheet_bucket",
    "incentive_bucket",
    "game_script_bucket",
)


def _norm(value: Any, default: str = "unknown") -> str:
    text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    return text or default


def build_context_bucket(candidate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    candidate = redact_sensitive(dict(candidate or {}))
    bucket = {
        "asset_type": _norm(candidate.get("asset_type") or candidate.get("asset_class")),
        "market_type": _norm(candidate.get("market_type") or candidate.get("source_type")),
        "provider": _norm(candidate.get("provider") or candidate.get("provider_id")),
        "sport": _norm(candidate.get("sport")),
        "league": _norm(candidate.get("league")),
        "timeframe": _norm(candidate.get("timeframe")),
        "session": _norm(candidate.get("session") or candidate.get("session_time_bucket")),
        "time_of_day": _norm(candidate.get("time_of_day") or candidate.get("session_time_bucket")),
        "liquidity_tier": _norm(candidate.get("liquidity_tier")),
        "volatility_regime": _norm(candidate.get("volatility_regime")),
        "manifold_cluster": _norm(candidate.get("manifold_cluster_id") or candidate.get("manifold_cluster_name")),
        "hidden_regime": _norm(candidate.get("hidden_regime") or candidate.get("hmm_regime")),
        "data_resolution": _norm(candidate.get("data_resolution")),
        "latency_tier": _norm(candidate.get("latency_tier")),
        "outcome_window": _norm(candidate.get("outcome_window")),
        "catalyst_type": _norm(candidate.get("catalyst_type")),
        "balance_sheet_bucket": _norm(candidate.get("balance_sheet_bucket") or candidate.get("balance_sheet_risk_bucket")),
        "incentive_bucket": _norm(candidate.get("incentive_bucket")),
        "game_script_bucket": _norm(candidate.get("game_script_bucket")),
    }
    bucket["context_key"] = context_key(bucket)
    bucket.update(locked_safety_flags())
    return bucket


def context_key(bucket: Mapping[str, Any]) -> str:
    parts = [f"{field}={_norm(bucket.get(field))}" for field in CONTEXT_BUCKET_FIELDS]
    return "|".join(parts)


def candidate_available_inputs(candidate: Mapping[str, Any] | None = None) -> set[str]:
    candidate = candidate or {}
    available = set()
    for key, value in candidate.items():
        if value not in (None, "", [], {}):
            available.add(str(key))
    explicit = candidate.get("available_inputs")
    if isinstance(explicit, list):
        available.update(str(item) for item in explicit if str(item).strip())
    return available
