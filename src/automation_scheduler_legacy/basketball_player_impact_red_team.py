from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import clamp, compact_list, finalize_safe_response, safe_flags


def review_basketball_player_impact(
    candidate: dict[str, Any] | None = None,
    player_impact_result: dict[str, Any] | None = None,
    *,
    provider: str | None = None,
) -> dict[str, Any]:
    source = candidate if isinstance(candidate, dict) else {}
    result = player_impact_result if isinstance(player_impact_result, dict) else {}
    selected_provider = str(provider or "deterministic_internal").strip().lower()
    if selected_provider not in {"deterministic_internal", "deepseek", "openai"}:
        selected_provider = "deterministic_internal"

    reasons: list[str] = []
    missing: list[str] = []
    downgrade = 0.0

    possession_status = str(result.get("possession_impact", {}).get("possession_impact_status") or result.get("possession_impact_status") or "").lower()
    tracking_status = str(result.get("tracking_opportunity", {}).get("tracking_status") or result.get("tracking_status") or "").lower()
    role_change = bool(result.get("role_context", {}).get("role_change_detected") or result.get("role_change_detected"))
    calibration = result.get("calibration") if isinstance(result.get("calibration"), dict) else {}
    market_relevance = result.get("market_relevance") if isinstance(result.get("market_relevance"), dict) else {}
    availability = result.get("availability_minutes") if isinstance(result.get("availability_minutes"), dict) else {}
    incentive = result.get("incentive_context") if isinstance(result.get("incentive_context"), dict) else {}
    lineup = result.get("lineup_matchup_context") if isinstance(result.get("lineup_matchup_context"), dict) else {}

    if possession_status in {"missing", "partial"}:
        reasons.append("possession_impact_evidence_weak")
        missing.extend(result.get("possession_impact", {}).get("possession_impact_missing_inputs") or ["possession_level_inputs"])
        downgrade += 8.0 if possession_status == "partial" else 14.0
    if tracking_status in {"missing", "partial"} and any(str(market).endswith("_prop") for market in market_relevance.get("recommended_market_focus", [])):
        reasons.append("prop_relevance_depends_on_missing_tracking_opportunity")
        missing.extend(result.get("tracking_opportunity", {}).get("tracking_missing_inputs") or ["tracking_opportunity_inputs"])
        downgrade += 10.0 if tracking_status == "partial" else 16.0
    if calibration.get("insufficient_sample", True):
        reasons.append("low_calibration_support")
        missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])
        downgrade += 12.0
    if availability.get("minutes_stability_score", 100.0) < 45.0:
        reasons.append("weak_minutes_projection")
        missing.append("stable_projected_minutes")
        downgrade += 12.0
    if availability.get("availability_score", 100.0) < 45.0:
        reasons.append("availability_or_injury_risk")
        missing.append("current_injury_status")
        downgrade += 10.0
    if role_change:
        reasons.append("recent_role_change_uncertainty")
        missing.append("role_change_reason")
        downgrade += 6.0
    if lineup.get("lineup_matchup_status") == "partial":
        reasons.append("projected_lineup_uncertainty")
        missing.append("projected_starting_lineup")
        downgrade += 6.0
    if "player_incentive_may_conflict_with_team_market" in (incentive.get("incentive_warning_flags") or []):
        reasons.append("incentive_overfit_or_team_market_conflict")
        missing.append("incentive_team_alignment_evidence")
        downgrade += 8.0
    if not reasons:
        reasons.append("no_fatal_red_team_warning")

    status = "downgrade" if downgrade >= 12.0 else ("watch" if downgrade > 0.0 else "pass_review_only")
    payload = {
        "player_impact_red_team_status": status,
        "red_team_provider": selected_provider,
        "red_team_only": True,
        "red_team_reasons": compact_list(reasons, limit=20),
        "red_team_downgrade": round(clamp(downgrade), 2),
        "missing_data_requested": compact_list(missing, limit=30),
        "approval_granted": False,
        "bet_slip_created": False,
        **safe_flags(red_team_only=True),
    }
    return finalize_safe_response(payload, source_payload={"candidate": source, "result": result}, red_team_only=True)
