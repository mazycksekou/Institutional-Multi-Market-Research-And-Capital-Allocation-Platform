from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Literal

import pandas as pd
import yfinance as yf

Direction = Literal["long", "short"]


@dataclass(frozen=True)
class ORBConfig:
    symbol: str
    start_date: date
    end_date: date
    opening_range_minutes: int = 15
    risk_reward: float = 2.0
    confirm_on_close: bool = True
    one_trade_per_day: bool = True
    use_vwap_filter: bool = False
    volume_multiplier: float = 0.0
    session_open: time = time(9, 30)
    session_close: time = time(16, 0)
    timezone: str = "America/New_York"


REQUIRED_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}


def load_intraday_data(config: ORBConfig, interval: str = "1m") -> pd.DataFrame:
    """Download intraday OHLCV data for an ORB backtest.

    Note: Yahoo Finance limits how far back high-resolution intraday data is
    available. Use recent date ranges for 1m/5m data.
    """
    ticker = yf.Ticker(config.symbol.upper().strip())
    data = ticker.history(
        start=config.start_date.isoformat(),
        end=pd.Timestamp(config.end_date).date().isoformat(),
        interval=interval,
        auto_adjust=False,
        prepost=False,
    )
    if data.empty:
        return data
    return normalize_intraday_data(data, config.timezone)


def normalize_intraday_data(data: pd.DataFrame, timezone: str) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {sorted(missing)}")

    out = data.copy()
    if not isinstance(out.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(out.index)
    if out.index.tz is None:
        out.index = out.index.tz_localize(timezone)
    else:
        out.index = out.index.tz_convert(timezone)

    out = out.sort_index()
    out["session_date"] = out.index.date
    return out


def _session_slice(day_data: pd.DataFrame, config: ORBConfig) -> pd.DataFrame:
    session = day_data.between_time(
        config.session_open.strftime("%H:%M"),
        config.session_close.strftime("%H:%M"),
        inclusive="left",
    )
    return session.copy()


def _with_vwap(session: pd.DataFrame) -> pd.DataFrame:
    session = session.copy()
    typical_price = (session["High"] + session["Low"] + session["Close"]) / 3
    cumulative_volume = session["Volume"].replace(0, pd.NA).cumsum()
    session["VWAP"] = (typical_price * session["Volume"]).cumsum() / cumulative_volume
    return session


def _trade_result(
    direction: Direction,
    entry_price: float,
    stop_price: float,
    target_price: float,
    after_entry: pd.DataFrame,
) -> tuple[str, pd.Timestamp, float]:
    for ts, row in after_entry.iterrows():
        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])

        if direction == "long":
            stop_hit = low <= stop_price
            target_hit = high >= target_price
        else:
            stop_hit = high >= stop_price
            target_hit = low <= target_price

        if stop_hit and target_hit:
            # Intrabar order is unknown from OHLC data. Use conservative ordering.
            return "loss", ts, stop_price
        if stop_hit:
            return "loss", ts, stop_price
        if target_hit:
            return "win", ts, target_price

    final_ts = after_entry.index[-1]
    final_price = float(after_entry.iloc[-1]["Close"])
    return "eod", final_ts, final_price


def _passes_filters(
    direction: Direction,
    row: pd.Series,
    opening_range: pd.DataFrame,
    config: ORBConfig,
) -> bool:
    if config.volume_multiplier > 0:
        avg_or_volume = float(opening_range["Volume"].mean())
        if avg_or_volume > 0 and float(row["Volume"]) < avg_or_volume * config.volume_multiplier:
            return False

    if config.use_vwap_filter and "VWAP" in row:
        if direction == "long" and float(row["Close"]) < float(row["VWAP"]):
            return False
        if direction == "short" and float(row["Close"]) > float(row["VWAP"]):
            return False

    return True


def run_orb_backtest(data: pd.DataFrame, config: ORBConfig) -> tuple[pd.DataFrame, dict[str, float]]:
    """Run a long/short opening range breakout backtest on intraday OHLCV data."""
    if data.empty:
        return pd.DataFrame(), _empty_metrics()

    df = normalize_intraday_data(data, config.timezone) if "session_date" not in data.columns else data.copy()
    trades: list[dict[str, object]] = []

    for session_date, day_data in df.groupby("session_date", sort=True):
        session = _session_slice(day_data, config)
        if session.empty:
            continue

        range_end = pd.Timestamp.combine(pd.Timestamp(session_date).date(), config.session_open).tz_localize(config.timezone)
        range_end = range_end + pd.Timedelta(minutes=config.opening_range_minutes)

        opening_range = session[session.index < range_end]
        post_range = session[session.index >= range_end]
        if opening_range.empty or post_range.empty:
            continue

        session = _with_vwap(session)
        post_range = session[session.index >= range_end]
        opening_range = session[session.index < range_end]

        or_high = float(opening_range["High"].max())
        or_low = float(opening_range["Low"].min())
        or_width = or_high - or_low
        if or_width <= 0:
            continue

        traded = False
        for ts, row in post_range.iterrows():
            long_break = float(row["Close" if config.confirm_on_close else "High"]) > or_high
            short_break = float(row["Close" if config.confirm_on_close else "Low"]) < or_low

            direction: Direction | None = None
            if long_break:
                direction = "long"
            elif short_break:
                direction = "short"

            if direction is None or not _passes_filters(direction, row, opening_range, config):
                continue

            entry_price = float(row["Close"]) if config.confirm_on_close else (or_high if direction == "long" else or_low)
            stop_price = or_low if direction == "long" else or_high
            risk_per_share = abs(entry_price - stop_price)
            if risk_per_share <= 0:
                continue

            if direction == "long":
                target_price = entry_price + risk_per_share * config.risk_reward
            else:
                target_price = entry_price - risk_per_share * config.risk_reward

            after_entry = post_range[post_range.index >= ts]
            exit_reason, exit_time, exit_price = _trade_result(
                direction,
                entry_price,
                stop_price,
                target_price,
                after_entry,
            )

            if direction == "long":
                pnl_per_share = exit_price - entry_price
            else:
                pnl_per_share = entry_price - exit_price
            r_multiple = pnl_per_share / risk_per_share

            trades.append(
                {
                    "date": session_date,
                    "direction": direction,
                    "or_high": or_high,
                    "or_low": or_low,
                    "or_width": or_width,
                    "entry_time": ts,
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "target_price": target_price,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "pnl_per_share": pnl_per_share,
                    "r_multiple": r_multiple,
                }
            )
            traded = True
            if config.one_trade_per_day and traded:
                break

    trades_df = pd.DataFrame(trades)
    return trades_df, calculate_metrics(trades_df)


def calculate_metrics(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return _empty_metrics()

    r = trades["r_multiple"].astype(float)
    wins = r[r > 0]
    losses = r[r < 0]
    equity = r.cumsum()
    drawdown = equity - equity.cummax()

    return {
        "trades": float(len(trades)),
        "win_rate": float((r > 0).mean()),
        "avg_r": float(r.mean()),
        "total_r": float(r.sum()),
        "best_r": float(r.max()),
        "worst_r": float(r.min()),
        "avg_win_r": float(wins.mean()) if not wins.empty else 0.0,
        "avg_loss_r": float(losses.mean()) if not losses.empty else 0.0,
        "max_drawdown_r": float(drawdown.min()) if not drawdown.empty else 0.0,
    }


def _empty_metrics() -> dict[str, float]:
    return {
        "trades": 0.0,
        "win_rate": 0.0,
        "avg_r": 0.0,
        "total_r": 0.0,
        "best_r": 0.0,
        "worst_r": 0.0,
        "avg_win_r": 0.0,
        "avg_loss_r": 0.0,
        "max_drawdown_r": 0.0,
    }
