from __future__ import annotations

from typing import Any

from src.security.policy import locked_safety_flags


MINIMUM_CAUSAL_SAMPLE_SIZE = 200

DEFAULT_CAUSAL_HYPOTHESES: tuple[dict[str, Any], ...] = (
    {
        "causal_hypothesis_id": "sports_injury_usage_prop_line_v1",
        "treatment_variable": "injury_confirmed",
        "outcome_variable": "player_usage_or_prop_line_move",
        "confounders": ["baseline_usage", "opponent_defense", "pace", "spread", "lineup_context"],
    },
    {
        "causal_hypothesis_id": "sports_pace_total_points_prop_v1",
        "treatment_variable": "pace_up_environment",
        "outcome_variable": "total_or_points_prop_hit_rate",
        "confounders": ["team_efficiency", "opponent_defense", "injuries", "market_opening_total"],
    },
    {
        "causal_hypothesis_id": "prediction_market_wide_spread_fake_edge_v1",
        "treatment_variable": "wide_bid_ask_spread",
        "outcome_variable": "fake_edge_or_negative_ev_rate",
        "confounders": ["liquidity", "time_to_close", "settlement_uncertainty", "news_catalyst"],
    },
    {
        "causal_hypothesis_id": "stock_low_float_catalyst_follow_through_v1",
        "treatment_variable": "low_float_plus_catalyst",
        "outcome_variable": "momentum_follow_through",
        "confounders": ["relative_volume", "spread", "market_regime", "dilution_risk"],
    },
    {
        "causal_hypothesis_id": "stock_balance_sheet_dilution_trap_v1",
        "treatment_variable": "poor_balance_sheet",
        "outcome_variable": "dilution_trap_or_failed_breakout",
        "confounders": ["cash_runway", "debt_maturity", "filing_status", "volume_spike"],
    },
    {
        "causal_hypothesis_id": "crypto_funding_extreme_reversal_v1",
        "treatment_variable": "funding_extreme",
        "outcome_variable": "crypto_reversal_or_liquidation_event",
        "confounders": ["open_interest", "liquidity", "macro_regime", "exchange_dislocation"],
    },
    {
        "causal_hypothesis_id": "rates_macro_surprise_volatility_v1",
        "treatment_variable": "macro_event_surprise",
        "outcome_variable": "bond_rate_volatility",
        "confounders": ["prior_volatility", "policy_expectations", "liquidity", "auction_schedule"],
    },
)


def _provided_confounder_count(row: dict[str, Any], confounders: list[str]) -> int:
    return sum(1 for field in confounders if row.get(field) not in (None, ""))


def evaluate_causal_hypothesis(
    hypothesis: dict[str, Any] | None,
    *,
    records: list[dict[str, Any]] | None = None,
    minimum_required_sample_size: int = MINIMUM_CAUSAL_SAMPLE_SIZE,
) -> dict[str, Any]:
    spec = dict(hypothesis or {})
    rows = [row for row in (records or []) if isinstance(row, dict)]
    sample_size = len(rows)
    confounders = list(spec.get("confounders") or [])
    treatment = str(spec.get("treatment_variable") or "unknown_treatment")
    outcome = str(spec.get("outcome_variable") or "unknown_outcome")
    missing_confounders = list(confounders)
    if rows and confounders:
        present = {
            field
            for field in confounders
            if any(row.get(field) not in (None, "") for row in rows)
        }
        missing_confounders = [field for field in confounders if field not in present]
    provided_total = sum(_provided_confounder_count(row, confounders) for row in rows)
    possible_total = max(1, len(confounders) * max(1, sample_size))
    confounder_coverage = provided_total / possible_total if confounders else 0.0
    confounding_risk = 1.0 if not confounders else round(max(0.05, min(1.0, 1.0 - (confounder_coverage * 0.75))), 6)
    insufficient = sample_size < int(minimum_required_sample_size or MINIMUM_CAUSAL_SAMPLE_SIZE)
    if insufficient:
        status = "not_ready"
        effect_estimate = None
        interval = None
    else:
        status = "exploratory" if confounding_risk >= 0.35 else "partial_evidence"
        effect_estimate = None
        interval = None
    payload = {
        "causal_hypothesis_id": spec.get("causal_hypothesis_id") or "custom_causal_hypothesis",
        "treatment_variable": treatment,
        "outcome_variable": outcome,
        "confounders": confounders,
        "sample_size": sample_size,
        "minimum_required_sample_size": int(minimum_required_sample_size or MINIMUM_CAUSAL_SAMPLE_SIZE),
        "effect_estimate": effect_estimate,
        "confidence_interval": interval,
        "causal_status": status,
        "insufficient_sample": bool(insufficient),
        "confounding_risk_score": confounding_risk,
        "missing_confounders": missing_confounders[:25],
        "recommendation_impact_allowed": False,
        "causal_claim_allowed": False,
        "correlation_only": True,
        "research_only": False,
        "affects_review_queue": False,
        "affects_execution": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def build_causal_scaffold_report(
    *,
    records: list[dict[str, Any]] | None = None,
    hypotheses: list[dict[str, Any]] | None = None,
    minimum_required_sample_size: int = MINIMUM_CAUSAL_SAMPLE_SIZE,
) -> dict[str, Any]:
    specs = hypotheses if hypotheses is not None else [dict(row) for row in DEFAULT_CAUSAL_HYPOTHESES]
    results = [
        evaluate_causal_hypothesis(
            spec,
            records=records,
            minimum_required_sample_size=minimum_required_sample_size,
        )
        for spec in specs
        if isinstance(spec, dict)
    ]
    payload = {
        "ok": True,
        "status": "causal_scaffold",
        "causal_status": "not_ready" if any(row["insufficient_sample"] for row in results) else "exploratory",
        "total_hypotheses": len(results),
        "not_ready_count": sum(1 for row in results if row["causal_status"] == "not_ready"),
        "high_confounding_risk_count": sum(1 for row in results if float(row["confounding_risk_score"]) >= 0.70),
        "hypotheses": results,
        "recommendation_impact_allowed": False,
        "causal_claim_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
