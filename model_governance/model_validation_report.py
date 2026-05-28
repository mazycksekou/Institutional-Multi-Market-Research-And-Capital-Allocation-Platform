from __future__ import annotations

from typing import Any


def build_model_validation_report(
    *,
    model_id: str,
    activation_tier: str,
    input_quality_gate_result: dict[str, Any],
    calibration_gate_result: dict[str, Any],
    backtest_gate_result: dict[str, Any],
    walk_forward_gate_result: dict[str, Any],
    risk_gate_result: dict[str, Any],
    drift_gate_result: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "input_quality_gate_result": input_quality_gate_result,
        "calibration_gate_result": calibration_gate_result,
        "backtest_gate_result": backtest_gate_result,
        "walk_forward_gate_result": walk_forward_gate_result,
        "risk_gate_result": risk_gate_result,
        "drift_gate_result": drift_gate_result,
    }
    blocked = [name for name, result in gates.items() if not result.get("passes_gate", not result.get("blocked", False))]
    return {
        "model_id": model_id,
        "activation_tier": activation_tier,
        "gates": gates,
        "blocked_gates": blocked,
        "validation_status": "approved" if not blocked else "blocked_by_governance",
    }

