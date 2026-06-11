from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, File, Form, HTTPException, Header, Path, Query, Request, Response, UploadFile

from src.api.schemas.automation import (
    AutomationCrossAssetManifoldReviewRequest,
    AutomationManifoldMapRequest,
)

def register_automation_manifold_routes(
    app: Any,
    *,
    automation_scheduler_dep: Any,
    compact_manifold_map_response_dep: Any,
    compact_manifold_review_response_dep: Any,
    redact_and_limit_payload_dep: Any,
) -> None:
    """
    Register automation manifold analysis routes.

    Canonical owner: src/api/automation_manifold_routes.py
    """
    automation_scheduler = automation_scheduler_dep
    compact_manifold_map_response = compact_manifold_map_response_dep
    compact_manifold_review_response = compact_manifold_review_response_dep
    redact_and_limit_payload = redact_and_limit_payload_dep

    @app.post("/api/automation/manifold-map", operation_id="mapAutomationManifoldState")
    async def automation_manifold_map_endpoint(payload: AutomationManifoldMapRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        result = automation_scheduler.map_automation_manifold_item(
            payload.item,
            historical_records=payload.historical_records or None,
        )
        compact = compact_manifold_map_response(result)
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact


    @app.get("/api/automation/manifold-clusters", operation_id="getAutomationManifoldClusters")
    async def automation_manifold_clusters_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=25)):
        cap = min(max(int(limit), 1), 100 if verbose else 25)
        result = automation_scheduler.get_automation_manifold_clusters(limit=cap)
        if verbose or include_debug:
            result["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return result


    @app.get("/api/automation/manifold-calibration", operation_id="getAutomationManifoldCalibration")
    async def automation_manifold_calibration_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=25)):
        cap = min(max(int(limit), 1), 100 if verbose else 25)
        result = automation_scheduler.get_automation_manifold_calibration(limit=cap)
        if verbose or include_debug:
            result["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return result


    @app.get("/api/automation/manifold-no-bet-traps", operation_id="getAutomationManifoldNoBetTraps")
    async def automation_manifold_no_bet_traps_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=25)):
        cap = min(max(int(limit), 1), 100 if verbose else 25)
        result = automation_scheduler.get_automation_manifold_no_bet_traps(limit=cap)
        if verbose or include_debug:
            result["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return result


    @app.post("/api/automation/cross-asset-manifold-review", operation_id="reviewAutomationCrossAssetManifold")
    async def automation_cross_asset_manifold_review_endpoint(payload: AutomationCrossAssetManifoldReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="cross-asset manifold review only supports dry_run=true")
        result = automation_scheduler.run_automation_cross_asset_manifold_review(
            payload.items,
            historical_records=payload.historical_records or None,
            persist=bool(payload.persist),
            max_items=payload.max_items,
        )
        cap = min(max(int(limit), 1), 100 if verbose else 10)
        compact = compact_manifold_review_response(result, limit=cap)
        if verbose or include_debug:
            compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
        return compact
