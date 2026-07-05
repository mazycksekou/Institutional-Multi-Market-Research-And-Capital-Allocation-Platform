from __future__ import annotations

from typing import Any

from .soccer_impact_common import clamp, compact_list, finalize_soccer_response, missing_fields, score_centered, score_from_range, weighted_average


CORE_FIELDS = (
    "xg_for",
    "xg_against",
    "non_penalty_xg_for",
    "non_penalty_xg_against",
    "expected_threat_for",
    "possession_value_for",
    "field_tilt",
)


def evaluate_soccer_possession_value_impact(row: dict[str, Any] | None = None, *, data_tier: int = 0, market_type: str = "three_way_moneyline") -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    sample_size = source.get("sample_size") or source.get("matches_sample_size") or source.get("matches")
    insufficient_sample = sample_size is not None and float(sample_size or 0) < 8

    shot_score = weighted_average(
        (
            (score_from_range(source.get("shots_for_per_game"), low=5, high=20), 0.45),
            (score_from_range(source.get("shots_against_per_game"), low=5, high=20, inverse=True), 0.35),
            (score_from_range(source.get("shots_on_target_for"), low=1, high=8), 0.35),
            (score_from_range(source.get("shots_on_target_against"), low=1, high=8, inverse=True), 0.25),
        )
    )
    xg_quality = weighted_average(
        (
            (score_from_range(source.get("xg_for"), low=0.4, high=2.8), 0.7),
            (score_from_range(source.get("xg_against"), low=0.4, high=2.8, inverse=True), 0.55),
            (score_from_range(source.get("non_penalty_xg_for"), low=0.3, high=2.5), 0.85),
            (score_from_range(source.get("non_penalty_xg_against"), low=0.3, high=2.5, inverse=True), 0.7),
            (score_from_range(source.get("xg_per_shot"), low=0.04, high=0.18), 0.45),
        )
    )
    chance_quality = weighted_average(
        (
            (xg_quality, 0.65),
            (score_from_range(source.get("big_chances_for"), low=0, high=5), 0.35),
            (score_from_range(source.get("big_chances_against"), low=0, high=5, inverse=True), 0.25),
            (score_from_range(source.get("box_entries_for"), low=6, high=34), 0.25),
            (score_from_range(source.get("penalty_area_touches_for"), low=6, high=38), 0.25),
        )
    )
    territorial = weighted_average(
        (
            (score_centered(source.get("field_tilt"), center=0.5, span=0.22), 0.75),
            (score_centered(source.get("possession_share"), center=0.5, span=0.24), 0.35),
            (score_from_range(source.get("final_third_entries"), low=18, high=70), 0.35),
            (score_from_range(source.get("box_entries_for"), low=6, high=34), 0.25),
        )
    )
    progression = weighted_average(
        (
            (score_from_range(source.get("progressive_passes"), low=15, high=85), 0.45),
            (score_from_range(source.get("progressive_carries"), low=5, high=45), 0.35),
            (score_from_range(source.get("passes_into_final_third"), low=15, high=85), 0.35),
            (score_from_range(source.get("passes_into_penalty_area"), low=2, high=22), 0.35),
            (score_from_range(source.get("carries_into_box"), low=0, high=12), 0.25),
        )
    )
    xt_score = weighted_average(
        (
            (score_from_range(source.get("expected_threat_for"), low=0.2, high=2.8), 0.7),
            (score_from_range(source.get("expected_threat_against"), low=0.2, high=2.8, inverse=True), 0.55),
            (score_from_range(source.get("xT_created"), low=0.05, high=1.2), 0.35),
        )
    )
    obv_vaep = weighted_average(
        (
            (score_from_range(source.get("possession_value_for"), low=0.1, high=2.5), 0.55),
            (score_from_range(source.get("possession_value_against"), low=0.1, high=2.5, inverse=True), 0.45),
            (score_from_range(source.get("vaep_for"), low=0.1, high=2.5), 0.45),
            (score_from_range(source.get("vaep_against"), low=0.1, high=2.5, inverse=True), 0.35),
            (score_from_range(source.get("obv_for"), low=0.1, high=2.5), 0.35),
        )
    )
    possession_value = weighted_average(((xt_score, 0.45), (obv_vaep, 0.45), (progression, 0.2), (territorial, 0.15)))
    first_half = weighted_average(
        (
            (score_from_range(source.get("first_half_xg_for"), low=0.1, high=1.5), 0.65),
            (score_from_range(source.get("first_half_xg_against"), low=0.1, high=1.5, inverse=True), 0.5),
            (score_from_range(source.get("first_half_shots_for"), low=2, high=10), 0.3),
        )
    )
    open_play = weighted_average(
        (
            (score_from_range(source.get("non_penalty_xg_for"), low=0.3, high=2.5), 0.65),
            (progression, 0.25),
            (territorial, 0.25),
            (score_from_range(source.get("set_piece_xg_for"), low=0, high=0.8, inverse=True), 0.1),
        )
    )
    defense = weighted_average(
        (
            (score_from_range(source.get("xg_against"), low=0.4, high=2.8, inverse=True), 0.55),
            (score_from_range(source.get("non_penalty_xg_against"), low=0.3, high=2.5, inverse=True), 0.55),
            (score_from_range(source.get("shots_against_per_game"), low=5, high=20, inverse=True), 0.25),
            (score_from_range(source.get("box_entries_against"), low=6, high=34, inverse=True), 0.25),
        )
    )
    set_piece_attack = score_from_range(source.get("set_piece_xg_for"), low=0, high=0.9)
    set_piece_defense_risk = score_from_range(source.get("set_piece_xg_against"), low=0, high=0.9)
    direct_transition = weighted_average(((score_from_range(source.get("direct_attack_rate"), low=0, high=1), 0.35), (score_from_range(source.get("counterattack_xg"), low=0, high=0.8), 0.45)))
    limited_proxy = source.get("xg_for") in (None, "") and source.get("non_penalty_xg_for") in (None, "") and source.get("expected_threat_for") in (None, "")
    if limited_proxy:
        xg_quality = weighted_average(((score_from_range(source.get("goals_for_per_game"), low=0.4, high=2.8), 0.35), (score_from_range(source.get("goals_against_per_game"), low=0.4, high=2.8, inverse=True), 0.25), (shot_score, 0.3)))
        chance_quality = weighted_average(((xg_quality, 0.45), (shot_score, 0.35)))
    total_signal = weighted_average(((chance_quality, 0.45), (xg_quality, 0.4), (direct_transition, 0.25), (set_piece_attack, 0.2), (set_piece_defense_risk, 0.15))) or 0.0
    team_total_signal = weighted_average(((chance_quality, 0.45), (open_play, 0.35), (set_piece_attack, 0.25), (territorial, 0.2))) or 0.0
    btts_signal = weighted_average(((total_signal, 0.4), (score_from_range(source.get("xg_against"), low=0.4, high=2.8), 0.25), (set_piece_defense_risk, 0.15), (direct_transition, 0.2))) or 0.0
    if market_type.startswith("first_half"):
        total_signal = weighted_average(((total_signal, 0.55), (first_half, 0.75))) or total_signal

    missing = missing_fields(source, CORE_FIELDS)
    confidence_reason = None
    if data_tier <= 0:
        confidence_reason = "no_soccer_team_or_chance_context"
    elif limited_proxy:
        confidence_reason = "goals_shots_proxy_only_xg_xt_obv_missing"
    elif insufficient_sample:
        confidence_reason = "small_sample_soccer_chance_context"

    return finalize_soccer_response(
        {
            "possession_value_score": round(clamp(possession_value or chance_quality or 0.0), 2),
            "chance_quality_score": round(clamp(chance_quality or 0.0), 2),
            "territorial_dominance_score": round(clamp(territorial or 0.0), 2),
            "progression_score": round(clamp(progression or 0.0), 2),
            "final_third_pressure_score": round(clamp(weighted_average(((territorial, 0.45), (progression, 0.35))) or 0.0), 2),
            "box_entry_score": round(clamp(score_from_range(source.get("box_entries_for"), low=6, high=34) or score_from_range(source.get("penalty_area_touches_for"), low=6, high=38) or 0.0), 2),
            "xg_quality_score": round(clamp(xg_quality or 0.0), 2),
            "first_half_pressure_score": round(clamp(first_half or 0.0), 2),
            "open_play_attack_score": round(clamp(open_play or 0.0), 2),
            "defensive_suppression_score": round(clamp(defense or 0.0), 2),
            "total_signal_score": round(clamp(total_signal), 2),
            "team_total_signal_score": round(clamp(team_total_signal), 2),
            "btts_signal_score": round(clamp(btts_signal), 2),
            "set_piece_xg_component_score": round(clamp(set_piece_attack or 0.0), 2),
            "confidence_cap_reason": confidence_reason,
            "missing_inputs": compact_list(missing, limit=30),
            "insufficient_sample": bool(insufficient_sample),
            "limited_proxy": bool(limited_proxy),
            "xg_fabricated": False,
            "xt_fabricated": False,
            "obv_vaep_fabricated": False,
            "set_piece_xg_separated": source.get("set_piece_xg_for") not in (None, ""),
        },
        source_payload=source,
    )
