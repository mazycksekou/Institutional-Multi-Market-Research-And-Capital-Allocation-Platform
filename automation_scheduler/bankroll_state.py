from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = "bankroll_state_v1"
ROOT = Path("data/bankroll")


def _redact(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for k, v in payload.items():
            lk = str(k).lower()
            if any(s in lk for s in ("secret", "token", "password", "credential", "api_key")):
                out[k] = "[redacted]"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(payload, list):
        return [_redact(v) for v in payload]
    return payload


def default_bankroll_state(starting_bankroll: float = 10000.0) -> dict[str, Any]:
    return {
        "bankroll_id": f"bankroll_{uuid4().hex[:12]}",
        "starting_bankroll": float(starting_bankroll),
        "current_bankroll": float(starting_bankroll),
        "peak_bankroll": float(starting_bankroll),
        "current_drawdown_percent": 0.0,
        "daily_exposure_percent": 0.0,
        "weekly_exposure_percent": 0.0,
        "market_group_exposure": {},
        "open_risk": 0.0,
        "closed_pnl": 0.0,
        "schema_version": SCHEMA_VERSION,
    }


def save_bankroll_state(state: dict[str, Any], path: Path | None = None) -> Path:
    ROOT.mkdir(parents=True, exist_ok=True)
    data = _redact(state)
    p = path or (ROOT / f"{data.get('bankroll_id', 'bankroll')}.json")
    p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return p


def load_bankroll_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
