from __future__ import annotations

from typing import Any, Mapping

from src.security.policy import locked_safety_flags


DEFAULT_CONFOUNDERS = {
    "sportsbook": ["injury_status", "lineup_context", "pace", "opponent_strength", "weather"],
    "prediction_market": ["liquidity", "time_to_close", "settlement_uncertainty", "news_catalyst"],
    "stock": ["market_regime", "relative_volume", "spread", "catalyst_type", "balance_sheet_bucket"],
    "crypto": ["funding_rate", "open_interest", "liquidity", "macro_regime"],
    "bond_rate": ["macro_event", "policy_expectations", "liquidity", "auction_schedule"],
}


def run_causal_discovery_research(
    candidate: Mapping[str, Any] | None = None,
    *,
    records: list[Mapping[str, Any]] | None = None,
    minimum_sample_size: int = 200,
) -> dict[str, Any]:
    candidate = candidate or {}
    rows = [row for row in (records or []) if isinstance(row, Mapping)]
    asset = str(candidate.get("asset_type") or candidate.get("market_type") or "unknown").lower()
    confounders = list(candidate.get("expected_confounders") or DEFAULT_CONFOUNDERS.get(asset, ["liquidity", "time", "market_regime"]))
    missing = [field for field in confounders if candidate.get(field) in (None, "", [], {})]
    if len(rows) < int(minimum_sample_size):
        return {
            "ok": True,
            "status": "not_ready",
            "causal_graph_support": "not_ready",
            "causal_discovery_method": "pc_fast_ges_lightweight_scaffold",
            "causal_driver_detected": False,
            "suspected_confounders": missing[:20],
            "spurious_correlation_risk": "high" if missing else "moderate",
            "causal_status": "not_ready",
            "causal_graph_confidence": 0.0,
            "causal_no_bet_reasons": ["causal_sample_insufficient", "missing_confounder_controls"] if missing else ["causal_sample_insufficient"],
            "insufficient_sample": True,
            "blocked_reason": "records_below_causal_discovery_minimum",
            "causal_claim_allowed": False,
            "red_team_only": True,
            **locked_safety_flags(),
        }
    support = "partial" if len(missing) <= max(1, len(confounders) // 3) else "no"
    confidence = 55.0 if support == "partial" else 20.0
    return {
        "ok": True,
        "status": "causal_scaffold_complete",
        "causal_graph_support": support,
        "causal_discovery_method": "pc_fast_ges_lightweight_scaffold",
        "causal_driver_detected": support == "partial",
        "suspected_confounders": missing[:20],
        "spurious_correlation_risk": "moderate" if support == "partial" else "high",
        "causal_status": "causal_hypothesis_support_partial" if support == "partial" else "causal_support_missing",
        "causal_graph_confidence": confidence,
        "causal_no_bet_reasons": ["missing_confounder_controls"] if missing else [],
        "insufficient_sample": False,
        "blocked_reason": None,
        "causal_claim_allowed": False,
        "red_team_only": True,
        **locked_safety_flags(),
    }
