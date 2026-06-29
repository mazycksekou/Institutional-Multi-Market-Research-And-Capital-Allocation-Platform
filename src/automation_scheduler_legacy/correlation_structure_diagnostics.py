from __future__ import annotations

from typing import Any

from .random_matrix_risk import evaluate_random_matrix_risk
from src.security.policy import locked_safety_flags


def diagnose_correlation_structure(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    rmt = evaluate_random_matrix_risk(payload or {})
    shock = float(rmt.get("correlation_shock_score", 0.0) or 0.0)
    if rmt.get("insufficient_matrix_data"):
        status = "insufficient_matrix_data"
        warning = "matrix_required_for_correlation_structure_diagnostics"
    elif bool(rmt.get("market_mode_detected")):
        status = "market_mode_detected"
        warning = "systemwide_correlation_mode_can_create_fake_idiosyncratic_edge"
    else:
        status = "no_market_mode_detected"
        warning = "no_rmt_market_mode_warning"
    payload_out = {
        "ok": True,
        "status": status,
        "correlation_shock_score": shock,
        "systemwide_noise_risk": rmt.get("systemwide_noise_risk"),
        "market_mode_detected": bool(rmt.get("market_mode_detected", False)),
        "idiosyncratic_signal_risk": rmt.get("idiosyncratic_signal_risk"),
        "correlation_warning": warning,
        "rmt": rmt,
    }
    payload_out.update(locked_safety_flags())
    payload_out["provider_write"] = False
    payload_out["execution_allowed"] = False
    payload_out["live_execution_enabled"] = False
    return payload_out
