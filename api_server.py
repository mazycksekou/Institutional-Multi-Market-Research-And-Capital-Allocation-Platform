from main import app, custom_openapi

app.openapi = custom_openapi


def _verify_runtime_routes() -> None:
    required_paths = {
        "/api/betting/events/active",
        "/api/actions/betting/events/active",
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
