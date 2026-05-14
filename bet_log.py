from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BET_LOG_PATH = Path("data") / "bet_log.jsonl"

CORE_FIELDS = [
    "bet_id",
    "timestamp",
    "sport_key",
    "event_id",
    "event",
    "sportsbook",
    "market",
    "selection",
    "line",
    "odds_american",
    "stake",
    "unit_size",
    "bankroll_at_bet",
    "model_level",
    "probability_type",
    "model_probability",
    "market_probability",
    "final_probability",
    "implied_probability",
    "edge_percent",
    "ev_per_100",
    "kelly_percent",
    "suggested_stake",
    "decision",
    "minimum_playable_odds",
    "actual_odds_taken",
    "closing_odds",
    "clv_percent",
    "result",
    "profit_loss",
    "status",
    "risk_profile",
    "confidence",
    "correlation_group",
    "user_action",
    "error_type",
    "notes",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_path(path: str | Path | None = None) -> Path:
    return Path(path) if path is not None else BET_LOG_PATH


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _american_to_decimal(odds: Any) -> float | None:
    odds_int = _to_int(odds)
    if odds_int is None or odds_int == 0:
        return None
    if odds_int > 0:
        return 1 + odds_int / 100
    return 1 + 100 / abs(odds_int)


def _implied_probability(odds: Any) -> float | None:
    decimal_odds = _american_to_decimal(odds)
    if not decimal_odds:
        return None
    return 1 / decimal_odds


def _is_worse_price(actual_odds: Any, minimum_odds: Any) -> bool:
    actual_decimal = _american_to_decimal(actual_odds)
    minimum_decimal = _american_to_decimal(minimum_odds)
    if actual_decimal is None or minimum_decimal is None:
        return False
    return actual_decimal < minimum_decimal


def calculate_profit_loss(result: str | None, stake: Any, odds_american: Any) -> float:
    normalized = (result or "").strip().lower()
    stake_float = _to_float(stake)
    odds_int = _to_int(odds_american)
    if normalized in {"push", "void", "cancelled", "canceled"}:
        return 0.0
    if normalized in {"loss", "lost"}:
        return round(-stake_float, 2)
    if normalized not in {"win", "won"} or odds_int is None:
        return 0.0
    if odds_int > 0:
        return round(stake_float * odds_int / 100, 2)
    return round(stake_float * 100 / abs(odds_int), 2)


def calculate_clv_percent(actual_odds_taken: Any, closing_odds: Any) -> float | None:
    actual_decimal = _american_to_decimal(actual_odds_taken)
    closing_decimal = _american_to_decimal(closing_odds)
    if actual_decimal is None or closing_decimal is None:
        return None
    return round(((actual_decimal - closing_decimal) / closing_decimal) * 100, 4)


def _resolve_error_type(entry: dict[str, Any]) -> str | None:
    decision = str(entry.get("decision") or "").strip().lower()
    user_action = str(entry.get("user_action") or "").strip().lower()
    probability_type = str(entry.get("probability_type") or "").strip().lower()
    manual_override = bool(entry.get("manual_override"))
    stake = _to_float(entry.get("stake"))
    suggested = _to_float(entry.get("suggested_stake"))

    if decision == "no_bet" and user_action == "bet_placed":
        return "ignored_no_bet"
    if _is_worse_price(entry.get("actual_odds_taken"), entry.get("minimum_playable_odds")):
        return "bad_price"
    if suggested > 0 and stake > suggested:
        return "overstaked"
    if probability_type == "market_derived" and user_action == "bet_placed" and not manual_override:
        return "market_only_bet"
    return entry.get("error_type")


def create_bet_log_entry(payload: dict[str, Any]) -> dict[str, Any]:
    entry = {field: payload.get(field) for field in CORE_FIELDS}
    entry.update({k: v for k, v in payload.items() if k not in entry})
    entry["bet_id"] = entry.get("bet_id") or str(uuid.uuid4())
    entry["timestamp"] = entry.get("timestamp") or _now_iso()
    entry["actual_odds_taken"] = entry.get("actual_odds_taken", entry.get("odds_american"))
    entry["odds_american"] = entry.get("odds_american", entry.get("actual_odds_taken"))
    entry["result"] = entry.get("result") or "pending"
    entry["status"] = entry.get("status") or "open"

    implied = _implied_probability(entry.get("actual_odds_taken"))
    if entry.get("implied_probability") is None and implied is not None:
        entry["implied_probability"] = round(implied, 6)

    entry["clv_percent"] = calculate_clv_percent(entry.get("actual_odds_taken"), entry.get("closing_odds"))
    entry["error_type"] = _resolve_error_type(entry)

    if entry.get("confirmed_bets_allowed") is False and entry.get("status") == "confirmed_model_bet":
        entry["status"] = "logged"

    return entry


def append_bet_log_entry(entry: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    target = _log_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def read_bet_log_entries(path: str | Path | None = None) -> list[dict[str, Any]]:
    target = _log_path(path)
    if not target.exists():
        return []
    entries: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            entries.append(json.loads(text))
    return entries


def update_bet_result(
    bet_id: str,
    result: str,
    closing_odds: Any = None,
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    target = _log_path(path)
    entries = read_bet_log_entries(target)
    updated: dict[str, Any] | None = None
    for entry in entries:
        if entry.get("bet_id") != bet_id:
            continue
        if closing_odds is not None:
            entry["closing_odds"] = closing_odds
        entry["result"] = result
        entry["status"] = "closed" if str(result).lower() in {"win", "won", "loss", "lost", "push"} else entry.get("status")
        entry["profit_loss"] = calculate_profit_loss(result, entry.get("stake"), entry.get("actual_odds_taken") or entry.get("odds_american"))
        entry["clv_percent"] = calculate_clv_percent(entry.get("actual_odds_taken"), entry.get("closing_odds"))
        updated = entry
        break

    if updated is None:
        return None

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return updated


def get_performance_summary(entries: list[dict[str, Any]] | None = None, path: str | Path | None = None) -> dict[str, Any]:
    rows = entries if entries is not None else read_bet_log_entries(path)
    total_bets = len(rows)
    wins = sum(1 for row in rows if str(row.get("result") or "").lower() in {"win", "won"})
    losses = sum(1 for row in rows if str(row.get("result") or "").lower() in {"loss", "lost"})
    pushes = sum(1 for row in rows if str(row.get("result") or "").lower() == "push")
    total_staked = round(sum(_to_float(row.get("stake")) for row in rows), 2)
    profit_loss = round(sum(_to_float(row.get("profit_loss")) for row in rows), 2)
    clv_values = [
        _to_float(row.get("clv_percent"))
        for row in rows
        if row.get("clv_percent") is not None
    ]
    error_counts: dict[str, int] = {}
    for row in rows:
        error_type = row.get("error_type")
        if not error_type:
            continue
        error_counts[str(error_type)] = error_counts.get(str(error_type), 0) + 1

    roi = round((profit_loss / total_staked) * 100, 2) if total_staked else 0.0
    return {
        "total_bets": total_bets,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "total_staked": total_staked,
        "profit_loss": profit_loss,
        "roi": roi,
        "yield": roi,
        "average_clv": round(sum(clv_values) / len(clv_values), 4) if clv_values else 0.0,
        "error_counts": error_counts,
    }


def get_bankroll_summary(entries: list[dict[str, Any]] | None = None, path: str | Path | None = None) -> dict[str, Any]:
    rows = entries if entries is not None else read_bet_log_entries(path)
    starting = next((_to_float(row.get("bankroll_at_bet")) for row in rows if row.get("bankroll_at_bet") is not None), 0.0)
    profit_loss = round(sum(_to_float(row.get("profit_loss")) for row in rows), 2)
    current = round(starting + profit_loss, 2) if starting else profit_loss
    return {
        "starting_bankroll": starting,
        "profit_loss": profit_loss,
        "current_bankroll": current,
        "bankroll_movement": round(current - starting, 2) if starting else profit_loss,
        "total_staked": round(sum(_to_float(row.get("stake")) for row in rows), 2),
    }


def get_clv_report(entries: list[dict[str, Any]] | None = None, path: str | Path | None = None) -> dict[str, Any]:
    rows = entries if entries is not None else read_bet_log_entries(path)
    clv_rows = []
    for row in rows:
        clv = calculate_clv_percent(row.get("actual_odds_taken"), row.get("closing_odds"))
        if clv is None:
            continue
        out = dict(row)
        out["clv_percent"] = clv
        clv_rows.append(out)
    average = round(sum(_to_float(row.get("clv_percent")) for row in clv_rows) / len(clv_rows), 4) if clv_rows else 0.0
    return {
        "count": len(clv_rows),
        "average_clv": average,
        "positive_clv_count": sum(1 for row in clv_rows if _to_float(row.get("clv_percent")) > 0),
        "negative_clv_count": sum(1 for row in clv_rows if _to_float(row.get("clv_percent")) < 0),
        "bets": clv_rows,
    }
