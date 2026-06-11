from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, HTTPException, Query

from src.api.schemas.betting_actions import (
    ActionBetLogRequest,
    ActionBetResultRequest,
    AnalyzeEventRequest,
    EvaluateLinesRequest,
    ModelProbabilityRequest,
    PriceEventRequest,
    ScreenshotAnalysisRequest,
    ScreenshotAnalysisResponse,
    SportAnalysisRequest,
    SportAnalysisResponse,
    SportsModelRegistryResponse,
)


def register_betting_action_routes(
    app: Any,
    *,
    require_action_key: Any,
    provider_router: Any,
    action_betting_service: Any,
    bet_log_dep: Any,
    bet_decision_engine_dep: Any,
    market_pricing_dep: Any,
    model_probability_dep: Any,
    multi_sport_model_registry_dep: Any,
    screenshot_intake_dep: Any,
    default_markets: str,
    default_bookmakers: str,
    utc_now_fn: Any,
) -> None:
    """
    Register raw betting and Custom GPT Action betting routes.

    Canonical owner: src/api/betting_action_routes.py
    """
    PROVIDER_ROUTER = provider_router
    ACTION_BETTING_SERVICE = action_betting_service
    DEFAULT_MARKETS = default_markets
    DEFAULT_BOOKMAKERS = default_bookmakers
    bet_log = bet_log_dep
    bet_decision_engine = bet_decision_engine_dep
    market_pricing = market_pricing_dep
    model_probability = model_probability_dep
    multi_sport_model_registry = multi_sport_model_registry_dep
    screenshot_intake = screenshot_intake_dep
    utc_now = utc_now_fn
    @app.get("/api/betting/events/active", operation_id="getActiveBettingEventsRaw", dependencies=[Depends(require_action_key)])
    async def get_active_betting_events(
        sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
        league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
        provider: Optional[str] = None,
        team: Optional[str] = None,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None,
        date: Optional[str] = Query(default=None),
    ):
        return await PROVIDER_ROUTER.get_active_events(
            provider,
            sport,
            league,
            team=team,
            home_team=home_team,
            away_team=away_team,
            date=date,
        )
    
    
    @app.get("/api/actions/betting/events/active", operation_id="getActiveBettingEvents", dependencies=[Depends(require_action_key)], summary="Get Active Betting Events", description="Retrieve active betting events for a specific league and provider with optional filtering.")
    async def action_get_active_betting_events(
        league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
        provider: Optional[str] = Query(None, description="Odds provider to use (defaults to configured provider)"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of events to return"),
    ):
        return await ACTION_BETTING_SERVICE.fetch_active_events_envelope(league, provider, limit)
    
    
    @app.get(
        "/api/actions/models/sports-registry",
        operation_id="getSportsModelRegistry",
        dependencies=[Depends(require_action_key)],
        response_model=SportsModelRegistryResponse,
        summary="Get Sports Model Registry",
        description=(
            "Return the multi-sport model registry, including model maturity, required independent inputs, "
            "provider needs, market support, logging requirements, and confirmed-bet governance eligibility."
        ),
    )
    async def action_get_sports_model_registry():
        return multi_sport_model_registry.get_sports_model_registry_response()
    
    
    @app.post(
        "/api/actions/models/sport-analysis",
        operation_id="analyzeSportModel",
        dependencies=[Depends(require_action_key)],
        response_model=SportAnalysisResponse,
        summary="Analyze Sport Model",
        description=(
            "Return the registered sport-model architecture foundation for a sport and market. "
            "This endpoint does not connect live providers and cannot create confirmed bets without required inputs, "
            "backtest proof, risk approval, and clear no-bet flags."
        ),
    )
    async def action_analyze_sport_model(payload: SportAnalysisRequest):
        try:
            return multi_sport_model_registry.analyze_sport_model(payload.model_dump(exclude_none=True))
        except Exception as exc:
            sport = None
            try:
                sport = payload.model_dump(exclude_none=True).get("sport")
            except Exception:
                sport = None
            return multi_sport_model_registry.sport_analysis_failed_response(
                sport=sport,
                detail=f"Sport analysis failed safely: {type(exc).__name__}",
            )
    
    
    @app.post(
        "/api/actions/ticket/screenshot-analysis",
        operation_id="analyzeTicketScreenshot",
        dependencies=[Depends(require_action_key)],
        response_model=ScreenshotAnalysisResponse,
        summary="Analyze Ticket Screenshot",
        description=(
            "Analyze sportsbook ticket fields parsed from a screenshot or OCR text. "
            "OCR is optional; ChatGPT may send structured parsed fields directly."
        ),
    )
    async def action_analyze_ticket_screenshot(payload: ScreenshotAnalysisRequest):
        try:
            return screenshot_intake.analyze_screenshot_ticket(payload.model_dump(exclude_none=True))
        except Exception as exc:
            return {
                "ok": False,
                "endpoint": "ticketScreenshotAnalysis",
                "partial_model_mode": True,
                "parsed_ticket": {},
                "provider_enrichment": {},
                "model_analysis": {},
                "full_board_preview": {
                    "confirmed_bets": [],
                    "target_lines": [],
                    "target_props": [],
                    "target_alt_lines": [],
                    "no_bets": [{"reason": "screenshot_analysis_failed_safely"}],
                    "best_correlated_parlay": None,
                    "value_ranking": [],
                    "risk_ranking": [],
                    "missing_inputs": [],
                    "manual_review_required": ["Manual review required after handled error."],
                    "logbook_ready_rows": [],
                },
                "missing_inputs": ["screenshot_analysis_failed"],
                "no_bets": [{"reason": "screenshot_analysis_failed_safely", "detail": type(exc).__name__}],
                "confirmed_bets": [],
                "suggested_stake": 0,
                "implied_probability": None,
                "logbook_ready_rows": [],
                "error": "screenshot_analysis_failed",
                "detail": f"Screenshot analysis failed safely: {type(exc).__name__}",
            }
    
    
    @app.post(
        "/api/actions/betting/log-bet",
        operation_id="logBet",
        dependencies=[Depends(require_action_key)],
        summary="Log Bet",
        description="Create and append a Sharpsbook-style betting log entry.",
    )
    async def action_log_bet(payload: ActionBetLogRequest):
        entry = bet_log.create_bet_log_entry(payload.model_dump(exclude_none=True))
        bet_log.append_bet_log_entry(entry)
        return {"ok": True, "endpoint": "logBet", "bet": entry}
    
    
    @app.post(
        "/api/actions/betting/log-result",
        operation_id="logBetResult",
        dependencies=[Depends(require_action_key)],
        summary="Log Bet Result",
        description="Update an existing logged bet with its result and calculated profit/loss.",
    )
    async def action_log_bet_result(payload: ActionBetResultRequest):
        updated = bet_log.update_bet_result(
            bet_id=payload.bet_id,
            result=payload.result,
            closing_odds=payload.closing_odds,
        )
        if updated is None:
            return {
                "ok": False,
                "endpoint": "logBetResult",
                "error": "BET_NOT_FOUND",
                "detail": f"No bet log entry found for bet_id {payload.bet_id}.",
            }
        return {"ok": True, "endpoint": "logBetResult", "bet": updated}
    
    
    @app.get(
        "/api/actions/betting/logs",
        operation_id="getBetLogs",
        dependencies=[Depends(require_action_key)],
        summary="Get Bet Logs",
        description="Read Sharpsbook-style betting log entries.",
    )
    async def action_get_bet_logs(limit: int = Query(default=100, ge=1, le=1000)):
        entries = bet_log.read_bet_log_entries()
        return {
            "ok": True,
            "endpoint": "getBetLogs",
            "count": len(entries),
            "logs": entries[-limit:],
        }
    
    
    @app.get(
        "/api/actions/betting/performance-summary",
        operation_id="getPerformanceSummary",
        dependencies=[Depends(require_action_key)],
        summary="Get Performance Summary",
        description="Summarize betting performance, ROI, yield, CLV, and error counts.",
    )
    async def action_get_performance_summary():
        return {
            "ok": True,
            "endpoint": "getPerformanceSummary",
            "summary": bet_log.get_performance_summary(),
        }
    
    
    @app.get(
        "/api/actions/betting/bankroll-summary",
        operation_id="getBankrollSummary",
        dependencies=[Depends(require_action_key)],
        summary="Get Bankroll Summary",
        description="Summarize bankroll movement from logged bets.",
    )
    async def action_get_bankroll_summary():
        return {
            "ok": True,
            "endpoint": "getBankrollSummary",
            "summary": bet_log.get_bankroll_summary(),
        }
    
    
    @app.get(
        "/api/actions/betting/clv-report",
        operation_id="getCLVReport",
        dependencies=[Depends(require_action_key)],
        summary="Get CLV Report",
        description="Compare actual odds taken against closing odds when available.",
    )
    async def action_get_clv_report():
        return {
            "ok": True,
            "endpoint": "getCLVReport",
            "report": bet_log.get_clv_report(),
        }
    
    
    @app.get("/api/betting/events/{event_id}/odds", operation_id="getEventOddsRaw", dependencies=[Depends(require_action_key)])
    async def get_event_odds_endpoint(
        event_id: str,
        sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
        league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
        provider: Optional[str] = None,
        markets: str = DEFAULT_MARKETS,
        bookmakers: str = DEFAULT_BOOKMAKERS,
    ):
        return await PROVIDER_ROUTER.get_event_odds(
            provider,
            event_id,
            sport,
            league,
            markets=markets,
            bookmakers=bookmakers,
        )
    
    
    @app.get("/api/actions/betting/events/{event_id}/odds", operation_id="getEventOdds", dependencies=[Depends(require_action_key)], summary="Get Event Odds", description="Retrieve betting odds for a specific event across specified markets and bookmakers.")
    async def action_get_event_odds(
        event_id: str,
        league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
        provider: Optional[str] = Query(None, description="Odds provider to use (defaults to configured provider)"),
        markets: str = Query(default=DEFAULT_MARKETS, description="Comma-separated list of markets to retrieve"),
    ):
        return await ACTION_BETTING_SERVICE.fetch_event_odds_envelope(
            event_id,
            league,
            provider,
            markets,
            DEFAULT_BOOKMAKERS,
        )
    
    
    @app.get("/api/betting/first-event-odds", operation_id="getFirstEventOddsRaw", dependencies=[Depends(require_action_key)])
    async def get_first_event_odds(
        sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
        league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
        provider: Optional[str] = None,
        team: Optional[str] = None,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None,
        date: Optional[str] = Query(default=None),
        markets: str = DEFAULT_MARKETS,
        bookmakers: str = DEFAULT_BOOKMAKERS,
    ):
        return await PROVIDER_ROUTER.get_first_event_odds(
            provider,
            sport,
            league,
            team=team,
            home_team=home_team,
            away_team=away_team,
            date=date,
            markets=markets,
            bookmakers=bookmakers,
        )
    
    
    @app.get("/api/actions/betting/first-event-odds", operation_id="getFirstEventOdds", dependencies=[Depends(require_action_key)], summary="Get First Event Odds", description="Retrieve odds for the first available event in a league across specified markets and bookmakers.")
    async def action_get_first_event_odds(
        league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
        provider: Optional[str] = Query(None, description="Odds provider to use (defaults to configured provider)"),
        markets: str = Query(default=DEFAULT_MARKETS, description="Comma-separated list of markets to retrieve"),
    ):
        endpoint_id = "getFirstEventOdds"
        league_param = ACTION_BETTING_SERVICE.normalize_action_league_input(league)
        provider_used = (provider or "").strip() or None
    
        try:
            active = await ACTION_BETTING_SERVICE.fetch_active_events_envelope(league, provider, 1)
            if not active.get("ok"):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": str(active.get("league") or league_param),
                    "event": {},
                    "odds": {},
                    "error": str(active.get("error") or "ACTIVE_EVENTS_FAILED"),
                    "detail": str(active.get("detail") or "Could not load active events."),
                }
    
            events = active.get("events") or []
            if not events:
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": str(active.get("league") or league_param),
                    "event": {},
                    "odds": {},
                    "error": "NO_EVENTS",
                    "detail": "No active events found for this league.",
                }
    
            first = events[0] if isinstance(events[0], dict) else {}
            eid = first.get("provider_event_id") or first.get("event_id") or first.get("id")
            if not eid:
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": str(active.get("league") or league_param),
                    "event": first,
                    "odds": {},
                    "error": "NO_EVENT_ID",
                    "detail": "First event is missing an id field.",
                }
    
            odds_env = await ACTION_BETTING_SERVICE.fetch_event_odds_envelope(
                str(eid),
                league,
                provider_used,
                markets,
                DEFAULT_BOOKMAKERS,
            )
    
            odds_body = {
                "markets_requested": odds_env.get("markets_requested") or ACTION_BETTING_SERVICE.parse_markets_requested(markets),
                "markets": odds_env.get("markets") or [],
                "bookmakers": odds_env.get("bookmakers") or [],
            }
    
            if not odds_env.get("ok"):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": str(odds_env.get("league") or active.get("league") or league_param),
                    "event": first,
                    "odds": odds_body,
                    "error": str(odds_env.get("error") or "ODDS_FAILED"),
                    "detail": str(odds_env.get("detail") or "Odds request failed."),
                }
    
            return {
                "ok": True,
                "endpoint": endpoint_id,
                "league": str(odds_env.get("league") or active.get("league") or league_param),
                "event": first,
                "odds": odds_body,
                "error": None,
                "detail": None,
            }
        except HTTPException as exc:
            detail = exc.detail
            if not isinstance(detail, str):
                detail = "Request rejected."
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": league_param,
                "event": {},
                "odds": {},
                "error": "HTTP_ERROR",
                "detail": detail,
            }
        except Exception:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": league_param,
                "event": {},
                "odds": {},
                "error": "UNEXPECTED_ERROR",
                "detail": "First-event odds request failed.",
            }
    
    
    @app.post("/api/actions/betting/evaluate-lines", operation_id="evaluateBettingLines", dependencies=[Depends(require_action_key)], summary="Evaluate Betting Lines", description="Evaluate betting lines with stake recommendations based on bankroll, risk profile, and model probabilities.")
    async def action_evaluate_betting_lines(payload: EvaluateLinesRequest):
        try:
            out = bet_decision_engine.evaluate_lines_payload(payload.model_dump())
            ok = bool(out.get("ok", True))
            return {
                "ok": ok,
                "sport": out.get("sport"),
                "event": out.get("event"),
                "risk_profile": out.get("risk_profile"),
                "error": out.get("error"),
                "detail": out.get("detail"),
                "results": out.get("results") or [],
            }
        except Exception as exc:
            return {
                "ok": False,
                "sport": getattr(payload, "sport", None),
                "event": getattr(payload, "event", None),
                "risk_profile": getattr(payload, "risk_profile", None),
                "error": "REQUEST_ERROR",
                "detail": str(exc),
                "results": [],
            }
    
    
    @app.post("/api/actions/betting/price-event", operation_id="priceBettingEvent", dependencies=[Depends(require_action_key)], summary="Price Betting Event", description="Price a betting event with stake recommendations based on bankroll, risk profile, and optional model probabilities.")
    async def action_price_betting_event(payload: PriceEventRequest):
        endpoint_id = "priceBettingEvent"
        markets_requested = ACTION_BETTING_SERVICE.parse_markets_requested(payload.markets)
    
        try:
            # Fetch event odds using the same Action safe odds logic
            odds_response = await ACTION_BETTING_SERVICE.fetch_event_odds_envelope(
                event_id=payload.event_id,
                league=payload.league,
                provider=payload.provider,
                markets_csv=payload.markets,
                bookmakers_csv=DEFAULT_BOOKMAKERS,
            )
    
            if not odds_response.get("ok"):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "sport": payload.sport,
                    "league": payload.league,
                    "event_id": payload.event_id,
                    "markets_requested": markets_requested,
                    "market_summary": [],
                    "best_prices": [],
                    "evaluation_ready_lines": [],
                    "warnings": [],
                    "error": odds_response.get("error", "ODDS_FETCH_FAILED"),
                    "detail": odds_response.get("detail", "Failed to fetch event odds"),
                }
    
            # Extract flat odds from markets
            flat_odds = []
            for market_block in odds_response.get("markets", []):
                for line in market_block.get("lines", []):
                    flat_odds.append(line)
    
            if not flat_odds:
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "sport": payload.sport,
                    "league": payload.league,
                    "event_id": payload.event_id,
                    "markets_requested": markets_requested,
                    "market_summary": [],
                    "best_prices": [],
                    "evaluation_ready_lines": [],
                    "warnings": ["No odds data found for event"],
                    "error": "NO_ODDS_DATA",
                    "detail": "No odds data available for the requested event",
                }
    
            # Create evaluation-ready lines with optional model probabilities
            evaluation_lines = market_pricing.create_evaluation_ready_lines(
                flat_odds,
                payload.model_probabilities
            )
    
            # Create market summary
            market_summary = market_pricing.create_market_summary(evaluation_lines)
    
            # Extract best prices for the response
            best_prices = []
            for summary in market_summary:
                for selection in summary.get("selections", []):
                    best_prices.append({
                        "market": summary["market"],
                        "line": summary["line"],
                        "selection": selection["selection"],
                        "best_odds_american": selection["best_odds"],
                        "consensus_probability": selection["consensus_probability"],
                        "fair_odds_american": selection["fair_odds"]
                    })
    
            # Check for warnings
            warnings = []
            if not evaluation_lines:
                warnings.append("No evaluation-ready lines created")
    
            # Check for stale lines
            stale_count = sum(1 for line in evaluation_lines if line.get("stale_line_flag", False))
            if stale_count > 0:
                warnings.append(f"{stale_count} lines flagged as potentially stale")
    
            return {
                "ok": True,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "market_summary": market_summary,
                "best_prices": best_prices,
                "evaluation_ready_lines": evaluation_lines,
                "warnings": warnings,
                "error": None,
                "detail": None,
            }
    
        except Exception as exc:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "market_summary": [],
                "best_prices": [],
                "evaluation_ready_lines": [],
                "warnings": [],
                "error": "UNEXPECTED_ERROR",
                "detail": str(exc),
            }
    
    
    @app.post("/api/actions/betting/model-probability", operation_id="estimateModelProbability", dependencies=[Depends(require_action_key)], summary="Estimate Model Probability", description="Calculate blended probabilities with adjustments, confidence scoring, and transparency outputs for betting decisions.")
    async def action_calculate_model_probability(payload: ModelProbabilityRequest):
        endpoint_id = "estimateModelProbability"
    
        try:
            # If no top-level market_probability provided, try to infer from priced_rows
            if payload.market_probability is None:
                if not payload.priced_rows or len(payload.priced_rows) == 0:
                    return {
                        "ok": False,
                        "endpoint": endpoint_id,
                        "error": "missing_market_probability",
                        "detail": "market_probability was not provided and no priced rows were available",
                        "final_probability": None,
                        "probability_type": None,
                        "market_probability": None,
                        "active_inputs": [],
                        "missing_inputs": [],
                        "applied_adjustments": {},
                        "adjustment_cap_warnings": [],
                        "model_limitations": [],
                        "data_quality_score": None,
                        "confidence": None,
                        "confidence_grade": None,
                        "provider_status": {}
                    }
    
                # Process each priced row individually
                results = []
                for row in payload.priced_rows:
                    # Infer market probability from row with priority: no_vig -> consensus -> implied
                    market_prob = None
                    if "no_vig_probability" in row and row["no_vig_probability"] is not None:
                        market_prob = row["no_vig_probability"]
                    elif "consensus_probability" in row and row["consensus_probability"] is not None:
                        market_prob = row["consensus_probability"]
                    elif "implied_probability" in row and row["implied_probability"] is not None:
                        market_prob = row["implied_probability"]
    
                    if market_prob is None:
                        # Skip this row with warning
                        results.append({
                            "ok": False,
                            "row": row,
                            "error": "missing_probability_in_row",
                            "detail": "Row does not contain no_vig_probability, consensus_probability, or implied_probability"
                        })
                        continue
    
                    # Create independent inputs from request
                    inputs = model_probability.IndependentInputs(
                        projection_probability=payload.projection_probability,
                        pitcher_adjustment=payload.pitcher_adjustment,
                        weather_adjustment=payload.weather_adjustment,
                        lineup_adjustment=payload.lineup_adjustment,
                        bullpen_adjustment=payload.bullpen_adjustment,
                        injury_adjustment=payload.injury_adjustment,
                        park_factor_adjustment=payload.park_factor_adjustment,
                        umpire_adjustment=payload.umpire_adjustment,
                        player_prop_projection=payload.player_prop_projection,
                        sharp_market_probability=payload.sharp_market_probability,
                        closing_line_projection=payload.closing_line_projection,
                    )
    
                    # Create probability response for this row
                    response = model_probability.create_probability_response(
                        market_probability=market_prob,
                        inputs=inputs
                    )
                    response["row"] = row
                    results.append(response)
    
                return {
                    "ok": True,
                    "endpoint": endpoint_id,
                    "results": results,
                    "processed_rows": len(payload.priced_rows),
                    "successful_rows": len([r for r in results if r.get("ok", False)]),
                    "failed_rows": len([r for r in results if not r.get("ok", False)])
                }
    
            else:
                # Use provided market_probability (fallback behavior)
                inputs = model_probability.IndependentInputs(
                    projection_probability=payload.projection_probability,
                    pitcher_adjustment=payload.pitcher_adjustment,
                    weather_adjustment=payload.weather_adjustment,
                    lineup_adjustment=payload.lineup_adjustment,
                    bullpen_adjustment=payload.bullpen_adjustment,
                    injury_adjustment=payload.injury_adjustment,
                    park_factor_adjustment=payload.park_factor_adjustment,
                    umpire_adjustment=payload.umpire_adjustment,
                    player_prop_projection=payload.player_prop_projection,
                    sharp_market_probability=payload.sharp_market_probability,
                    closing_line_projection=payload.closing_line_projection,
                )
    
                # Create probability response
                response = model_probability.create_probability_response(
                    market_probability=payload.market_probability,
                    inputs=inputs
                )
    
                return response
    
        except Exception as exc:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "error": "UNEXPECTED_ERROR",
                "detail": str(exc),
                "final_probability": None,
                "probability_type": None,
                "market_probability": None,
                "active_inputs": [],
                "missing_inputs": [],
                "applied_adjustments": {},
                "adjustment_cap_warnings": [],
                "model_limitations": [],
                "data_quality_score": None,
                "confidence": None,
                "confidence_grade": None,
                "provider_status": {}
            }
    
    
    @app.post("/api/actions/betting/analyze-event", operation_id="analyzeBettingEvent", dependencies=[Depends(require_action_key)], summary="Analyze Betting Event", description="Complete betting analysis pipeline: fetch odds, price event, estimate probabilities, and evaluate lines.")
    async def action_analyze_betting_event(payload: AnalyzeEventRequest):
        endpoint_id = "analyzeBettingEvent"
        markets_requested = ACTION_BETTING_SERVICE.parse_markets_requested(payload.markets)
    
        try:
            # Step 1: Fetch odds using Action safe odds logic
            step = "fetch_odds"
            odds_response = await ACTION_BETTING_SERVICE.fetch_event_odds_envelope(
                event_id=payload.event_id,
                league=payload.league,
                provider=payload.provider,
                markets_csv=payload.markets,
                bookmakers_csv=DEFAULT_BOOKMAKERS,
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
                    "step_failed": step
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
                model_probabilities=None  # Will be set after model probability step
            )
    
            # Create a mock price response since we need model probabilities first
            price_response = await action_price_betting_event(price_request)
    
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
                    "step_failed": step
                }
    
            # Step 3: Estimate model probabilities
            step = "estimate_probabilities"
            model_request = ModelProbabilityRequest(
                market_probability=None,
                projection_probability=payload.independent_inputs.get("projection_probability") if payload.independent_inputs else None,
                pitcher_adjustment=payload.independent_inputs.get("pitcher_adjustment") if payload.independent_inputs else None,
                weather_adjustment=payload.independent_inputs.get("weather_adjustment") if payload.independent_inputs else None,
                lineup_adjustment=payload.independent_inputs.get("lineup_adjustment") if payload.independent_inputs else None,
                bullpen_adjustment=payload.independent_inputs.get("bullpen_adjustment") if payload.independent_inputs else None,
                injury_adjustment=payload.independent_inputs.get("injury_adjustment") if payload.independent_inputs else None,
                park_factor_adjustment=payload.independent_inputs.get("park_factor_adjustment") if payload.independent_inputs else None,
                umpire_adjustment=payload.independent_inputs.get("umpire_adjustment") if payload.independent_inputs else None,
                player_prop_projection=payload.independent_inputs.get("player_prop_projection") if payload.independent_inputs else None,
                sharp_market_probability=payload.independent_inputs.get("sharp_market_probability") if payload.independent_inputs else None,
                closing_line_projection=payload.independent_inputs.get("closing_line_projection") if payload.independent_inputs else None,
                priced_rows=price_response.get("evaluation_ready_lines", [])
            )
    
            model_response = await action_calculate_model_probability(model_request)
    
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
                    "step_failed": step
                }
    
            # Extract model probability results for matching
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
                    "step_failed": step
                }
    
            # Create a mapping key for matching model results to evaluation lines
            model_probability_map = {}
            for result in model_results:
                if result.get("ok", False) and "row" in result:
                    row = result["row"]
                    # Create matching key using sportsbook, market, selection, line, odds_american
                    match_key = (
                        row.get("sportsbook"),
                        row.get("market"),
                        row.get("selection"),
                        row.get("line"),
                        row.get("odds_american")
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
                    "step_failed": None
                }
    
            # Filter and validate evaluation_ready_lines before passing to evaluateBettingLines
            valid_evaluation_lines = []
            validation_warnings = []
    
            for line in evaluation_ready_lines:
                # Check required fields
                sportsbook = line.get("sportsbook")
                market = line.get("market")
                selection = line.get("selection")
                odds_american = line.get("odds_american")
    
                # Skip rows with missing required fields
                if sportsbook is None or sportsbook == "unknown":
                    validation_warnings.append("Skipped line because sportsbook was missing.")
                    continue
    
                if odds_american is None:
                    validation_warnings.append("Skipped line because odds_american was missing.")
                    continue
    
                if market is None or selection is None:
                    validation_warnings.append("Skipped line because market or selection was missing.")
                    continue
    
                # Create matching key for this evaluation line
                match_key = (
                    sportsbook,
                    market,
                    selection,
                    line.get("line"),
                    odds_american
                )
    
                # Find matching model probability result
                model_result = model_probability_map.get(match_key)
    
                # Determine model_probability based on probability type and line data.
                # Market-derived analysis must use the probability from this same line.
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
    
                # Validate model_probability
                if (
                    model_probability is None
                    or model_probability <= 0
                    or model_probability >= 1
                ):
                    validation_warnings.append("Skipped line because model_probability was invalid for evaluation.")
                    continue
    
                # Create valid evaluation line with matched model probability
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
                    "opening_odds_american": line.get("opening_odds_american")
                }
    
                valid_evaluation_lines.append(valid_line)
    
            # If no valid lines, return error response
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
                    "step_failed": "evaluate_lines"
                }
    
            evaluate_request = EvaluateLinesRequest(
                sport=payload.sport,
                event=f"{payload.league} - {payload.event_id}",
                bankroll=payload.bankroll,
                unit_size=payload.unit_size,
                risk_profile=payload.risk_profile,
                lines=valid_evaluation_lines,
                max_stake_pct=payload.max_stake_pct
            )
    
            evaluate_response = await action_evaluate_betting_lines(evaluate_request)
    
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
                    "step_failed": step
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
    
                # Market-derived or registry-blocked sports cannot produce confirmed bets.
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
    
            # Add warnings for missing inputs
            if model_results:
                # Get missing inputs from first successful model result
                for result in model_results:
                    if result.get("ok", False):
                        missing_inputs = result.get("missing_inputs", [])
                        if missing_inputs:
                            warnings.append(f"Missing model inputs: {', '.join(missing_inputs)}")
                        break
    
            # Add validation warnings
            warnings.extend(validation_warnings)
    
            # Get model data from first successful result
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
    
            # Create log-ready rows
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
                    "unit_size": payload.unit_size
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
                "step_failed": None
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
                "step_failed": "unknown"
            }
