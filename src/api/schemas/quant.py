from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class BetAnalysisRequest(BaseModel):
    sport: str
    event: str
    pick: str
    market: str
    odds: int
    true_probability_pct: float
    stake: float
    bankroll: float
    correlation_group: str
    current_group_exposure: float = 0
    notes: Optional[str] = None


class MarketPricingRequest(BaseModel):
    event: str
    provider: str
    sportsbook: str
    league: str
    market: str
    selection: str
    american_odds: int
    true_probability: float = Field(gt=0, lt=1)
    bankroll: float = Field(ge=0)
    stake: float = Field(ge=0)
    correlation_group: Optional[str] = None
    notes: Optional[str] = None


class StockAnalysisRequest(BaseModel):
    ticker: str
    current_price: float
    expected_stock_return_pct: float
    beta: float
    risk_free_rate_pct: float
    expected_market_return_pct: float
    planned_position_size: float
    portfolio_value: float
    notes: Optional[str] = None
