from typing import Any

from fastapi import Body, Depends, HTTPException, Query


def register_governance_routes(
    app: Any,
    *,
    build_model_validation_report_dep: Any,
    compact_governance_inventory_dep: Any,
    compact_governance_report_dep: Any,
    compact_health_response_dep: Any,
    compact_validation_response_dep: Any,
    generate_governance_report_dep: Any,
    get_governance_health_dep: Any,
    get_model_inventory_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register governance routes.

    Canonical owner: src/api/governance_routes.py
    """
    build_model_validation_report = build_model_validation_report_dep
    compact_governance_inventory = compact_governance_inventory_dep
    compact_governance_report = compact_governance_report_dep
    compact_health_response = compact_health_response_dep
    compact_validation_response = compact_validation_response_dep
    generate_governance_report = generate_governance_report_dep
    get_governance_health = get_governance_health_dep
    get_model_inventory = get_model_inventory_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.get("/api/governance/health", operation_id="getGovernanceHealth")
    async def get_governance_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = {"ok": True, **get_governance_health()}
        compact = compact_health_response(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/governance/inventory", operation_id="getGovernanceInventory")
    async def get_governance_inventory_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = {"ok": True, "inventory": get_model_inventory()}
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_governance_inventory(payload, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/governance/report", operation_id="getGovernanceReport")
    async def get_governance_report_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        payload = {"ok": True, **generate_governance_report()}
        compact = compact_governance_report(payload)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
        return compact


    @app.post("/api/governance/validate", operation_id="validateGovernanceDryRun")
    async def validate_governance_endpoint(payload: dict[str, Any], verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        model_id = str(payload.get("model_id") or "unknown_model")
        activation_tier = str(payload.get("activation_tier") or "research_only")
        result = {
            "ok": True,
            "dry_run": True,
            "validation": build_model_validation_report(model_id=model_id, activation_tier=activation_tier),
        }
        compact = compact_validation_response(result)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact
