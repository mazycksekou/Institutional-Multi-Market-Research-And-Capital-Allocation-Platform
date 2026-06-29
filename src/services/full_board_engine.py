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


def _identity(value: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(value.get("sport") or value.get("sport_key") or "").strip().lower(),
        str(value.get("event") or value.get("event_id") or "").strip().lower(),
        str(value.get("market") or "").strip().lower(),
        str(value.get("selection") or "").strip().lower(),
    )


def _same_market_selection(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_identity = _identity(left)
    right_identity = _identity(right)
    return bool(all(left_identity) and left_identity == right_identity)


def _remove_confirmed_selection_no_bets(
    no_bets: list[dict[str, Any]],
    confirmed_bets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not confirmed_bets:
        return no_bets
    filtered = []
    for no_bet in no_bets:
        if no_bet.get("reason") == "confirmed bet rules not satisfied":
            continue
        if any(_same_market_selection(no_bet, confirmed) for confirmed in confirmed_bets):
            continue
        filtered.append(no_bet)
    return filtered


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
        existing_review = board["manual_review_required"]
        if existing_review is False:
            existing_review = []
        board["manual_review_required"] = list(existing_review or []) + [
            "Only visible markets were analyzed. Additional markets require provider enrichment."
        ]

    if visible_markets:
        board["target_lines"] = board["target_lines"] or [{"market": m, "status": "visible_only"} for m in visible_markets]
    if visible_props:
        board["target_props"] = [{"market": p, "status": "visible_only"} for p in visible_props]
    if visible_alt_lines:
        board["target_alt_lines"] = [{"market": a, "status": "visible_only"} for a in visible_alt_lines]

    board["confirmed_bets"] = list(model_analysis.get("confirmed_bets") or [])
    board["no_bets"] = _remove_confirmed_selection_no_bets(list(board["no_bets"] or []), board["confirmed_bets"])
    if not board["no_bets"] and not board["confirmed_bets"]:
        board["no_bets"] = [{"reason": "confirmed bet rules not satisfied"}]
    return board
