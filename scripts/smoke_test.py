import os
import sys

import requests

BASE_URL = os.getenv(
    "BASE_URL",
    "https://betting-stock-api-code-integration.onrender.com"
).rstrip("/")
ACTION_API_KEY = os.getenv("ACTION_API_KEY")
EXPECTED_SERVER = "https://betting-stock-api-code-integration.onrender.com"
TIMEOUT = 8


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"{status} {name}{': ' + detail if detail else ''}")
    return passed


def get(path, protected=False):
    headers = {}
    if protected and ACTION_API_KEY:
        headers["x-action-key"] = ACTION_API_KEY

    return requests.get(f"{BASE_URL}{path}", headers=headers, timeout=TIMEOUT)


def main():
    results = []

    root = get("/")
    results.append(check("root returns 200", root.status_code == 200, str(root.status_code)))

    ping = get("/ping")
    ping_json = ping.json() if ping.headers.get("content-type", "").startswith("application/json") else {}
    results.append(check("ping returns ok true", ping.status_code == 200 and ping_json == {"ok": True}, str(ping_json)))

    health = get("/health")
    health_json = health.json() if health.headers.get("content-type", "").startswith("application/json") else {}
    results.append(check("health returns status ok", health.status_code == 200 and health_json.get("status") == "ok", str(health_json)))

    openapi = get("/openapi.json")
    openapi_json = openapi.json()
    servers = openapi_json.get("servers", [])
    operation_ids = {
        operation.get("operationId")
        for path_item in openapi_json.get("paths", {}).values()
        for operation in path_item.values()
        if isinstance(operation, dict)
    }
    openapi_text = openapi.text.lower()

    results.append(check("openapi has servers", bool(servers), str(servers)))
    results.append(check("openapi server equals Render URL", any(server.get("url") == EXPECTED_SERVER for server in servers), str(servers)))
    results.append(check("openapi has no x-action-key", "x-action-key" not in openapi_text))
    results.append(check("openapi has ping operationId", "ping" in operation_ids))
    results.append(check("openapi has healthCheck operationId", "healthCheck" in operation_ids))

    if ACTION_API_KEY:
        for path in ("/odds/events", "/odds/first-event", "/bets/summary", "/debug/config"):
            response = get(path, protected=True)
            results.append(check(f"{path} protected call returns JSON", response.headers.get("content-type", "").startswith("application/json"), str(response.status_code)))
    else:
        print("SKIP protected endpoint checks: ACTION_API_KEY is not set")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
