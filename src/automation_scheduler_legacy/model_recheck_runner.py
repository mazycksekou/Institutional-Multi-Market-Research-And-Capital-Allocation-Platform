from __future__ import annotations

from typing import Any

import multi_sport_model_registry as registry


def _candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    input_stats = dict(candidate.get("input_stats") or {})
    for key in ("player", "opponent", "team", "selection", "market", "odds_american"):
        if candidate.get(key) is not None and key not in input_stats:
            input_stats[key] = candidate[key]
    return {
        "sport": candidate.get("sport"),
        "market": candidate.get("market"),
        "selection": candidate.get("selection"),
        "event_id": candidate.get("event_id"),
        "odds_american": candidate.get("odds_american"),
        "bankroll": candidate.get("bankroll", 1000),
        "unit_size": candidate.get("unit_size", 25),
        "risk_profile": candidate.get("risk_profile", "medium"),
        "input_stats": input_stats,
    }


def run_model_recheck(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = _candidate_payload(candidate)
    sport = str(payload.get("sport") or "")
    config = registry.get_sport_model_config(sport)
    if not config:
        return {"status": "skipped_unknown_sport", "sport": sport, "missing_inputs": [], "confirmed_bets": []}

    normalized = registry.normalize_sport_inputs_for_model(
        sport=payload["sport"],
        market=payload["market"],
        selection=payload["selection"],
        input_stats=payload["input_stats"],
        ticket=payload,
    )
    payload["input_stats"] = normalized["input_stats"]

    missing_inputs = []
    for field in config.get("required_inputs", []):
        value = payload["input_stats"].get(field)
        if value in (None, "", [], {}):
            missing_inputs.append(field)
    if missing_inputs:
        return {
            "status": "skipped_missing_inputs",
            "sport": sport,
            "missing_inputs": missing_inputs,
            "confirmed_bets": [],
            "reason": "Required inputs missing for local model recheck.",
        }

    response = registry.analyze_sport_model(payload)
    confirmed_bets = list(response.get("confirmed_bets") or [])
    enrichment_only_fields = {"public_betting_percent", "sharp_money_percent", "social_sentiment", "news_velocity", "market_movement"}
    if set(payload["input_stats"]).issubset(enrichment_only_fields):
        confirmed_bets = []
        response["no_bet_flags"] = list(response.get("no_bet_flags") or []) + ["enrichment-only data cannot confirm"]

    return {
        "status": "completed",
        "sport": sport,
        "model_status": response.get("model_status"),
        "model_name": response.get("model_name"),
        "missing_inputs": list(response.get("missing_inputs") or []),
        "confirmed_bets": confirmed_bets,
        "no_bet_flags": list(response.get("no_bet_flags") or []),
        "true_probability": response.get("true_probability"),
    }
