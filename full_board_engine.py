from __future__ import annotations

from typing import Any


FULL_BOARD_EMPTY = {
    "confirmed_bets": [],
    "target_lines": [],
    "target_props": [],
    "target_alt_lines": [],
    "no_bets": [],
    "best_correlated_parlay": None,
    "value_ranking": [],
    "risk_ranking": [],
    "missing_inputs": [],
    "manual_review_required": [],
    "logbook_ready_rows": [],
}


def build_full_board_preview(ticket: dict[str, Any], model_analysis: dict[str, Any], provider_enrichment: dict[str, Any]) -> dict[str, Any]:
    board = dict(FULL_BOARD_EMPTY)
    model_board = model_analysis.get("full_board_preview") if isinstance(model_analysis, dict) else None
    if isinstance(model_board, dict):
        board.update({k: model_board.get(k, v) for k, v in board.items()})

    visible_markets = ticket.get("visible_markets") or []
    visible_props = ticket.get("visible_props") or []
    visible_alt_lines = ticket.get("visible_alt_lines") or []
    only_visible = not any(
        block.get("provider_status") == "available"
        for block in provider_enrichment.values()
        if isinstance(block, dict)
    )
    if only_visible:
        board["manual_review_required"] = list(board["manual_review_required"]) + [
            "Only visible markets were analyzed. Additional markets require provider enrichment."
        ]

    if visible_markets:
        board["target_lines"] = board["target_lines"] or [{"market": m, "status": "visible_only"} for m in visible_markets]
    if visible_props:
        board["target_props"] = [{"market": p, "status": "visible_only"} for p in visible_props]
    if visible_alt_lines:
        board["target_alt_lines"] = [{"market": a, "status": "visible_only"} for a in visible_alt_lines]

    board["confirmed_bets"] = list(model_analysis.get("confirmed_bets") or [])
    board["no_bets"] = board["no_bets"] or [{"reason": "confirmed bet rules not satisfied"}]
    return board
