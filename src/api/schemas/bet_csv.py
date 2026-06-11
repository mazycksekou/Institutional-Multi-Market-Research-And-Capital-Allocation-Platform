from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BetLogRequest(BaseModel):
    date: Optional[str] = None
    type: str = "bet"
    sport: Optional[str] = None
    event: Optional[str] = None
    pick: Optional[str] = None
    market: Optional[str] = None
    odds: Optional[int] = None
    stake: float = 0
    bankroll: Optional[float] = None
    true_probability_pct: Optional[float] = None
    implied_probability_pct: Optional[float] = None
    edge_pct: Optional[float] = None
    ev_per_100: Optional[float] = None
    ev_dollars: Optional[float] = None
    kelly_pct: Optional[float] = None
    suggested_stake: Optional[float] = None
    correlation_group: Optional[str] = None
    exposure_status: Optional[str] = None
    decision: Optional[str] = None
    result: Optional[str] = "pending"
    profit_or_loss: float = 0
    notes: Optional[str] = None
