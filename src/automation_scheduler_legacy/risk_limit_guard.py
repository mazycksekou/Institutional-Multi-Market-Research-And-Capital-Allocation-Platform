from __future__ import annotations

from typing import Any

from src.services.ledger_service import append_security_event
from .security_event_types import RISK_LIMIT_BLOCKED
from src.security.policy import locked_safety_flags


DEFAULT_RISK_LIMITS = {
    "max_order_notional": None,
    "max_daily_notional": None,
    "max_daily_loss": None,
    "max_position_count": None,
    "max_correlation_exposure": None,
    "max_provider_exposure": None,
    "max_asset_class_exposure": None,
    "max_slippage": None,
    "max_spread": None,
    "max_open_orders": None,
    "risk_limit_status": "execution_locked",
}


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_risk_limits(
    request: dict[str, Any] | None = None,
    *,
    risk_limits: dict[str, Any] | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
) -> dict[str, Any]:
    request = request if isinstance(request, dict) else {}
    risk_limits = risk_limits if isinstance(risk_limits, dict) else {}
    merged = {**DEFAULT_RISK_LIMITS, **risk_limits}
    blockers: list[str] = []
    warnings: list[str] = []
    missing = [key for key, value in merged.items() if key.startswith("max_") and value is None]
    if missing:
        blockers.append("risk_limits_missing")
    if merged.get("risk_limit_status") != "active":
        blockers.append("risk_limit_status_execution_locked")

    notional = _as_float(request.get("notional") or request.get("order_notional") or request.get("max_notional"))
    max_order = _as_float(merged.get("max_order_notional"))
    if notional is not None and max_order is not None and notional > max_order:
        blockers.append("max_order_notional_exceeded")

    spread = _as_float(request.get("spread") or request.get("spread_percent"))
    max_spread = _as_float(merged.get("max_spread"))
    if spread is not None and max_spread is not None and spread > max_spread:
        blockers.append("max_spread_exceeded")

    slippage = _as_float(request.get("slippage") or request.get("slippage_estimate"))
    max_slippage = _as_float(merged.get("max_slippage"))
    if slippage is not None and max_slippage is not None and slippage > max_slippage:
        blockers.append("max_slippage_exceeded")

    status = "blocked" if blockers else "warn_only"
    result = {
        "ok": not bool(blockers),
        "status": "risk_limit_blocked" if blockers else "risk_limit_warn_only",
        "risk_limit_status": "execution_locked" if blockers else "warn_only",
        "risk_limits": merged,
        "risk_blockers": sorted(set(blockers)),
        "risk_warnings": sorted(set(warnings)),
        "risk_guard_can_enable_execution": False,
        "risk_guard_action": status,
        **locked_safety_flags(),
    }
    if persist_audit and blockers:
        append_security_event(
            event_type=RISK_LIMIT_BLOCKED,
            actor_type="system",
            action_requested="risk_limit_check",
            denial_reason=";".join(sorted(set(blockers))),
            asset_type=request.get("asset_type"),
            market_type=request.get("market_type"),
            provider_name=request.get("provider"),
            request_payload={"request": request, "risk_limits": risk_limits},
            response_payload=result,
            base_data_dir=base_data_dir,
        )
    return result
