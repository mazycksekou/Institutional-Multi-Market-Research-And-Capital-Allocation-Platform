from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.core.backtester import run_walk_forward_backtest


def sports_master_db_path() -> Path:
    return Path(os.getenv("SPORTS_MASTER_DB_PATH", "data/sports_master.db"))


def run_model_backtest(
    *,
    sport: str = "basketball_nba",
    market: str = "h2h",
    start_year: int = 2024,
    min_edge: float = 0.01,
    min_train_rows: int = 40,
) -> dict[str, Any]:
    return run_walk_forward_backtest(
        db_path=sports_master_db_path(),
        sport_key=sport,
        market=market,
        start_year=start_year,
        min_edge=min_edge,
        min_train_rows=min_train_rows,
    )
