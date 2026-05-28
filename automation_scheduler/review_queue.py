from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cadence_controller import choose_next_check_seconds
from .market_clock import apply_score_decay, is_market_closed, is_stale, seconds_since
from .opportunity_scoring import classify_opportunity
from .scheduler_config import SCHEMA_VERSION, safe_run_id, utc_now_iso


def _queue_path(config: dict[str, Any]) -> Path:
    path = Path(config["paths"]["review_queue"]) / "review_queue.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_review_queue(config: dict[str, Any]) -> list[dict[str, Any]]:
    path = _queue_path(config)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_review_queue(config: dict[str, Any], items: list[dict[str, Any]]) -> None:
    path = _queue_path(config)
    path.write_text(json.dumps(items, indent=2, sort_keys=True), encoding="utf-8")


def _review_item_id(candidate: dict[str, Any]) -> str:
    parts = [
        str(candidate.get("source") or "unknown"),
        str(candidate.get("market_type") or "unknown"),
        str(candidate.get("sport_or_symbol") or "unknown"),
        str(candidate.get("market") or "unknown"),
        str(candidate.get("selection") or "unknown"),
    ]
    return safe_run_id("review_item", "|".join(parts))


def build_review_item(candidate: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    thresholds = config["score_thresholds"]
    opportunity_score = float(candidate.get("opportunity_score", 0))
    if opportunity_score < float(thresholds["ignore_below"]):
        return None

    cadence = choose_next_check_seconds(
        market_type=str(candidate.get("market_type") or "news_events"),
        opportunity_score=opportunity_score,
        provider_name=str(candidate.get("provider") or "news_provider"),
        config=config,
        low_liquidity=bool(candidate.get("low_liquidity")),
        market_closed=False,
    )
    now = utc_now_iso()
    recommended_action = classify_opportunity(opportunity_score, thresholds)
    return {
        "schema_version": SCHEMA_VERSION,
        "id": _review_item_id(candidate),
        "created_at": str(candidate.get("created_at") or now),
        "updated_at": now,
        "source": candidate.get("source", "scheduler"),
        "market_type": candidate.get("market_type", "unknown"),
        "sport_or_symbol": candidate.get("sport_or_symbol", "unknown"),
        "market": candidate.get("market", "unknown"),
        "selection": candidate.get("selection", "unknown"),
        "odds_or_price": candidate.get("odds_or_price"),
        "candidate_type": candidate.get("candidate_type"),
        "books_compared": candidate.get("books_compared"),
        "best_book": candidate.get("best_book"),
        "best_line": candidate.get("best_line"),
        "best_odds": candidate.get("best_odds"),
        "model_probability": candidate.get("model_probability"),
        "implied_probability": candidate.get("implied_probability"),
        "ev_percent": candidate.get("ev_percent"),
        "estimated_roi_percent": candidate.get("estimated_roi_percent"),
        "middle_zone": candidate.get("middle_zone"),
        "middle_width": candidate.get("middle_width"),
        "arbitrage_implied_sum": candidate.get("arbitrage_implied_sum"),
        "stake_plan": candidate.get("stake_plan"),
        "max_loss": candidate.get("max_loss"),
        "max_gain": candidate.get("max_gain"),
        "line_match_confidence": candidate.get("line_match_confidence"),
        "book_disagreement_score": candidate.get("book_disagreement_score"),
        "stale_data_risk": candidate.get("stale_data_risk", False),
        "movement": candidate.get("movement", {}),
        "field_scores": candidate.get("field_scores", {}),
        "opportunity_score": round(opportunity_score, 2),
        "confidence": candidate.get("confidence"),
        "risk": candidate.get("risk"),
        "liquidity": candidate.get("liquidity"),
        "recommended_action": recommended_action,
        "recheck_after_seconds": cadence["next_check_seconds"],
        "stale_after_seconds": int(candidate.get("stale_after_seconds") or max(300, cadence["next_check_seconds"] * 4)),
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "reason": candidate.get("reason", ""),
        "blockers": list(candidate.get("blockers") or []),
        "provider": candidate.get("provider", "unknown"),
        "market_close_at": candidate.get("market_close_at"),
        "status": "active",
    }


def upsert_review_item(config: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    items = load_review_queue(config)
    by_id = {existing["id"]: existing for existing in items}
    existing = by_id.get(item["id"])
    if existing:
        item["created_at"] = existing.get("created_at", item["created_at"])
    by_id[item["id"]] = item
    ordered = sorted(by_id.values(), key=lambda row: (-float(row.get("opportunity_score", 0)), row.get("id", "")))
    save_review_queue(config, ordered)
    return item


def rescore_review_queue(config: dict[str, Any]) -> list[dict[str, Any]]:
    thresholds = config["score_thresholds"]
    items = load_review_queue(config)
    current_items: list[dict[str, Any]] = []
    for item in items:
        age_seconds = seconds_since(item.get("updated_at")) or 0
        decayed_score = apply_score_decay(float(item.get("opportunity_score", 0)), age_seconds)
        item["opportunity_score"] = decayed_score
        item["updated_at"] = utc_now_iso()

        if str(item.get("human_decision") or "").lower() == "rejected":
            item["status"] = "inactive"
            item["recommended_action"] = "no_bet"
        elif is_market_closed(item):
            item["status"] = "inactive"
            item["recommended_action"] = "no_action"
            if "market_closed" not in item["blockers"]:
                item["blockers"].append("market_closed")
        elif is_stale(item):
            item["status"] = "inactive"
            item["recommended_action"] = "no_action"
            if "stale_data" not in item["blockers"]:
                item["blockers"].append("stale_data")
        elif decayed_score < float(thresholds["ignore_below"]):
            item["status"] = "inactive"
            item["recommended_action"] = "no_action"
            if "score_decay_below_threshold" not in item["blockers"]:
                item["blockers"].append("score_decay_below_threshold")
        else:
            item["status"] = "active"
            item["recommended_action"] = classify_opportunity(decayed_score, thresholds)
            cadence = choose_next_check_seconds(
                market_type=str(item.get("market_type") or "news_events"),
                opportunity_score=decayed_score,
                provider_name=str(item.get("provider") or "news_provider"),
                config=config,
                low_liquidity=bool(item.get("liquidity", 0) < 0.35),
                market_closed=False,
            )
            item["recheck_after_seconds"] = cadence["next_check_seconds"]
            current_items.append(item)

    ordered = sorted(items, key=lambda row: (-float(row.get("opportunity_score", 0)), row.get("id", "")))
    save_review_queue(config, ordered)
    return sorted(current_items, key=lambda row: (-float(row.get("opportunity_score", 0)), row.get("id", "")))


def list_active_review_items(config: dict[str, Any]) -> list[dict[str, Any]]:
    return rescore_review_queue(config)
