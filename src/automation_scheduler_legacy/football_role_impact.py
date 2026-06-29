from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    average_present,
    clamp,
    compact_list,
    confidence_from_sample,
    finalize_football_response,
    missing_fields,
    normalize_role,
    present_fields,
    safe_float,
    score_centered,
    score_from_range,
    weighted_average,
)


ROLE_INPUTS: dict[str, tuple[str, ...]] = {
    "QB": (
        "epa_per_dropback",
        "success_rate",
        "cpoe",
        "pressure_to_sack_rate",
        "time_to_throw",
        "air_yards_per_attempt",
        "deep_attempt_rate",
        "turnover_worthy_proxy",
        "scramble_epa",
        "red_zone_passing_epa",
        "third_down_epa",
        "play_action_efficiency",
        "blitz_efficiency",
    ),
    "RB": (
        "rush_epa",
        "rushing_success_rate",
        "explosive_rush_rate",
        "stuff_rate",
        "yards_before_contact_proxy",
        "yards_after_contact_proxy",
        "box_adjusted_efficiency",
        "route_participation",
        "target_share",
        "receiving_epa",
        "pass_protection_proxy",
    ),
    "WR": (
        "route_participation",
        "target_share",
        "first_read_target_proxy",
        "air_yard_share",
        "yards_per_route_run",
        "separation_proxy",
        "contested_target_rate",
        "catch_rate_over_expected_proxy",
        "yac_over_expected_proxy",
        "red_zone_target_share",
        "third_down_target_share",
        "explosive_reception_rate",
    ),
    "TE": (
        "route_participation",
        "target_share",
        "first_read_target_proxy",
        "air_yard_share",
        "yards_per_route_run",
        "separation_proxy",
        "contested_target_rate",
        "catch_rate_over_expected_proxy",
        "yac_over_expected_proxy",
        "red_zone_target_share",
        "third_down_target_share",
        "explosive_reception_rate",
    ),
    "OL": (
        "pressure_allowed_proxy",
        "sack_allowed_proxy",
        "run_block_success_proxy",
        "penalty_rate",
        "blown_block_proxy",
        "continuity_score",
    ),
    "DL": (
        "pressure_rate",
        "pass_rush_win_proxy",
        "sack_rate",
        "hurry_rate",
        "run_stop_rate",
        "havoc_rate",
        "containment_score",
    ),
    "EDGE": (
        "pressure_rate",
        "pass_rush_win_proxy",
        "sack_rate",
        "hurry_rate",
        "run_stop_rate",
        "havoc_rate",
        "containment_score",
    ),
    "LB": (
        "coverage_target_rate",
        "separation_allowed_proxy",
        "yards_allowed_per_target",
        "explosive_allowed_rate",
        "tackle_efficiency_proxy",
        "missed_tackle_proxy",
        "run_fit_score",
        "turnover_play_rate",
    ),
    "CB": (
        "coverage_target_rate",
        "separation_allowed_proxy",
        "yards_allowed_per_target",
        "explosive_allowed_rate",
        "tackle_efficiency_proxy",
        "missed_tackle_proxy",
        "run_fit_score",
        "turnover_play_rate",
    ),
    "S": (
        "coverage_target_rate",
        "separation_allowed_proxy",
        "yards_allowed_per_target",
        "explosive_allowed_rate",
        "tackle_efficiency_proxy",
        "missed_tackle_proxy",
        "run_fit_score",
        "turnover_play_rate",
    ),
}


def _role_from_source(row: dict[str, Any]) -> str:
    return normalize_role(row.get("role") or row.get("position") or row.get("player_role"))


def _sample_size(row: dict[str, Any]) -> float:
    for key in ("player_sample_size", "routes_run", "dropbacks", "rush_attempts", "targets", "snaps", "snap_count"):
        value = safe_float(row.get(key))
        if value is not None:
            return value
    games = safe_float(row.get("games_sample_size") or row.get("games"))
    return (games or 0.0) * 40.0


def _role_market_relevance(role: str) -> list[str]:
    mapping = {
        "QB": ["passing_yards", "passing_tds", "interceptions", "sacks", "spread", "total"],
        "RB": ["rushing_yards", "rushing_attempts", "receiving_yards", "anytime_td", "team_total"],
        "WR": ["receiving_yards", "receptions", "longest_reception", "anytime_td", "passing_yards"],
        "TE": ["receiving_yards", "receptions", "anytime_td", "team_total"],
        "OL": ["sacks", "rushing_yards", "spread", "total"],
        "DL": ["sacks", "rushing_yards_allowed", "spread", "total"],
        "EDGE": ["sacks", "interceptions", "spread", "passing_yards_allowed"],
        "LB": ["tackles", "sacks", "defensive_prop", "rushing_yards_allowed"],
        "CB": ["interceptions", "defensive_prop", "receiving_yards_allowed", "longest_reception"],
        "S": ["tackles", "interceptions", "defensive_prop", "explosive_pass_allowed"],
        "K": ["field_goals", "total", "spread"],
        "P": ["field_position", "spread", "total"],
    }
    return mapping.get(role, [])


def _evaluate_qb(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    efficiency = weighted_average(
        (
            (score_centered(row.get("epa_per_dropback"), center=0.0, span=0.28), 1.25),
            (score_from_range(row.get("success_rate"), low=0.34, high=0.56), 0.85),
            (score_centered(row.get("cpoe"), center=0.0, span=8.0), 0.8),
            (score_from_range(row.get("pressure_to_sack_rate"), low=0.08, high=0.28, inverse=True), 0.75),
            (score_centered(row.get("scramble_epa"), center=0.0, span=0.22), 0.35),
            (score_centered(row.get("third_down_epa"), center=0.0, span=0.35), 0.55),
            (score_centered(row.get("red_zone_passing_epa"), center=0.0, span=0.4), 0.55),
            (score_centered(row.get("play_action_efficiency"), center=0.0, span=0.35), 0.35),
            (score_centered(row.get("blitz_efficiency"), center=0.0, span=0.35), 0.45),
        )
    )
    usage = weighted_average(
        (
            (score_from_range(row.get("air_yards_per_attempt"), low=5.2, high=10.0), 0.55),
            (score_from_range(row.get("deep_attempt_rate"), low=0.05, high=0.22), 0.45),
            (score_from_range(row.get("dropbacks"), low=18.0, high=46.0), 0.65),
        )
    )
    volatility = weighted_average(
        (
            (score_from_range(row.get("turnover_worthy_proxy"), low=0.01, high=0.07), 0.8),
            (score_from_range(row.get("pressure_to_sack_rate"), low=0.08, high=0.28), 0.55),
            (score_from_range(row.get("deep_attempt_rate"), low=0.05, high=0.24), 0.25),
        )
    )
    return efficiency, usage, volatility


def _evaluate_rb(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    efficiency = weighted_average(
        (
            (score_centered(row.get("rush_epa"), center=0.0, span=0.22), 1.0),
            (score_from_range(row.get("rushing_success_rate"), low=0.34, high=0.56), 0.85),
            (score_from_range(row.get("explosive_rush_rate"), low=0.03, high=0.16), 0.55),
            (score_from_range(row.get("stuff_rate"), low=0.08, high=0.28, inverse=True), 0.65),
            (score_from_range(row.get("yards_before_contact_proxy"), low=0.4, high=2.4), 0.35),
            (score_from_range(row.get("yards_after_contact_proxy"), low=1.8, high=4.2), 0.55),
            (score_centered(row.get("box_adjusted_efficiency"), center=0.0, span=0.24), 0.75),
            (score_centered(row.get("receiving_epa"), center=0.0, span=0.24), 0.35),
            (score_from_range(row.get("pass_protection_proxy"), low=0.0, high=100.0), 0.2),
        )
    )
    usage = weighted_average(
        (
            (score_from_range(row.get("carry_share_recent") or row.get("carry_share"), low=0.10, high=0.72), 0.85),
            (score_from_range(row.get("route_participation"), low=0.05, high=0.58), 0.45),
            (score_from_range(row.get("target_share"), low=0.02, high=0.22), 0.35),
        )
    )
    volatility = weighted_average(((score_from_range(row.get("stuff_rate"), low=0.08, high=0.30), 0.75), (100.0 - (usage or 0.0), 0.35)))
    return efficiency, usage, volatility


def _evaluate_pass_catcher(row: dict[str, Any], role: str) -> tuple[float | None, float | None, float | None]:
    route_floor = 0.10 if role == "TE" else 0.20
    efficiency = weighted_average(
        (
            (score_from_range(row.get("yards_per_route_run"), low=0.6, high=3.4), 1.0),
            (score_centered(row.get("separation_proxy"), center=0.0, span=2.0), 0.5),
            (score_from_range(row.get("contested_target_rate"), low=0.04, high=0.35, inverse=True), 0.35),
            (score_centered(row.get("catch_rate_over_expected_proxy"), center=0.0, span=10.0), 0.55),
            (score_centered(row.get("yac_over_expected_proxy"), center=0.0, span=3.5), 0.45),
            (score_from_range(row.get("explosive_reception_rate"), low=0.04, high=0.24), 0.5),
        )
    )
    usage = weighted_average(
        (
            (score_from_range(row.get("route_participation"), low=route_floor, high=0.95), 0.95),
            (score_from_range(row.get("target_share"), low=0.05, high=0.34), 0.9),
            (score_from_range(row.get("first_read_target_proxy"), low=0.04, high=0.32), 0.65),
            (score_from_range(row.get("air_yard_share"), low=0.05, high=0.45), 0.65),
            (score_from_range(row.get("red_zone_target_share"), low=0.03, high=0.32), 0.35),
            (score_from_range(row.get("third_down_target_share"), low=0.03, high=0.30), 0.35),
        )
    )
    volatility = weighted_average(((score_from_range(row.get("air_yard_share"), low=0.05, high=0.50), 0.35), (score_from_range(row.get("contested_target_rate"), low=0.04, high=0.35), 0.45), (100.0 - (usage or 0.0), 0.45)))
    return efficiency, usage, volatility


def _evaluate_ol(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    efficiency = weighted_average(
        (
            (score_from_range(row.get("pressure_allowed_proxy"), low=0.08, high=0.42, inverse=True), 1.0),
            (score_from_range(row.get("sack_allowed_proxy"), low=0.01, high=0.12, inverse=True), 0.8),
            (score_from_range(row.get("run_block_success_proxy"), low=0.32, high=0.58), 0.9),
            (score_from_range(row.get("penalty_rate"), low=0.0, high=0.10, inverse=True), 0.45),
            (score_from_range(row.get("blown_block_proxy"), low=0.02, high=0.14, inverse=True), 0.65),
            (score_from_range(row.get("continuity_score"), low=0.0, high=100.0), 0.75),
        )
    )
    usage = score_from_range(row.get("snap_share_recent") or row.get("snap_share"), low=0.20, high=1.0)
    volatility = weighted_average(((score_from_range(row.get("pressure_allowed_proxy"), low=0.08, high=0.42), 0.55), (score_from_range(row.get("penalty_rate"), low=0.0, high=0.10), 0.4), (100.0 - (score_from_range(row.get("continuity_score"), low=0.0, high=100.0) or 0.0), 0.45)))
    return efficiency, usage, volatility


def _evaluate_front(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    efficiency = weighted_average(
        (
            (score_from_range(row.get("pressure_rate"), low=0.04, high=0.22), 0.9),
            (score_from_range(row.get("pass_rush_win_proxy"), low=0.04, high=0.28), 0.85),
            (score_from_range(row.get("sack_rate"), low=0.01, high=0.12), 0.65),
            (score_from_range(row.get("hurry_rate"), low=0.02, high=0.18), 0.45),
            (score_from_range(row.get("run_stop_rate"), low=0.02, high=0.16), 0.55),
            (score_from_range(row.get("havoc_rate"), low=0.02, high=0.18), 0.65),
            (score_from_range(row.get("containment_score"), low=0.0, high=100.0), 0.35),
        )
    )
    usage = score_from_range(row.get("snap_share_recent") or row.get("defensive_snap_share"), low=0.20, high=0.90)
    volatility = weighted_average(((score_from_range(row.get("sack_rate"), low=0.01, high=0.12), 0.35), (100.0 - (usage or 0.0), 0.35)))
    return efficiency, usage, volatility


def _evaluate_coverage(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    efficiency = weighted_average(
        (
            (score_from_range(row.get("coverage_target_rate"), low=0.06, high=0.24, inverse=True), 0.45),
            (score_from_range(row.get("separation_allowed_proxy"), low=0.5, high=3.2, inverse=True), 0.65),
            (score_from_range(row.get("yards_allowed_per_target"), low=4.5, high=10.5, inverse=True), 0.75),
            (score_from_range(row.get("explosive_allowed_rate"), low=0.04, high=0.24, inverse=True), 0.75),
            (score_from_range(row.get("tackle_efficiency_proxy"), low=0.65, high=0.95), 0.5),
            (score_from_range(row.get("missed_tackle_proxy"), low=0.03, high=0.22, inverse=True), 0.45),
            (score_from_range(row.get("run_fit_score"), low=0.0, high=100.0), 0.45),
            (score_from_range(row.get("turnover_play_rate"), low=0.0, high=0.08), 0.35),
        )
    )
    usage = score_from_range(row.get("snap_share_recent") or row.get("defensive_snap_share"), low=0.20, high=0.95)
    volatility = weighted_average(((score_from_range(row.get("explosive_allowed_rate"), low=0.04, high=0.24), 0.6), (score_from_range(row.get("missed_tackle_proxy"), low=0.03, high=0.22), 0.45), (100.0 - (usage or 0.0), 0.25)))
    return efficiency, usage, volatility


def evaluate_football_role_impact(
    row: dict[str, Any] | None = None,
    *,
    player_level_allowed: bool | None = None,
    data_tier: int | None = None,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    role = _role_from_source(source)
    if player_level_allowed is False:
        return finalize_football_response(
            {
                "role": role,
                "role_impact_score": 0.0,
                "role_usage_score": 0.0,
                "role_efficiency_score": 0.0,
                "role_volatility_score": 100.0,
                "role_confidence_cap": 20.0,
                "missing_role_inputs": ["player_participation", "snap_share"],
                "player_market_relevance": [],
                "player_level_allowed": False,
                "confidence_cap_reason": "player_level_data_not_available_for_data_tier",
                "data_tier": data_tier,
            },
            source_payload=source,
        )

    inputs = ROLE_INPUTS.get(role, ())
    present = present_fields(source, inputs)
    missing = missing_fields(source, inputs)
    if role == "UNKNOWN":
        impact = usage = efficiency = 0.0
        volatility = 75.0
        cap = 25.0
        cap_reason = "unknown_role"
    elif role == "QB":
        efficiency, usage, volatility = _evaluate_qb(source)
        impact = weighted_average(((efficiency, 1.15), (usage, 0.45), (100.0 - (volatility or 0.0), 0.35)))
    elif role == "RB":
        efficiency, usage, volatility = _evaluate_rb(source)
        impact = weighted_average(((efficiency, 1.05), (usage, 0.75), (100.0 - (volatility or 0.0), 0.25)))
    elif role in {"WR", "TE"}:
        efficiency, usage, volatility = _evaluate_pass_catcher(source, role)
        impact = weighted_average(((efficiency, 0.95), (usage, 0.95), (100.0 - (volatility or 0.0), 0.2)))
    elif role == "OL":
        efficiency, usage, volatility = _evaluate_ol(source)
        impact = weighted_average(((efficiency, 1.1), (usage, 0.55), (100.0 - (volatility or 0.0), 0.3)))
    elif role in {"DL", "EDGE"}:
        efficiency, usage, volatility = _evaluate_front(source)
        impact = weighted_average(((efficiency, 1.0), (usage, 0.55), (100.0 - (volatility or 0.0), 0.25)))
    elif role in {"LB", "CB", "S"}:
        efficiency, usage, volatility = _evaluate_coverage(source)
        impact = weighted_average(((efficiency, 1.0), (usage, 0.55), (100.0 - (volatility or 0.0), 0.25)))
    else:
        efficiency = average_present([score_from_range(source.get("snap_share_recent"), low=0.0, high=1.0), score_from_range(source.get("role_score"), low=0.0, high=100.0)])
        usage = score_from_range(source.get("snap_share_recent"), low=0.0, high=1.0)
        volatility = 50.0
        impact = weighted_average(((efficiency, 1.0), (usage, 0.5)))

    sample = _sample_size(source)
    cap = confidence_from_sample(sample, full_sample=350.0, floor=25.0, cap=92.0)
    cap_reason = locals().get("cap_reason")
    if role == "UNKNOWN":
        cap = min(cap, 25.0)
    elif not present:
        cap = min(cap, 35.0)
        cap_reason = "missing_role_inputs"
    elif len(present) < max(3, len(inputs) // 3):
        cap = min(cap, 55.0)
        cap_reason = "partial_role_inputs"

    result = {
        "role": role,
        "role_impact_score": round(clamp(impact or 0.0), 2),
        "role_usage_score": round(clamp(usage or 0.0), 2),
        "role_efficiency_score": round(clamp(efficiency or 0.0), 2),
        "role_volatility_score": round(clamp(volatility or 0.0), 2),
        "role_confidence_cap": round(clamp(cap), 2),
        "missing_role_inputs": compact_list(missing if role != "UNKNOWN" else ["role", "position"], limit=30),
        "player_market_relevance": _role_market_relevance(role),
        "player_level_allowed": True,
        "tracking_metrics_inferred": False,
        "confidence_cap_reason": cap_reason,
        "sample_size": int(sample),
        "data_tier": data_tier,
    }
    return finalize_football_response(result, source_payload=source)
