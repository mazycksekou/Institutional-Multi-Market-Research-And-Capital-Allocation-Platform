from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from src.brokerage.ledger import record_ledger_event

from src.data.data_paths import get_paper_ledger_dir
from src.services.scheduler_config import SCHEMA_VERSION, redact_secrets as _redact_secrets, utc_now_iso


LEDGER_SCHEMA_VERSION = f"{SCHEMA_VERSION}.paper_ledger.v1"


def _ledger_path(base_dir: str = "data/paper_ledger") -> Path:
    normalized = str(base_dir).replace("\\", "/").rstrip("/")
    directory = get_paper_ledger_dir() if normalized in {"data/paper_ledger", "data"} else Path(base_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "paper_ledger.json"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _american_to_implied_probability(odds: Any) -> float:
    american = _to_float(odds)
    if american == 0:
        return 0.0
    if american > 0:
        return 100.0 / (american + 100.0)
    return abs(american) / (abs(american) + 100.0)


def _profit_for_win(stake: float, american_odds: float) -> float:
    if american_odds >= 100:
        return stake * (american_odds / 100.0)
    if american_odds <= -100:
        return stake * (100.0 / abs(american_odds))
    return 0.0


def load_paper_ledger(base_dir: str = "data/paper_ledger") -> list[dict[str, Any]]:
    path = _ledger_path(base_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_paper_ledger(items: list[dict[str, Any]], base_dir: str = "data/paper_ledger") -> None:
    path = _ledger_path(base_dir)
    path.write_text(json.dumps(items, indent=2, sort_keys=True), encoding="utf-8")


def create_paper_entry(payload: dict[str, Any], base_dir: str = "data/paper_ledger") -> dict[str, Any]:
    implied_probability = payload.get("implied_probability")
    if implied_probability is None:
        implied_probability = _american_to_implied_probability(payload.get("recommended_odds"))
    no_vig_probability = payload.get("no_vig_probability")
    if no_vig_probability is None:
        no_vig_probability = implied_probability

    entry = {
        "ledger_id": uuid.uuid4().hex[:16],
        "created_at": utc_now_iso(),
        "recommendation_id": str(payload.get("recommendation_id") or uuid.uuid4().hex[:12]),
        "model_id": str(payload.get("model_id") or "unknown_model"),
        "model_group": str(payload.get("model_group") or "unknown_group"),
        "market_type": str(payload.get("market_type") or "unknown_market"),
        "event_id": payload.get("event_id"),
        "event_name": payload.get("event_name"),
        "market_name": payload.get("market_name"),
        "selection_name": payload.get("selection_name"),
        "book": payload.get("book"),
        "opening_odds": payload.get("opening_odds"),
        "recommended_odds": payload.get("recommended_odds"),
        "closing_odds": payload.get("closing_odds"),
        "model_probability": _to_float(payload.get("model_probability")),
        "implied_probability": _to_float(implied_probability),
        "no_vig_probability": _to_float(no_vig_probability),
        "ev_percent": _to_float(payload.get("ev_percent")),
        "recommended_action": payload.get("recommended_action", "paper_tracking"),
        "recommended_kelly_mode": payload.get("recommended_kelly_mode", "fractional"),
        "recommended_stake_percent": _to_float(payload.get("recommended_stake_percent")),
        "paper_stake": _to_float(payload.get("paper_stake"), default=0.0),
        "result_status": payload.get("result_status", "pending"),
        "paper_profit_loss": _to_float(payload.get("paper_profit_loss"), default=0.0),
        "settlement_status": payload.get("settlement_status", "open"),
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "schema_version": LEDGER_SCHEMA_VERSION,
    }

    ledger = load_paper_ledger(base_dir)
    ledger.append(entry)
    _save_paper_ledger(ledger, base_dir)
    ledger_entry_snapshot = {key: value for key, value in entry.items() if key != "brokerage_ledger_event"}
    entry["brokerage_ledger_event"] = record_ledger_event(
        event_type="paper_trade_entry_created",
        subject_id=str(entry["ledger_id"]),
        payload={"paper_ledger_entry": ledger_entry_snapshot},
        metadata={"source_module": "automation_scheduler.paper_trade_ledger"},
    )
    return entry


def update_closing_line(recommendation_id: str, closing_odds: float, base_dir: str = "data/paper_ledger") -> dict[str, Any] | None:
    ledger = load_paper_ledger(base_dir)
    target = None
    for entry in ledger:
        if str(entry.get("recommendation_id")) == str(recommendation_id):
            entry["closing_odds"] = _to_float(closing_odds)
            target = entry
            break
    if target is not None:
        _save_paper_ledger(ledger, base_dir)
        ledger_entry_snapshot = {key: value for key, value in target.items() if key != "brokerage_ledger_event"}
        target["brokerage_ledger_event"] = record_ledger_event(
            event_type="paper_trade_entry_updated",
            subject_id=str(target["ledger_id"]),
            payload={"paper_ledger_entry": ledger_entry_snapshot, "closing_odds": _to_float(closing_odds)},
            metadata={"source_module": "automation_scheduler.paper_trade_ledger"},
        )
    return target


def settle_paper_entry(recommendation_id: str, result_status: str, base_dir: str = "data/paper_ledger") -> dict[str, Any] | None:
    result = str(result_status).lower()
    if result not in {"win", "loss", "push"}:
        raise ValueError("result_status must be one of: win, loss, push")

    ledger = load_paper_ledger(base_dir)
    target = None
    for entry in ledger:
        if str(entry.get("recommendation_id")) != str(recommendation_id):
            continue
        stake = _to_float(entry.get("paper_stake"), default=0.0)
        odds = _to_float(entry.get("recommended_odds"), default=0.0)
        if result == "win":
            pnl = _profit_for_win(stake, odds)
        elif result == "loss":
            pnl = -stake
        else:
            pnl = 0.0
        entry["result_status"] = result
        entry["paper_profit_loss"] = round(pnl, 4)
        entry["settlement_status"] = "settled"
        target = entry
        break
    if target is not None:
        _save_paper_ledger(ledger, base_dir)
    return target


def summarize_paper_ledger(base_dir: str = "data/paper_ledger") -> dict[str, Any]:
    ledger = load_paper_ledger(base_dir)
    settled = [e for e in ledger if str(e.get("settlement_status")) == "settled"]
    wins = sum(1 for e in settled if str(e.get("result_status")) == "win")
    losses = sum(1 for e in settled if str(e.get("result_status")) == "loss")
    pushes = sum(1 for e in settled if str(e.get("result_status")) == "push")
    total_stake = sum(_to_float(e.get("paper_stake")) for e in settled)
    total_pnl = sum(_to_float(e.get("paper_profit_loss")) for e in settled)
    realized_roi_percent = (total_pnl / total_stake * 100.0) if total_stake > 0 else 0.0
    return {
        "ok": True,
        "status": "paper_tracking",
        "total_entries": len(ledger),
        "settled_entries": len(settled),
        "win_count": wins,
        "loss_count": losses,
        "push_count": pushes,
        "realized_roi_percent": round(realized_roi_percent, 4),
        "paper_profit_loss": round(total_pnl, 4),
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }


def redact_secrets(payload: Any) -> Any:
    return _redact_secrets(payload)
