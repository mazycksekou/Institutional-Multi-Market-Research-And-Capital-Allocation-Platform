from __future__ import annotations

from typing import Any

from src.services.model_backtest_service import run_model_backtest


def register_model_backtest_routes(app: Any) -> None:
    """
    Register model backtest route.

    Canonical owner: src/api/model_backtest_routes.py
    """

    @app.get("/model/backtest")
    def model_backtest(
        sport: str = "basketball_nba",
        market: str = "h2h",
        start_year: int = 2024,
        min_edge: float = 0.01,
        min_train_rows: int = 40,
    ):
        return run_model_backtest(
            sport=sport,
            market=market,
            start_year=start_year,
            min_edge=min_edge,
            min_train_rows=min_train_rows,
        )
