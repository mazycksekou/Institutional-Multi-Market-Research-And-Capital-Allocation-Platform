from __future__ import annotations

from typing import Any

import multi_sport_model_registry
from full_board_engine import build_full_board_preview
from logbook_engine import build_logbook_ready_row
from providers.market_normalizer import normalize_ticket_fields
from providers.odds_provider_router import enrich_ticket


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _identity(value: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(value.get("sport") or value.get("sport_key") or "").strip().lower(),
        str(value.get("event") or value.get("event_id") or "").strip().lower(),
        str(value.get("market") or "").strip().lower(),
        str(value.get("selection") or "").strip().lower(),
    )


def _confirmed_logbook_row(row: dict[str, Any]) -> bool:
    return (
        str(row.get("decision") or "").strip().upper() == "CONFIRMED_BET"
        and str(row.get("status") or "").strip().lower() == "confirmed_bet"
    )


def _collect_confirmed_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    confirmed_rows: list[dict[str, Any]] = []

    def collect_from_container(container: Any) -> None:
        if not isinstance(container, dict):
            return
        for bet in container.get("confirmed_bets") or []:
            if isinstance(bet, dict):
                confirmed_rows.append(bet)

    collect_from_container(response)
    collect_from_container(response.get("full_board_preview"))
    collect_from_container(response.get("full_board"))

    model_analysis = response.get("model_analysis")
    collect_from_container(model_analysis)
    if isinstance(model_analysis, dict):
        collect_from_container(model_analysis.get("full_board_preview"))
        collect_from_container(model_analysis.get("full_board"))

    for row in response.get("logbook_ready_rows") or []:
        if isinstance(row, dict) and _confirmed_logbook_row(row):
            confirmed_rows.append(row)

    return confirmed_rows


def _remove_confirmed_selection_no_bets(no_bets: list[dict[str, Any]], confirmed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    confirmed_identities = [_identity(bet) for bet in confirmed_rows if isinstance(bet, dict)]
    confirmed_keys = {identity for identity in confirmed_identities if all(identity)}
    if not confirmed_keys:
        return no_bets
    stale_reasons = {
        "required inputs missing",
        "confirmed bets disabled",
        "manual_review_required",
        "inactive_missing_data",
        "evaluated_no_bet",
        "evaluated_no_bet_low_confidence",
        "evaluated_no_bet_edge_too_small",
        "confirmed bet rules not satisfied",
        "sentiment data unavailable",
        "crowdsourced signal unavailable",
        "social signal not backtested",
        "crowd signal not calibrated",
    }

    def same_confirmed_selection(no_bet: dict[str, Any]) -> bool:
        sport, event, market, selection = _identity(no_bet)
        for confirmed_sport, confirmed_event, confirmed_market, confirmed_selection in confirmed_identities:
            if market != confirmed_market or selection != confirmed_selection:
                continue
            sport_matches = not sport or sport == confirmed_sport
            event_matches = not event or event == confirmed_event
            if sport_matches and event_matches:
                return True
        return False

    filtered = []
    for no_bet in no_bets:
        if _identity(no_bet) in confirmed_keys:
            continue
        reason = str(no_bet.get("reason") or no_bet.get("status") or "").strip()
        if same_confirmed_selection(no_bet) and (reason in stale_reasons or reason):
            continue
        filtered.append(no_bet)
    return filtered


def _remove_stale_no_bet_logbook_rows(rows: list[dict[str, Any]], confirmed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    confirmed_keys = {_identity(row) for row in confirmed_rows if isinstance(row, dict) and all(_identity(row))}
    if not confirmed_keys:
        return rows
    filtered = []
    for row in rows:
        if not isinstance(row, dict):
            filtered.append(row)
            continue
        if _identity(row) in confirmed_keys and not _confirmed_logbook_row(row):
            continue
        filtered.append(row)
    return filtered


def _cleanup_confirmed_selection_no_bets(response: dict[str, Any]) -> dict[str, Any]:
    confirmed_rows = _collect_confirmed_rows(response)
    if not confirmed_rows:
        return response
    response["no_bets"] = _remove_confirmed_selection_no_bets(list(response.get("no_bets") or []), confirmed_rows)
    response["logbook_ready_rows"] = _remove_stale_no_bet_logbook_rows(list(response.get("logbook_ready_rows") or []), confirmed_rows)
    for board_key in ("full_board_preview", "full_board"):
        board = response.get(board_key)
        if isinstance(board, dict):
            board["no_bets"] = _remove_confirmed_selection_no_bets(list(board.get("no_bets") or []), confirmed_rows)
            if "logbook_ready_rows" in board:
                board["logbook_ready_rows"] = _remove_stale_no_bet_logbook_rows(list(board.get("logbook_ready_rows") or []), confirmed_rows)
    model_analysis = response.get("model_analysis")
    if isinstance(model_analysis, dict):
        model_analysis["no_bets"] = _remove_confirmed_selection_no_bets(list(model_analysis.get("no_bets") or []), confirmed_rows)
        if "logbook_ready_rows" in model_analysis:
            model_analysis["logbook_ready_rows"] = _remove_stale_no_bet_logbook_rows(list(model_analysis.get("logbook_ready_rows") or []), confirmed_rows)
        for board_key in ("full_board_preview", "full_board"):
            model_board = model_analysis.get(board_key)
            if isinstance(model_board, dict):
                model_board["no_bets"] = _remove_confirmed_selection_no_bets(list(model_board.get("no_bets") or []), confirmed_rows)
                if "logbook_ready_rows" in model_board:
                    model_board["logbook_ready_rows"] = _remove_stale_no_bet_logbook_rows(list(model_board.get("logbook_ready_rows") or []), confirmed_rows)
    return response


def parse_ticket(payload: dict[str, Any]) -> dict[str, Any]:
    ticket = normalize_ticket_fields(payload)
    teams = ticket.get("teams")
    if isinstance(teams, list) and len(teams) >= 2:
        ticket.setdefault("away_team", teams[0])
        ticket.setdefault("home_team", teams[1])
    input_stats = ticket.get("input_stats") or {}
    sport_key = multi_sport_model_registry.normalize_sport_key(str(ticket.get("sport") or ""))
    normalization = multi_sport_model_registry.normalize_sport_inputs_for_model(
        sport=sport_key,
        market=ticket.get("market"),
        selection=ticket.get("selection"),
        input_stats=input_stats,
        ticket=ticket,
    )
    input_stats = normalization["input_stats"]
    for field in ("market", "selection", "line", "total_line", "sportsbook"):
        if ticket.get(field) is None and input_stats.get(field) is not None:
            ticket[field] = input_stats.get(field)
    if ticket.get("book") is None and input_stats.get("sportsbook") is not None:
        ticket["book"] = input_stats.get("sportsbook")
    if ticket.get("event") is None and input_stats.get("event") is not None:
        ticket["event"] = input_stats.get("event")
    if ticket.get("odds_american") is None and input_stats.get("odds_american") is not None:
        ticket["odds_american"] = input_stats.get("odds_american")
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
        "input_stats": input_stats,
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
    no_bets = _remove_confirmed_selection_no_bets(no_bets, confirmed_bets)
    full_board_preview["no_bets"] = _remove_confirmed_selection_no_bets(list(full_board_preview.get("no_bets") or []), confirmed_bets)
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

    response = {
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
        "raw_input_keys": model_analysis.get("raw_input_keys"),
        "normalized_input_keys": model_analysis.get("normalized_input_keys"),
        "missing_inputs_before_normalization": model_analysis.get("missing_inputs_before_normalization"),
        "missing_inputs_after_normalization": model_analysis.get("missing_inputs_after_normalization"),
        "sport_alias_resolved": model_analysis.get("sport_alias_resolved"),
        "normalizer_used": model_analysis.get("normalizer_used"),
    }
    return _cleanup_confirmed_selection_no_bets(response)
