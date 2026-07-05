from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


DATA_DIR = Path("data")
BETS_FILE = DATA_DIR / "bets.csv"


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _read_existing(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists() or path.stat().st_size == 0:
        return [], []

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        records = [dict(row) for row in reader]

    return fieldnames, records


def append_bet(row: dict[str, Any], path: Path = BETS_FILE) -> dict[str, Any]:
    """
    Append one bet record to the CSV ledger.

    Canonical owner: src/services/bet_csv_service.py
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_fields, records = _read_existing(path)

    incoming_fields = list(row.keys())
    fieldnames = list(existing_fields)

    for field in incoming_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    clean_row = {field: _stringify(row.get(field)) for field in fieldnames}

    # If the schema changed, rewrite with the expanded header.
    if existing_fields and fieldnames != existing_fields:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow({field: record.get(field, "") for field in fieldnames})
            writer.writerow(clean_row)
    else:
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames or incoming_fields)
            if write_header:
                writer.writeheader()
            writer.writerow(clean_row)

    return dict(row)


def _float_from(record: dict[str, Any], keys: tuple[str, ...]) -> float:
    for key in keys:
        raw = record.get(key)
        if raw in (None, ""):
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return 0.0


def summarize_bets(path: Path = BETS_FILE) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Summarize the CSV bet ledger.

    Returns (summary, records) to preserve the current main.py route contract.
    """
    if not path.exists() or path.stat().st_size == 0:
        return {"message": "No bets logged yet."}, []

    _, records = _read_existing(path)

    wins = 0
    losses = 0
    pushes = 0
    total_staked = 0.0
    total_profit = 0.0

    for record in records:
        total_staked += _float_from(record, ("stake", "amount", "risk", "wager", "units"))
        total_profit += _float_from(record, ("profit", "pnl", "net", "net_profit"))

        result = str(record.get("result") or record.get("outcome") or "").strip().lower()
        if result in {"win", "won", "w"}:
            wins += 1
        elif result in {"loss", "lost", "l"}:
            losses += 1
        elif result in {"push", "void", "p"}:
            pushes += 1

    settled = wins + losses

    summary = {
        "count": len(records),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "total_staked": total_staked,
        "total_profit": total_profit,
        "win_rate": (wins / settled) if settled else 0.0,
        "roi": (total_profit / total_staked) if total_staked else 0.0,
    }

    return summary, records
