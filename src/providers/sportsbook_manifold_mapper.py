from __future__ import annotations

from typing import Any

from src.market_intelligence.market_state_manifold import map_market_state


def map_sportsbook_market(
    item: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    row = dict(item or {})
    row.setdefault("asset_type", "sportsbook")
    return map_market_state(
        row,
        registry=registry,
        calibration_report=calibration_report,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )


def map_sportsbook_full_board(
    items: list[dict[str, Any]] | None,
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    rows = [row for row in (items or []) if isinstance(row, dict)]
    mapped = [
        map_sportsbook_market(
            row,
            registry=registry,
            calibration_report=calibration_report,
            historical_records=historical_records,
            base_data_dir=base_data_dir,
        )
        for row in rows
    ]
    script_counts: dict[str, int] = {}
    no_bet = 0
    stale = 0
    correlated = 0
    for row in mapped:
        name = str(row.get("manifold_cluster_name") or "unknown")
        script_counts[name] = script_counts.get(name, 0) + 1
        if row.get("recommended_action") == "NO_BET" or float(row.get("no_bet_trap_score") or 0.0) >= 65.0:
            no_bet += 1
        if name == "stale_prop_line":
            stale += 1
        if name == "correlated_sgp_candidate":
            correlated += 1
    return {
        "ok": True,
        "status": "sportsbook_manifold_mapped",
        "items_mapped": len(mapped),
        "game_script_cluster_counts": script_counts,
        "markets_fit_game_script_count": len([row for row in mapped if row.get("recommended_action") in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}]),
        "stale_line_count": stale,
        "correlated_parlay_candidate_count": correlated,
        "no_bet_trap_count": no_bet,
        "items": mapped,
        "execution_allowed": False,
        "provider_write": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }
