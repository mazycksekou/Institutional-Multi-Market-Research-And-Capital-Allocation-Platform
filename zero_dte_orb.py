from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import product
from typing import Any

import pandas as pd

from orb_backtest import ORBConfig, load_intraday_data, run_orb_backtest


@dataclass(frozen=True)
class ProfitabilityWindow:
    label: str = "Weekly"
    rule: str = "W"


PROFITABILITY_WINDOWS: dict[str, ProfitabilityWindow] = {
    "Daily": ProfitabilityWindow("Daily", "D"),
    "Weekly": ProfitabilityWindow("Weekly", "W"),
    "Monthly": ProfitabilityWindow("Monthly", "ME"),
}


def build_0dte_orb_config(
    symbol: str,
    start_date: date,
    end_date: date,
    opening_range_minutes: int = 15,
    risk_reward: float = 2.0,
    confirm_on_close: bool = True,
    one_trade_per_day: bool = True,
    use_vwap_filter: bool = False,
    volume_multiplier: float = 0.0,
) -> ORBConfig:
    """Create the baseline 0DTE ORB config.

    This intentionally uses the ORB signal on the underlying. The 0DTE option
    execution layer can map each signal to same-day calls/puts once an option
    chain provider is connected.
    """
    return ORBConfig(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        opening_range_minutes=opening_range_minutes,
        risk_reward=risk_reward,
        confirm_on_close=confirm_on_close,
        one_trade_per_day=one_trade_per_day,
        use_vwap_filter=use_vwap_filter,
        volume_multiplier=volume_multiplier,
    )


def add_0dte_baseline_fields(
    trades: pd.DataFrame,
    account_size: float,
    risk_per_trade_pct: float,
    profitability_window: str = "Weekly",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Add baseline 0DTE data fields and money-over-time metrics.

    The P&L model is risk based: each trade risks a fixed percentage of account
    equity and converts R-multiple into dollars. This makes baseline tests
    comparable while the option premium fill model is still being tuned.
    """
    if trades.empty:
        return trades.copy(), _empty_0dte_metrics(account_size, profitability_window)

    out = trades.copy()
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    out = out.sort_values("entry_time")

    starting_equity = float(account_size)
    risk_dollars = starting_equity * (float(risk_per_trade_pct) / 100.0)

    out["strategy"] = "15m ORB 0DTE baseline"
    out["option_side"] = out["direction"].map({"long": "CALL", "short": "PUT"})
    out["risk_dollars"] = risk_dollars
    out["pnl_dollars"] = out["r_multiple"].astype(float) * risk_dollars
    out["equity"] = starting_equity + out["pnl_dollars"].cumsum()
    out["return_pct"] = out["pnl_dollars"] / starting_equity * 100.0
    out["cumulative_return_pct"] = (out["equity"] / starting_equity - 1.0) * 100.0
    out["made_money"] = out["pnl_dollars"] > 0

    window = PROFITABILITY_WINDOWS.get(profitability_window, PROFITABILITY_WINDOWS["Weekly"])
    by_period = (
        out.set_index("entry_time")
        .resample(window.rule)
        .agg(
            trades=("pnl_dollars", "count"),
            pnl_dollars=("pnl_dollars", "sum"),
            avg_r=("r_multiple", "mean"),
            wins=("made_money", "sum"),
            ending_equity=("equity", "last"),
        )
    )
    by_period = by_period[by_period["trades"] > 0].copy()
    by_period["return_pct"] = by_period["pnl_dollars"] / starting_equity * 100.0
    by_period["made_money"] = by_period["pnl_dollars"] > 0
    by_period["win_rate"] = by_period["wins"] / by_period["trades"]

    metrics = calculate_0dte_money_metrics(out, by_period, starting_equity, window.label)
    return out, metrics


def calculate_0dte_money_metrics(
    trades: pd.DataFrame,
    period_returns: pd.DataFrame,
    starting_equity: float,
    window_label: str,
) -> dict[str, Any]:
    ending_equity = float(trades["equity"].iloc[-1]) if not trades.empty else starting_equity
    total_pnl = ending_equity - starting_equity
    total_return_pct = (ending_equity / starting_equity - 1.0) * 100.0 if starting_equity else 0.0

    profitable_periods = int(period_returns["made_money"].sum()) if not period_returns.empty else 0
    total_periods = int(len(period_returns))
    profitable_period_rate = profitable_periods / total_periods if total_periods else 0.0

    equity = trades["equity"].astype(float) if not trades.empty else pd.Series(dtype=float)
    drawdown_pct = ((equity / equity.cummax()) - 1.0) * 100.0 if not equity.empty else pd.Series(dtype=float)

    return {
        "starting_equity": starting_equity,
        "ending_equity": ending_equity,
        "total_pnl_dollars": total_pnl,
        "total_return_pct": total_return_pct,
        "made_money": bool(total_pnl > 0),
        "profitability_window": window_label,
        "profitable_periods": profitable_periods,
        "total_periods": total_periods,
        "profitable_period_rate": profitable_period_rate,
        "max_drawdown_pct": float(drawdown_pct.min()) if not drawdown_pct.empty else 0.0,
        "avg_trade_return_pct": float(trades["return_pct"].mean()) if not trades.empty else 0.0,
    }


def run_0dte_orb_baseline(
    symbol: str,
    start_date: date,
    end_date: date,
    account_size: float = 10_000.0,
    risk_per_trade_pct: float = 1.0,
    profitability_window: str = "Weekly",
    **config_kwargs: Any,
) -> dict[str, Any]:
    config = build_0dte_orb_config(symbol, start_date, end_date, **config_kwargs)
    data = load_intraday_data(config)
    trades, orb_metrics = run_orb_backtest(data, config)
    enriched_trades, money_metrics = add_0dte_baseline_fields(
        trades,
        account_size=account_size,
        risk_per_trade_pct=risk_per_trade_pct,
        profitability_window=profitability_window,
    )
    return {
        "config": config,
        "data": data,
        "trades": enriched_trades,
        "orb_metrics": orb_metrics,
        "money_metrics": money_metrics,
        "period_returns": build_period_returns(enriched_trades, account_size, profitability_window),
    }


def build_period_returns(
    trades: pd.DataFrame,
    account_size: float,
    profitability_window: str = "Weekly",
) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    window = PROFITABILITY_WINDOWS.get(profitability_window, PROFITABILITY_WINDOWS["Weekly"])
    out = (
        trades.set_index("entry_time")
        .resample(window.rule)
        .agg(
            trades=("pnl_dollars", "count"),
            pnl_dollars=("pnl_dollars", "sum"),
            avg_r=("r_multiple", "mean"),
            ending_equity=("equity", "last"),
        )
    )
    out = out[out["trades"] > 0].copy()
    out["return_pct"] = out["pnl_dollars"] / float(account_size) * 100.0
    out["made_money"] = out["pnl_dollars"] > 0
    return out.reset_index()


def tune_0dte_orb_baseline(
    symbol: str,
    start_date: date,
    end_date: date,
    account_size: float,
    risk_per_trade_pct: float,
    opening_range_minutes: list[int],
    risk_rewards: list[float],
    volume_multipliers: list[float],
    vwap_filters: list[bool],
    profitability_window: str = "Weekly",
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for minutes, rr, volume_mult, use_vwap in product(
        opening_range_minutes,
        risk_rewards,
        volume_multipliers,
        vwap_filters,
    ):
        result = run_0dte_orb_baseline(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            account_size=account_size,
            risk_per_trade_pct=risk_per_trade_pct,
            profitability_window=profitability_window,
            opening_range_minutes=minutes,
            risk_reward=rr,
            volume_multiplier=volume_mult,
            use_vwap_filter=use_vwap,
            confirm_on_close=True,
            one_trade_per_day=True,
        )
        money = result["money_metrics"]
        orb = result["orb_metrics"]
        rows.append(
            {
                "opening_range_minutes": minutes,
                "risk_reward": rr,
                "volume_multiplier": volume_mult,
                "use_vwap_filter": use_vwap,
                "trades": orb["trades"],
                "win_rate": orb["win_rate"],
                "avg_r": orb["avg_r"],
                "total_r": orb["total_r"],
                "total_return_pct": money["total_return_pct"],
                "total_pnl_dollars": money["total_pnl_dollars"],
                "profitable_period_rate": money["profitable_period_rate"],
                "max_drawdown_pct": money["max_drawdown_pct"],
                "made_money": money["made_money"],
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["profitable_period_rate", "total_return_pct", "avg_r"],
        ascending=[False, False, False],
    )


def _empty_0dte_metrics(account_size: float, profitability_window: str) -> dict[str, Any]:
    return {
        "starting_equity": float(account_size),
        "ending_equity": float(account_size),
        "total_pnl_dollars": 0.0,
        "total_return_pct": 0.0,
        "made_money": False,
        "profitability_window": profitability_window,
        "profitable_periods": 0,
        "total_periods": 0,
        "profitable_period_rate": 0.0,
        "max_drawdown_pct": 0.0,
        "avg_trade_return_pct": 0.0,
    }
