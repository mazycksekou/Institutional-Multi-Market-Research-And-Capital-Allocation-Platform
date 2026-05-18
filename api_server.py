from main import app, custom_openapi

app.openapi = custom_openapi


def _verify_runtime_routes() -> None:
    required_paths = {
        "/api/betting/events/active",
        "/api/actions/betting/events/active",
        "/api/actions/betting/events/{event_id}/odds",
        "/api/actions/betting/first-event-odds",
        "/api/actions/betting/evaluate-lines",
        "/api/actions/betting/price-event",
        "/api/actions/betting/model-probability",
        "/api/actions/betting/analyze-event",
        "/api/actions/betting/log-bet",
        "/api/actions/betting/log-result",
        "/api/actions/betting/logs",
        "/api/actions/betting/performance-summary",
        "/api/actions/betting/bankroll-summary",
        "/api/actions/betting/clv-report",
        "/api/actions/models/sports-registry",
        "/api/actions/models/sport-analysis",
        "/api/actions/ticket/screenshot-analysis",
        "/quant/market-pricing",
        "/quant/bet-analysis",
        "/quant/stock-analysis",
        "/api/betting/events/{event_id}/odds",
        "/api/betting/first-event-odds",
    }
    route_paths = {route.path for route in app.routes}
    missing_routes = sorted(required_paths - route_paths)
    if missing_routes:
        raise RuntimeError(f"api_server:app is missing runtime routes: {missing_routes}")

    schema_paths = set(app.openapi().get("paths", {}))
    missing_schema_paths = sorted(required_paths - schema_paths)
    if missing_schema_paths:
        raise RuntimeError(f"api_server:app OpenAPI schema is missing routes: {missing_schema_paths}")


_verify_runtime_routes()
