from __future__ import annotations

from typing import Any, Mapping

from src.security.secret_safety import redact_sensitive
from src.security.policy import locked_safety_flags
from .strategy_context_buckets import build_context_bucket
from .strategy_maturity import evaluate_strategy_maturity
from .strategy_registry import get_strategy_registry, normalize_strategy_record


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _asset_matches(strategy: Mapping[str, Any], asset_type: str) -> bool:
    supported = {_norm(item) for item in list(strategy.get("asset_types_supported") or [])}
    return "*" in supported or asset_type in supported


def _market_matches(strategy: Mapping[str, Any], market_type: str) -> bool:
    supported = {_norm(item) for item in list(strategy.get("market_types_supported") or [])}
    return "*" in supported or market_type in supported


def _context_match_value(expr: str, context: Mapping[str, Any]) -> bool:
    if ":" not in expr:
        return False
    key, expected = expr.split(":", 1)
    actual = _norm(context.get(key))
    expected = _norm(expected)
    if expected in {"minute_or_better"}:
        return actual in {"tick", "quote", "sub_minute", "1m", "1m_candles", "minute", "5m"}
    if key == "sport" and expected == "basketball":
        return actual in {"basketball", "nba", "wnba", "ncaab", "basketball_nba", "basketball_wnba"}
    return actual == expected


def _context_allowed(strategy: Mapping[str, Any], context: Mapping[str, Any]) -> tuple[bool, str | None]:
    for forbidden in list(strategy.get("forbidden_contexts") or []):
        if _context_match_value(str(forbidden), context):
            return False, f"forbidden_context:{forbidden}"
    allowed_contexts = list(strategy.get("allowed_contexts") or [])
    if not allowed_contexts:
        return True, None
    # Allowed contexts are hints unless they target the current core dimensions.
    strict_contexts = [ctx for ctx in allowed_contexts if str(ctx).split(":", 1)[0] in {"asset_type", "market_type", "sport", "league"}]
    if strict_contexts and not any(_context_match_value(str(ctx), context) for ctx in strict_contexts):
        return False, f"allowed_context_not_matched:{','.join(strict_contexts)}"
    return True, None


def route_strategies(
    candidate: Mapping[str, Any] | None,
    *,
    registry: Mapping[str, Mapping[str, Any]] | None = None,
    safety_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    reg = {key: normalize_strategy_record(value) for key, value in (registry or get_strategy_registry()).items()}
    context = build_context_bucket(safe_candidate)
    asset_type = _norm(context.get("asset_type"))
    market_type = _norm(context.get("market_type"))
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for strategy in sorted(reg.values(), key=lambda row: row["strategy_id"]):
        strategy_id = str(strategy.get("strategy_id"))
        if not _asset_matches(strategy, asset_type):
            skipped.append({"strategy_id": strategy_id, "reason": f"asset_type_not_supported:{asset_type}"})
            continue
        if not _market_matches(strategy, market_type):
            skipped.append({"strategy_id": strategy_id, "reason": f"market_type_not_supported:{market_type}"})
            continue
        context_ok, context_reason = _context_allowed(strategy, context)
        if not context_ok:
            skipped.append({"strategy_id": strategy_id, "reason": context_reason})
            continue
        maturity = evaluate_strategy_maturity(strategy, candidate=safe_candidate)
        if maturity["blocked"]:
            blocked.append(
                {
                    "strategy_id": strategy_id,
                    "maturity_status": maturity["maturity_status"],
                    "blocked_reason": maturity["blocked_reason"],
                    "missing_required_inputs": maturity["missing_required_inputs"],
                }
            )
            continue
        selected.append(
            {
                "strategy_id": strategy_id,
                "strategy_family": strategy.get("strategy_family"),
                "maturity_status": maturity["maturity_status"],
                "can_affect_review": maturity["can_affect_review"],
                "can_affect_ranking": maturity["can_affect_ranking"],
                "can_affect_execution": False,
                "missing_optional_inputs": maturity["missing_optional_inputs"],
            }
        )

    if safety_status and bool(safety_status.get("execution_allowed", False)):
        # Router never inherits execution authority from upstream inputs.
        safety_status = {**dict(safety_status), "execution_allowed": False}

    return {
        "ok": True,
        "status": "strategy_routing_complete",
        "candidate_id": safe_candidate.get("candidate_id") or safe_candidate.get("id") or safe_candidate.get("ticker"),
        "context_bucket": context,
        "selected_strategies": selected,
        "skipped_strategies": skipped,
        "blocked_strategies": blocked,
        "selected_strategy_ids": [row["strategy_id"] for row in selected],
        "skipped_strategy_ids": [row["strategy_id"] for row in skipped],
        "blocked_strategy_ids": [row["strategy_id"] for row in blocked],
        "universal_strategy_agreement_required": False,
        "missing_optional_strategy_blocks_review": False,
        **locked_safety_flags(),
    }
