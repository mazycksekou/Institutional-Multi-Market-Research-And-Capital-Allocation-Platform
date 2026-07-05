from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from src.providers import resolve_sport_key


ACTION_SAFE_EVENT_KEYS: frozenset[str] = frozenset({
    "provider",
    "provider_type",
    "provider_event_id",
    "event_id",
    "id",
    "sport_key",
    "league",
    "commence_time",
    "home_team",
    "away_team",
    "event_ticker",
    "series_ticker",
    "title",
    "category",
    "status",
})

ACTION_ODDS_LINE_KEYS: frozenset[str] = frozenset({
    "provider",
    "provider_type",
    "provider_event_id",
    "sport_key",
    "market",
    "sportsbook",
    "selection",
    "price_american",
    "price_decimal",
    "implied_probability",
    "point",
    "last_update",
})


class ActionBettingService:
    def __init__(
        self,
        provider_router: Any,
        *,
        default_markets: str,
        default_bookmakers: str,
    ) -> None:
        self.provider_router = provider_router
        self.default_markets = default_markets
        self.default_bookmakers = default_bookmakers

    @staticmethod
    def normalize_action_league_input(league: str) -> str:
        raw = (league or "").strip() or "baseball_mlb"
        if raw.lower().replace("-", "_") == "mlb":
            return "baseball_mlb"
        return raw

    @staticmethod
    def slim_events_for_action(events: Any, limit: int) -> list[dict[str, Any]]:
        if not isinstance(events, list):
            return []
        cap = max(0, min(int(limit), 100))
        out: list[dict[str, Any]] = []
        for event in events[:cap]:
            if not isinstance(event, dict):
                continue
            row = {key: event[key] for key in ACTION_SAFE_EVENT_KEYS if key in event}
            if not row:
                provider_id = event.get("id") or event.get("event_id") or event.get("provider_event_id")
                if provider_id is not None:
                    row = {"provider_event_id": provider_id, "event_id": provider_id, "id": provider_id}
            out.append(row)
        return out

    @staticmethod
    def parse_markets_requested(markets_csv: str) -> list[str]:
        parts = [part.strip() for part in (markets_csv or "").split(",") if part.strip()]
        return parts if parts else ["h2h", "spreads", "totals"]

    @staticmethod
    def build_markets_and_bookmakers(flat_odds: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not isinstance(flat_odds, list):
            return [], []
        by_market: dict[str, list[dict[str, Any]]] = {}
        books: dict[str, dict[str, str]] = {}
        for row in flat_odds:
            if not isinstance(row, dict):
                continue
            slim = {key: row[key] for key in ACTION_ODDS_LINE_KEYS if key in row}
            market = str(slim.get("market") or "unknown")
            by_market.setdefault(market, []).append(slim)
            sportsbook = slim.get("sportsbook")
            if sportsbook is not None and str(sportsbook) not in books:
                key = str(sportsbook)
                books[key] = {"key": key, "title": key}
        markets_out = [{"market_key": key, "lines": value} for key, value in sorted(by_market.items())]
        bookmakers_out = sorted(books.values(), key=lambda book: book["key"])
        return markets_out, bookmakers_out

    @staticmethod
    def event_odds_fail(
        endpoint_id: str,
        event_id: str,
        league_val: str,
        provider_val: str,
        markets_requested: list[str],
        error: str,
        detail: str,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "event_id": event_id,
            "league": league_val,
            "provider": provider_val,
            "markets_requested": markets_requested,
            "markets": [],
            "bookmakers": [],
            "error": error,
            "detail": detail,
        }

    async def fetch_active_events_envelope(
        self,
        league: str,
        provider: Optional[str],
        limit: int,
    ) -> dict[str, Any]:
        endpoint_id = "getActiveBettingEvents"
        league_param = self.normalize_action_league_input(league)
        provider_used = (provider or "").strip() or None
        default_provider = self.provider_router.default_betting_provider()
        resolved_provider = provider_used or default_provider
        sport_key_out: Optional[str] = None

        try:
            sport_key, _label, resolve_err = resolve_sport_key(None, league_param)
            if resolve_err:
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": league_param,
                    "provider": resolved_provider,
                    "count": 0,
                    "events": [],
                    "error": str(resolve_err.get("error_type") or "UNKNOWN_SPORT"),
                    "detail": str(resolve_err.get("message") or "Unknown sport or league."),
                }
            sport_key_out = sport_key

            payload = await self.provider_router.get_active_events(provider_used, None, league_param)

            if not isinstance(payload, dict):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": sport_key_out or league_param,
                    "provider": resolved_provider,
                    "count": 0,
                    "events": [],
                    "error": "INVALID_RESPONSE",
                    "detail": "Provider returned an unexpected payload.",
                }

            if not payload.get("ok"):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": str(payload.get("sport_key") or sport_key_out or league_param),
                    "provider": str(payload.get("provider") or resolved_provider),
                    "count": 0,
                    "events": [],
                    "error": str(payload.get("error_type") or "PROVIDER_ERROR"),
                    "detail": str(payload.get("message") or "Provider request failed."),
                }

            events_src = payload.get("events")
            if not isinstance(events_src, list) and isinstance(payload.get("data"), list):
                events_src = payload["data"]
            if not isinstance(events_src, list):
                events_src = []

            slim = self.slim_events_for_action(events_src, limit)
            league_out = str(payload.get("sport_key") or sport_key_out or league_param)

            return {
                "ok": True,
                "endpoint": endpoint_id,
                "league": league_out,
                "provider": str(payload.get("provider") or resolved_provider),
                "count": len(slim),
                "events": slim,
                "error": None,
                "detail": None,
            }
        except Exception:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(sport_key_out or league_param),
                "provider": str(provider_used or default_provider),
                "count": 0,
                "events": [],
                "error": "UNEXPECTED_ERROR",
                "detail": "Active events request failed.",
            }

    async def fetch_event_odds_envelope(
        self,
        event_id: str,
        league: str,
        provider: Optional[str],
        markets_csv: str,
        bookmakers_csv: str,
    ) -> dict[str, Any]:
        endpoint_id = "getEventOdds"
        league_param = self.normalize_action_league_input(league)
        provider_used = (provider or "").strip() or None
        default_provider = self.provider_router.default_betting_provider()
        resolved_provider = provider_used or default_provider
        markets_requested = self.parse_markets_requested(markets_csv)
        sport_key_out: Optional[str] = None

        try:
            sport_key, _label, resolve_err = resolve_sport_key(None, league_param)
            if resolve_err:
                return self.event_odds_fail(
                    endpoint_id,
                    event_id,
                    league_param,
                    resolved_provider,
                    markets_requested,
                    str(resolve_err.get("error_type") or "UNKNOWN_SPORT"),
                    str(resolve_err.get("message") or "Unknown sport or league."),
                )
            sport_key_out = sport_key

            payload = await self.provider_router.get_event_odds(
                provider_used,
                event_id,
                None,
                league_param,
                markets=markets_csv or self.default_markets,
                bookmakers=bookmakers_csv or self.default_bookmakers,
            )

            if not isinstance(payload, dict):
                return self.event_odds_fail(
                    endpoint_id,
                    event_id,
                    str(sport_key_out or league_param),
                    resolved_provider,
                    markets_requested,
                    "INVALID_RESPONSE",
                    "Provider returned an unexpected payload.",
                )

            if not payload.get("ok"):
                return self.event_odds_fail(
                    endpoint_id,
                    event_id,
                    str(payload.get("sport_key") or sport_key_out or league_param),
                    str(payload.get("provider") or resolved_provider),
                    markets_requested,
                    str(payload.get("error_type") or "PROVIDER_ERROR"),
                    str(payload.get("message") or "Provider request failed."),
                )

            flat = payload.get("odds")
            markets_block, books_block = self.build_markets_and_bookmakers(flat)
            league_out = str(payload.get("sport_key") or sport_key_out or league_param)

            return {
                "ok": True,
                "endpoint": endpoint_id,
                "event_id": event_id,
                "league": league_out,
                "provider": str(payload.get("provider") or resolved_provider),
                "markets_requested": markets_requested,
                "markets": markets_block,
                "bookmakers": books_block,
                "error": None,
                "detail": None,
            }
        except HTTPException as exc:
            detail = exc.detail
            if not isinstance(detail, str):
                detail = "Request rejected."
            return self.event_odds_fail(
                endpoint_id,
                event_id,
                str(sport_key_out or league_param),
                str(provider_used or default_provider),
                markets_requested,
                "HTTP_ERROR",
                detail,
            )
        except Exception:
            return self.event_odds_fail(
                endpoint_id,
                event_id,
                str(sport_key_out or league_param),
                str(provider_used or default_provider),
                markets_requested,
                "UNEXPECTED_ERROR",
                "Event odds request failed.",
            )

# BEGIN ANALYZE_BETTING_EVENT_PIPELINE_SERVICE
async def analyze_betting_event_pipeline(
    payload,
    *,
    action_betting_service,
    default_bookmakers,
    price_event,
    calculate_model_probability,
    evaluate_lines,
    PriceEventRequest,
    ModelProbabilityRequest,
    EvaluateLinesRequest,
    multi_sport_model_registry,
    utc_now,
):
    """
    Canonical action-betting service orchestration for analyzeBettingEvent.

    This owns the full action pipeline:
    fetch odds -> price event -> model probability -> evaluate lines -> categorize output.

    FastAPI routes should only adapt HTTP/schema concerns and call this service.
    Tests should call this service with injected fake dependencies instead of patching main.py
    or extracted route closures.
    """
    endpoint_id = "analyzeBettingEvent"
    markets_requested = action_betting_service.parse_markets_requested(payload.markets)

    try:
        # Step 1: Fetch odds using Action safe odds logic
        step = "fetch_odds"
        odds_response = await action_betting_service.fetch_event_odds_envelope(
            event_id=payload.event_id,
            league=payload.league,
            provider=payload.provider,
            markets_csv=payload.markets,
            bookmakers_csv=default_bookmakers,
        )

        if not odds_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": None,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to fetch odds: {odds_response.get('detail', 'Unknown error')}"],
                "model_limitations": [],
                "missing_inputs": [],
                "active_inputs": [],
                "market_summary": [],
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": odds_response.get("error", "ODDS_FETCH_FAILED"),
                "detail": odds_response.get("detail", "Failed to fetch event odds"),
                "step_failed": step,
            }

        # Step 2: Price the event using priceBettingEvent logic
        step = "price_event"
        price_request = PriceEventRequest(
            sport=payload.sport,
            event_id=payload.event_id,
            league=payload.league,
            markets=payload.markets,
            provider=payload.provider,
            bankroll=payload.bankroll,
            unit_size=payload.unit_size,
            risk_profile=payload.risk_profile,
            model_probabilities=None,
        )

        price_response = await price_event(price_request)

        if not price_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": None,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to price event: {price_response.get('detail', 'Unknown error')}"],
                "model_limitations": [],
                "missing_inputs": [],
                "active_inputs": [],
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": price_response.get("error", "EVENT_PRICING_FAILED"),
                "detail": price_response.get("detail", "Failed to price betting event"),
                "step_failed": step,
            }

        # Step 3: Estimate model probabilities
        step = "estimate_probabilities"
        independent_inputs = payload.independent_inputs or {}
        model_request = ModelProbabilityRequest(
            market_probability=None,
            projection_probability=independent_inputs.get("projection_probability"),
            pitcher_adjustment=independent_inputs.get("pitcher_adjustment"),
            weather_adjustment=independent_inputs.get("weather_adjustment"),
            lineup_adjustment=independent_inputs.get("lineup_adjustment"),
            bullpen_adjustment=independent_inputs.get("bullpen_adjustment"),
            injury_adjustment=independent_inputs.get("injury_adjustment"),
            park_factor_adjustment=independent_inputs.get("park_factor_adjustment"),
            umpire_adjustment=independent_inputs.get("umpire_adjustment"),
            player_prop_projection=independent_inputs.get("player_prop_projection"),
            sharp_market_probability=independent_inputs.get("sharp_market_probability"),
            closing_line_projection=independent_inputs.get("closing_line_projection"),
            priced_rows=price_response.get("evaluation_ready_lines", []),
        )

        model_response = await calculate_model_probability(model_request)

        if not model_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": None,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to estimate probabilities: {model_response.get('detail', 'Unknown error')}"],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": model_response.get("error", "PROBABILITY_ESTIMATION_FAILED"),
                "detail": model_response.get("detail", "Failed to estimate model probabilities"),
                "step_failed": step,
            }

        model_results = model_response.get("results", [])
        probability_type = model_response.get("probability_type")
        if model_results:
            for result in model_results:
                if result.get("ok", False):
                    probability_type = result.get("probability_type", probability_type)
                    break

        if not model_results and probability_type != "market_derived":
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": probability_type,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": ["Model probabilities were generated but could not be matched to evaluation lines."],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": "model_probability_handoff_failed",
                "detail": "Model probabilities were generated but could not be matched to evaluation lines.",
                "step_failed": step,
            }

        model_probability_map = {}
        for result in model_results:
            if result.get("ok", False) and "row" in result:
                row = result["row"]
                match_key = (
                    row.get("sportsbook"),
                    row.get("market"),
                    row.get("selection"),
                    row.get("line"),
                    row.get("odds_american"),
                )
                model_probability_map[match_key] = result

        # Step 4: Evaluate lines using evaluateBettingLines logic
        step = "evaluate_lines"
        evaluation_ready_lines = price_response.get("evaluation_ready_lines", [])

        if not evaluation_ready_lines:
            return {
                "ok": True,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": model_response.get("probability_type", "unknown"),
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [{"reason": "No evaluation-ready lines available", "lines": []}],
                "warnings": ["No lines available for evaluation"],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": None,
                "detail": "Analysis completed but no lines available for evaluation",
                "step_failed": None,
            }

        valid_evaluation_lines = []
        validation_warnings = []

        for line in evaluation_ready_lines:
            sportsbook = line.get("sportsbook")
            market = line.get("market")
            selection = line.get("selection")
            odds_american = line.get("odds_american")

            if sportsbook is None or sportsbook == "unknown":
                validation_warnings.append("Skipped line because sportsbook was missing.")
                continue

            if odds_american is None:
                validation_warnings.append("Skipped line because odds_american was missing.")
                continue

            if market is None or selection is None:
                validation_warnings.append("Skipped line because market or selection was missing.")
                continue

            match_key = (
                sportsbook,
                market,
                selection,
                line.get("line"),
                odds_american,
            )

            model_result = model_probability_map.get(match_key)

            if probability_type == "market_derived":
                model_probability = (
                    line.get("no_vig_probability")
                    if line.get("no_vig_probability") is not None
                    else line.get("consensus_probability")
                    if line.get("consensus_probability") is not None
                    else line.get("implied_probability")
                )
            elif model_result:
                model_probability = model_result.get("final_probability")
            else:
                model_probability = None

            if (
                model_probability is None
                or model_probability <= 0
                or model_probability >= 1
            ):
                validation_warnings.append("Skipped line because model_probability was invalid for evaluation.")
                continue

            valid_line = {
                "sportsbook": sportsbook,
                "market": market,
                "selection": selection,
                "line": line.get("line"),
                "odds_american": odds_american,
                "model_probability": model_probability,
                "no_vig_probability": line.get("no_vig_probability"),
                "consensus_probability": line.get("consensus_probability"),
                "implied_probability": line.get("implied_probability"),
                "correlation_group": line.get("correlation_group"),
                "opening_odds_american": line.get("opening_odds_american"),
            }

            valid_evaluation_lines.append(valid_line)

        if not valid_evaluation_lines:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": model_response.get("probability_type", "unknown"),
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": validation_warnings,
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": "no_valid_evaluation_lines",
                "detail": "No valid sportsbook lines were available for evaluation.",
                "step_failed": "evaluate_lines",
            }

        evaluate_request = EvaluateLinesRequest(
            sport=payload.sport,
            event=f"{payload.league} - {payload.event_id}",
            bankroll=payload.bankroll,
            unit_size=payload.unit_size,
            risk_profile=payload.risk_profile,
            lines=valid_evaluation_lines,
            max_stake_pct=payload.max_stake_pct,
        )

        evaluate_response = await evaluate_lines(evaluate_request)

        if not evaluate_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": model_response.get("probability_type", "unknown"),
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to evaluate lines: {evaluate_response.get('detail', 'Unknown error')}"],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": evaluate_response.get("error", "LINE_EVALUATION_FAILED"),
                "detail": evaluate_response.get("detail", "Failed to evaluate betting lines"),
                "step_failed": step,
            }

        # Step 5: Process results and categorize bets
        evaluation_results = evaluate_response.get("results", [])
        confirmed_bets = []
        target_lines = []
        no_bets = []
        warnings = []
        registry_sport_key = payload.sport
        if not multi_sport_model_registry.is_supported_sport(registry_sport_key):
            registry_sport_key = payload.league
        sport_confirmed_bets_allowed = multi_sport_model_registry.confirmed_bets_allowed(registry_sport_key)
        sport_model_level = multi_sport_model_registry.classify_model_level(registry_sport_key)
        confirmed_bet_blocked_count = 0

        for result in evaluation_results:
            decision = result.get("decision")
            normalized_decision = decision.lower().strip() if isinstance(decision, str) else ""
            bet_like_decisions = {"bet", "strong_bet", "strong bet"}
            is_bet_like = normalized_decision in bet_like_decisions

            if probability_type in {"market_derived", "market_derived_only"} or not sport_confirmed_bets_allowed:
                if is_bet_like:
                    result["decision"] = (
                        "target_market_derived"
                        if probability_type in {"market_derived", "market_derived_only"}
                        else "target_registry_blocked"
                    )
                    result["market_derived_only"] = probability_type in {"market_derived", "market_derived_only"}
                    result["confirmed_bets_allowed"] = False
                    result["model_level"] = sport_model_level
                    target_lines.append(result)
                    confirmed_bet_blocked_count += 1
                elif decision in ["TARGET", "WATCH"]:
                    target_lines.append(result)
                else:
                    no_bets.append(result)
            else:
                if decision == "BET":
                    confirmed_bets.append(result)
                elif decision in ["TARGET", "WATCH"]:
                    target_lines.append(result)
                else:
                    no_bets.append(result)

        if probability_type == "market_derived":
            warnings.append("Using market-derived probability only; no independent projection data was provided.")
            warnings.append("Line evaluated with market-derived probability only; not a confirmed betting recommendation.")
        elif probability_type == "market_derived_only":
            warnings.append("Using market-derived probability only; no independent projection data was provided.")
            warnings.append("Line evaluated with market-derived probability only; not a confirmed betting recommendation.")

        if confirmed_bet_blocked_count and not sport_confirmed_bets_allowed:
            warnings.append(
                "Confirmed bets are disabled for this sport in the model registry until independent projection inputs are connected."
            )

        if model_results:
            for result in model_results:
                if result.get("ok", False):
                    missing_inputs = result.get("missing_inputs", [])
                    if missing_inputs:
                        warnings.append(f"Missing model inputs: {', '.join(missing_inputs)}")
                    break

        warnings.extend(validation_warnings)

        model_limitations = []
        missing_inputs = []
        active_inputs = []
        if model_results:
            for result in model_results:
                if result.get("ok", False):
                    model_limitations = result.get("model_limitations", [])
                    missing_inputs = result.get("missing_inputs", [])
                    active_inputs = result.get("active_inputs", [])
                    break

        log_ready_rows = []
        for result in evaluation_results:
            log_row = {
                "timestamp": utc_now(),
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "market": result.get("market"),
                "selection": result.get("selection"),
                "line": result.get("line"),
                "odds_american": result.get("odds_american"),
                "decision": result.get("decision"),
                "stake": result.get("stake"),
                "expected_value": result.get("expected_value"),
                "probability_type": probability_type,
                "final_probability": result.get("model_probability"),
                "risk_profile": payload.risk_profile,
                "bankroll": payload.bankroll,
                "unit_size": payload.unit_size,
            }
            log_ready_rows.append(log_row)

        return {
            "ok": True,
            "endpoint": endpoint_id,
            "sport": payload.sport,
            "league": payload.league,
            "event_id": payload.event_id,
            "markets_requested": markets_requested,
            "probability_type": probability_type,
            "confirmed_bets": confirmed_bets,
            "target_lines": target_lines,
            "no_bets": no_bets,
            "warnings": warnings,
            "model_limitations": model_limitations,
            "missing_inputs": missing_inputs,
            "active_inputs": active_inputs,
            "market_summary": price_response.get("market_summary", []),
            "evaluation_results": evaluation_results,
            "log_ready_rows": log_ready_rows,
            "error": None,
            "detail": None,
            "step_failed": None,
        }

    except Exception as exc:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "sport": payload.sport,
            "league": payload.league,
            "event_id": payload.event_id,
            "markets_requested": markets_requested,
            "probability_type": None,
            "confirmed_bets": [],
            "target_lines": [],
            "no_bets": [],
            "warnings": [f"Unexpected error during analysis: {str(exc)}"],
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": [],
            "market_summary": [],
            "evaluation_results": [],
            "log_ready_rows": [],
            "error": "UNEXPECTED_ERROR",
            "detail": str(exc),
            "step_failed": "unknown",
        }
# END ANALYZE_BETTING_EVENT_PIPELINE_SERVICE
