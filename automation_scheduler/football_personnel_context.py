from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    clamp,
    compact_list,
    finalize_football_response,
    missing_fields,
    percent_score,
    score_from_range,
    weighted_average,
)


PERSONNEL_INPUTS = (
    "offensive_personnel_rate_11",
    "offensive_personnel_rate_12",
    "offensive_personnel_rate_21",
    "heavy_personnel_rate",
    "shotgun_rate",
    "motion_rate",
    "play_action_rate",
    "rpo_rate",
    "no_huddle_rate",
    "defensive_nickel_rate",
    "defensive_dime_rate",
    "box_count",
    "blitz_rate",
    "pressure_rate",
    "man_coverage_rate",
    "zone_coverage_rate",
    "two_high_rate",
    "single_high_rate",
)


def evaluate_football_personnel_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    spread_personnel = weighted_average(
        (
            (score_from_range(source.get("offensive_personnel_rate_11"), low=0.35, high=0.82), 0.75),
            (score_from_range(source.get("shotgun_rate"), low=0.35, high=0.88), 0.55),
            (score_from_range(source.get("motion_rate"), low=0.18, high=0.72), 0.55),
            (score_from_range(source.get("rpo_rate"), low=0.0, high=0.18), 0.25),
        )
    )
    heavy_personnel = weighted_average(
        (
            (score_from_range(source.get("offensive_personnel_rate_12"), low=0.05, high=0.38), 0.45),
            (score_from_range(source.get("offensive_personnel_rate_21"), low=0.0, high=0.20), 0.25),
            (score_from_range(source.get("heavy_personnel_rate"), low=0.02, high=0.32), 0.45),
        )
    )
    formation_fit = weighted_average(
        (
            (spread_personnel, 0.65),
            (score_from_range(source.get("play_action_rate"), low=0.10, high=0.38), 0.45),
            (score_from_range(source.get("no_huddle_rate"), low=0.0, high=0.28), 0.3),
            (heavy_personnel, 0.25),
        )
    )
    pressure_stress = weighted_average(
        (
            (score_from_range(source.get("blitz_rate"), low=0.12, high=0.46), 0.55),
            (score_from_range(source.get("pressure_rate"), low=0.22, high=0.46), 0.75),
            (score_from_range(source.get("defensive_dime_rate"), low=0.04, high=0.32), 0.25),
        )
    )
    box_stress = score_from_range(source.get("box_count"), low=5.0, high=8.5)
    coverage_complexity = weighted_average(
        (
            (score_from_range(source.get("man_coverage_rate"), low=0.12, high=0.48), 0.35),
            (score_from_range(source.get("two_high_rate"), low=0.18, high=0.62), 0.35),
            (score_from_range(source.get("single_high_rate"), low=0.18, high=0.62), 0.25),
            (score_from_range(source.get("defensive_nickel_rate"), low=0.35, high=0.82), 0.2),
        )
    )
    personnel_fit = weighted_average(((spread_personnel, 0.55), (heavy_personnel, 0.25), (formation_fit, 0.65)))
    matchup_stress = weighted_average(((pressure_stress, 0.75), (box_stress, 0.55), (coverage_complexity, 0.55)))
    tendency_risk = weighted_average(
        (
            (score_from_range(source.get("offensive_personnel_rate_11"), low=0.35, high=0.90), 0.25),
            (score_from_range(source.get("shotgun_rate"), low=0.35, high=0.95), 0.25),
            (100.0 - (percent_score(source.get("motion_rate")) or 0.0), 0.25),
        )
    )
    flags = []
    if (pressure_stress or 0.0) >= 70.0:
        flags.append("defensive_pressure_structure_volatility")
    if (box_stress or 0.0) >= 70.0:
        flags.append("loaded_box_run_game_volatility")
    if (score_from_range(source.get("two_high_rate"), low=0.18, high=0.62) or 0.0) >= 70.0:
        flags.append("two_high_shell_deep_passing_constraint")
    if (tendency_risk or 0.0) >= 75.0:
        flags.append("offensive_tendency_predictability_risk")
    hints = compact_list(
        [
            "passing_volume" if (spread_personnel or 0.0) >= 60.0 else None,
            "rushing_volume" if (heavy_personnel or 0.0) >= 55.0 else None,
            "sacks_interceptions" if (pressure_stress or 0.0) >= 65.0 else None,
            "receiving_depth_props" if (score_from_range(source.get("two_high_rate"), low=0.18, high=0.62) or 0.0) >= 65.0 else None,
        ],
        limit=10,
    )

    return finalize_football_response(
        {
            "personnel_fit_score": round(clamp(personnel_fit or 0.0), 2),
            "formation_fit_score": round(clamp(formation_fit or 0.0), 2),
            "matchup_stress_score": round(clamp(matchup_stress or 0.0), 2),
            "defensive_structure_risk": round(clamp(matchup_stress or 0.0), 2),
            "offensive_tendency_score": round(clamp(100.0 - (tendency_risk or 0.0)), 2),
            "offensive_tendency_risk": round(clamp(tendency_risk or 0.0), 2),
            "volatility_flags": compact_list(flags or ["personnel_context_modifier_only"], limit=10),
            "market_relevance_hints": hints,
            "missing_inputs": compact_list(missing_fields(source, PERSONNEL_INPUTS), limit=30),
            "edge_fabricated": False,
        },
        source_payload=source,
    )
