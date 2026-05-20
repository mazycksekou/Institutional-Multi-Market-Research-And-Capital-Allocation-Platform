from __future__ import annotations

from typing import Any

import multi_sport_model_registry
from full_board_engine import build_full_board_preview
from logbook_engine import build_logbook_ready_row
from providers.market_normalizer import normalize_ticket_fields
from providers.odds_provider_router import enrich_ticket


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def parse_ticket(payload: dict[str, Any]) -> dict[str, Any]:
    ticket = normalize_ticket_fields(payload)
    teams = ticket.get("teams")
    if isinstance(teams, list) and len(teams) >= 2:
        ticket.setdefault("away_team", teams[0])
        ticket.setdefault("home_team", teams[1])
    return {
        "source_type": ticket.get("source_type") or "parsed_fields",
        "sport": ticket.get("sport"),
        "league": ticket.get("league"),
        "event": ticket.get("event"),
        "teams": ticket.get("teams") or [],
        "market": ticket.get("market"),
        "selection": ticket.get("selection"),
        "odds_american": ticket.get("odds_american"),
        "line": ticket.get("line"),
        "total_line": ticket.get("total_line"),
        "book": ticket.get("book"),
        "screenshot_text": ticket.get("screenshot_text"),
        "visible_markets": ticket.get("visible_markets") or [],
        "visible_props": ticket.get("visible_props") or [],
        "visible_alt_lines": ticket.get("visible_alt_lines") or [],
        "bankroll": ticket.get("bankroll"),
        "unit_size": ticket.get("unit_size"),
        "risk_profile": ticket.get("risk_profile") or "conservative",
        "input_stats": ticket.get("input_stats") or {},
    }


def analyze_screenshot_ticket(payload: dict[str, Any]) -> dict[str, Any]:
    ticket = parse_ticket(payload)
    required_for_ticket = ["sport", "market", "selection", "odds_american"]
    missing_ticket = [field for field in required_for_ticket if not _present(ticket.get(field))]
    if not _present(ticket.get("event")) and not _present(ticket.get("teams")):
        missing_ticket.append("event_or_teams")

    try:
        provider_enrichment = enrich_ticket(ticket)
    except Exception as exc:
        provider_enrichment = {
            "provider_status": "error",
            "provider_notes": f"Provider enrichment failed safely: {type(exc).__name__}",
        }
    model_payload = {
        "sport": ticket.get("sport"),
        "league": ticket.get("league"),
        "event_id": ticket.get("event"),
        "market": ticket.get("market"),
        "selection": ticket.get("selection"),
        "odds_american": ticket.get("odds_american"),
        "line": ticket.get("line") if ticket.get("line") is not None else ticket.get("total_line"),
        "sportsbook": ticket.get("book"),
        "bankroll": ticket.get("bankroll"),
        "unit_size": ticket.get("unit_size"),
        "risk_profile": ticket.get("risk_profile"),
        "input_stats": ticket.get("input_stats") or {},
    }
    model_analysis = multi_sport_model_registry.analyze_sport_model(model_payload)
    model_missing = model_analysis.get("missing_inputs") or []
    missing_inputs = list(dict.fromkeys(missing_ticket + model_missing))

    partial_model_mode = bool(missing_inputs or not model_analysis.get("true_probability"))
    no_bets = list(model_analysis.get("no_bets") or [])
    confidence = model_analysis.get("confidence")
    decision = model_analysis.get("decision")
    status = model_analysis.get("status")
    if partial_model_mode:
        no_bets.append({
            "reason": "partial_model_mode",
            "missing_inputs": missing_inputs,
            "confidence": confidence,
        })

    full_board_preview = build_full_board_preview(ticket, model_analysis, provider_enrichment)
    row = build_logbook_ready_row(ticket, model_analysis)
    row.update(model_analysis.get("logbook_ready_row") or {})
    row.setdefault("confidence", confidence)
    row.setdefault("decision", decision or "NO_BET")
    row.setdefault("status", status or "manual_review_required")
    log_rows = [row]
    full_board_preview["logbook_ready_rows"] = log_rows
    implied_probability = model_analysis.get("implied_probability")
    confirmed_bets = list(model_analysis.get("confirmed_bets") or [])
    suggested_stake = model_analysis.get("suggested_stake") if confirmed_bets else 0
    if not confirmed_bets and status == "evaluated_no_bet_low_confidence" and not any(
        no_bet.get("reason") == "low confidence" for no_bet in no_bets if isinstance(no_bet, dict)
    ):
        no_bets.append({
            "sport": model_analysis.get("sport") or ticket.get("sport"),
            "event": ticket.get("event"),
            "market": ticket.get("market"),
            "selection": ticket.get("selection"),
            "reason": "low confidence",
            "no_bet_reason": "low confidence",
            "confidence": confidence,
            "edge_percent": model_analysis.get("edge_percent") or model_analysis.get("edge"),
        })

    return {
        "ok": True,
        "endpoint": "ticketScreenshotAnalysis",
        "partial_model_mode": partial_model_mode,
        "parsed_ticket": ticket,
        "provider_enrichment": provider_enrichment,
        "model_analysis": model_analysis,
        "full_board_preview": full_board_preview,
        "missing_inputs": missing_inputs,
        "no_bets": no_bets,
        "confirmed_bets": confirmed_bets,
        "suggested_stake": suggested_stake or 0,
        "implied_probability": implied_probability,
        "confidence": confidence,
        "decision": decision,
        "status": status,
        "stake": suggested_stake or 0,
        "logbook_ready_rows": log_rows,
    }
