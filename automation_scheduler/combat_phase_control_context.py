from __future__ import annotations

from typing import Any

from .combat_impact_common import SUPPORTED_COMBAT_PHASES, clamp, compact_list, finalize_combat_response, missing_fields, score_from_range, weighted_average


PHASE_FIELDS = {
    "OPEN_SPACE_STRIKING": "open_space_striking_control",
    "POCKET_BOXING": "pocket_boxing_control",
    "KICKING_RANGE": "kicking_range_control",
    "CLINCH": "clinch_control",
    "CAGE_WRESTLING": "cage_wrestling_control",
    "TAKEDOWN_ENTRY": "takedown_entry_success",
    "TOP_CONTROL": "top_control_success",
    "BOTTOM_SURVIVAL": "bottom_survival_success",
    "SCRAMBLE": "scramble_win_rate",
    "SUBMISSION_SEQUENCE": "submission_sequence_control",
    "GROUND_AND_POUND": "ground_and_pound_control",
    "BOXING_OUTSIDE": "footwork_ringcraft_score",
    "BOXING_INSIDE": "pocket_boxing_control",
}


def evaluate_combat_phase_control_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    phase_scores: dict[str, float] = {}
    for phase, field in PHASE_FIELDS.items():
        value = score_from_range(source.get(field), low=0.0, high=1.0)
        if value is not None:
            phase_scores[phase] = value
    distance = weighted_average(
        (
            (score_from_range(source.get("distance_management_score"), low=0.0, high=1.0), 0.35),
            (score_from_range(source.get("lead_hand_control"), low=0.0, high=1.0), 0.2),
            (score_from_range(source.get("footwork_ringcraft_score"), low=0.0, high=1.0), 0.2),
            (score_from_range(source.get("range_recovery_score"), low=0.0, high=1.0), 0.2),
        )
    )
    volatility = weighted_average(
        (
            (score_from_range(source.get("phase_transition_frequency"), low=0.0, high=1.0), 0.45),
            (100.0 - min(phase_scores.values()) if phase_scores else None, 0.25),
            (score_from_range(source.get("opponent_phase_weaknesses"), low=0.0, high=1.0), 0.2),
        )
    )
    control = weighted_average([(value, 1.0) for value in phase_scores.values()] + [(distance, 0.4)]) or 0.0
    preferred = max(phase_scores.items(), key=lambda item: item[1])[0] if phase_scores else "UNKNOWN"
    reasons = []
    if phase_scores.get("OPEN_SPACE_STRIKING", 0.0) >= 58:
        reasons.append("open_space_striking_control_supported")
    if phase_scores.get("CLINCH", 0.0) >= 58 or phase_scores.get("CAGE_WRESTLING", 0.0) >= 58:
        reasons.append("clinch_or_cage_control_supported")
    if phase_scores.get("TOP_CONTROL", 0.0) >= 58 or phase_scores.get("SCRAMBLE", 0.0) >= 58:
        reasons.append("top_bottom_scramble_phase_supported")
    missing = missing_fields(source, PHASE_FIELDS.values())
    no_bet = []
    if missing:
        no_bet.append("phase_control_missing_caps_advanced_confidence")
    if source.get("final_result") and not phase_scores:
        no_bet.append("phase_control_not_inferred_from_final_result")
    if volatility and volatility >= 65:
        no_bet.append("conflicting_phase_signals_reduce_confidence")
    return finalize_combat_response(
        {
            "phase_control_score": round(clamp(control), 2),
            "preferred_phase": preferred if preferred in SUPPORTED_COMBAT_PHASES else "UNKNOWN",
            "fighter_a_phase_edges": compact_list([phase for phase, value in phase_scores.items() if value >= 58], limit=10),
            "fighter_b_phase_edges": compact_list([phase for phase, value in phase_scores.items() if value <= 35], limit=10),
            "phase_volatility_score": round(clamp(volatility or 0.0), 2),
            "phase_mismatch_reasons": compact_list(reasons, limit=15),
            "market_relevance_modifier": round(clamp(weighted_average(((control, 0.55), (100.0 - (volatility or 0.0), 0.25), (distance, 0.2))) or 0.0), 2),
            "missing_inputs": compact_list(missing, limit=20),
            "phase_control_fabricated": False,
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

