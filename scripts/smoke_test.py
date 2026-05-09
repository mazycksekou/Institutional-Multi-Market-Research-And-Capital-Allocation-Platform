import os
import sys

import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ACTION_API_KEY = os.getenv("ACTION_API_KEY", "")
EXPECTED_SERVER = "https://betting-stock-api-code-integration.onrender.com"
TIMEOUT = 10


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"{status} {name}{': ' + detail if detail else ''}")
    return passed


def headers():
    if ACTION_API_KEY:
        return {"X-API-Key": ACTION_API_KEY}
    return {}


def get(path):
    return requests.get(f"{BASE_URL}{path}", headers=headers(), timeout=TIMEOUT)


def post(path, payload):
    return requests.post(f"{BASE_URL}{path}", headers=headers(), json=payload, timeout=TIMEOUT)


def main():
    results = []

    ping = requests.get(f"{BASE_URL}/ping", timeout=TIMEOUT)
    results.append(check("ping returns ok true", ping.status_code == 200 and ping.json() == {"ok": True}))

    health = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    results.append(check("health returns status ok", health.status_code == 200 and health.json().get("status") == "ok"))

    config = get("/api/debug/config")
    results.append(check("debug config returns JSON", config.status_code == 200, str(config.status_code)))

    mlb = get("/api/betting/events/active?league=MLB")
    mlb_json = mlb.json()
    results.append(check("MLB resolves to baseball_mlb", mlb_json.get("sport_key") == "baseball_mlb", str(mlb_json)))
    results.append(check("MLB league label preserved", mlb_json.get("league") == "MLB", str(mlb_json)))

    missing_sport = get("/api/betting/first-event-odds")
    results.append(check("first event odds requires sport", missing_sport.json().get("error_type") == "SPORT_REQUIRED"))

    bet = post("/quant/bet-analysis", {
        "sport": "UFC",
        "event": "Fighter A vs Fighter B",
        "pick": "Fighter A moneyline",
        "market": "moneyline",
        "odds": 150,
        "true_probability_pct": 45,
        "stake": 100,
        "bankroll": 1000,
        "correlation_group": "ufc-main-card",
        "current_group_exposure": 0,
    }).json()
    results.append(check("bet quant implied probability", bet.get("analysis", {}).get("implied_probability_pct") == 40.0, str(bet)))

    stock = post("/quant/stock-analysis", {
        "ticker": "NVDA",
        "current_price": 900,
        "expected_stock_return_pct": 18,
        "beta": 1.7,
        "risk_free_rate_pct": 4.5,
        "expected_market_return_pct": 10,
        "planned_position_size": 500,
        "portfolio_value": 10000,
    }).json()
    results.append(check("stock quant CAPM", stock.get("analysis", {}).get("capm_required_return_pct") == 13.85, str(stock)))

    openapi = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT).json()
    servers = openapi.get("servers", [])
    operation_ids = {
        operation.get("operationId")
        for path_item in openapi.get("paths", {}).values()
        for operation in path_item.values()
        if isinstance(operation, dict)
    }
    required_operations = {
        "healthCheck",
        "ping",
        "getDebugConfig",
        "getStockData",
        "getWatchlistData",
        "getActiveBettingEvents",
        "getEventOdds",
        "getFirstEventOdds",
        "analyzeStocksAndOdds",
        "logBet",
        "getBetSummary",
        "quantBetAnalysis",
        "quantStockAnalysis",
    }
    results.append(check("openapi server equals Render URL", any(server.get("url") == EXPECTED_SERVER for server in servers)))
    results.append(check("openapi has required operation IDs", required_operations.issubset(operation_ids), str(required_operations - operation_ids)))

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
