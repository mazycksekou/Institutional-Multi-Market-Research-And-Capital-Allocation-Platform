from __future__ import annotations

from typing import Any


def compare_settlement_rules(rule_sets: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rule_sets) < 2:
        return {"material_mismatch": False, "settlement_risk": 0.0, "mismatches": []}
    mismatches: list[str] = []
    overtime_values = {str(rule.get("includes_overtime", "unknown")).lower() for rule in rule_sets}
    void_values = {str(rule.get("void_on_push", "unknown")).lower() for rule in rule_sets}
    player_prop_values = {str(rule.get("player_prop_settlement", "unknown")).lower() for rule in rule_sets}
    prediction_values = {str(rule.get("prediction_resolution", "unknown")).lower() for rule in rule_sets}
    if len(overtime_values) > 1:
        mismatches.append("overtime_rule_mismatch")
    if len(void_values) > 1:
        mismatches.append("void_rule_mismatch")
    if len(player_prop_values) > 1:
        mismatches.append("player_prop_settlement_mismatch")
    if len(prediction_values) > 1:
        mismatches.append("prediction_market_resolution_mismatch")
    return {
        "material_mismatch": bool(mismatches),
        "settlement_risk": round(min(1.0, len(mismatches) * 0.25), 4),
        "mismatches": mismatches,
        "overtime_rule_match": "overtime_rule_mismatch" not in mismatches,
        "void_rule_match": "void_rule_mismatch" not in mismatches,
        "player_prop_rule_match": "player_prop_settlement_mismatch" not in mismatches,
        "prediction_market_resolution_match": "prediction_market_resolution_mismatch" not in mismatches,
    }
