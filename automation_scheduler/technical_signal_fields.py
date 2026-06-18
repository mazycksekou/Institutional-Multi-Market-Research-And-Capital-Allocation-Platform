from __future__ import annotations

OHLCV_FIELDS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

TECHNICAL_INDICATOR_FIELDS = [
    "ema_12",
    "ema_26",
    "macd",
    "macd_signal_line",
    "macd_histogram",
    "macd_divergence",
    "vwap",
    "rsi",
    "adx",
]

MARKET_PARTICIPATION_FIELDS = [
    "market_breadth",
    "order_flow",
    "open_interest",
]

TECHNICAL_SIGNAL_FIELDS = [
    *OHLCV_FIELDS,
    *TECHNICAL_INDICATOR_FIELDS,
    *MARKET_PARTICIPATION_FIELDS,
    "bid_size",
    "ask_size",
    "quoted_depth",
    "volume_open_interest_ratio",
    "net_gex",
    "strike_gex",
    "call_gex",
    "put_gex",
    "gamma_flip_level",
    "gex_regime",
    "strike_volume_profile",
    "volume_profile_peak_strike",
    "cpi_day",
    "fomc_day",
    "jobs_day",
    "fed_speaker_day",
]

TECHNICAL_SIGNAL_FIELDS_BY_MARKET = {
    "stocks": {
        "required": [
            *OHLCV_FIELDS,
            *TECHNICAL_INDICATOR_FIELDS,
            "market_breadth",
        ],
        "optional": ["order_flow", "open_interest"],
    },
    "ETFs": {
        "required": [
            *OHLCV_FIELDS,
            *TECHNICAL_INDICATOR_FIELDS,
            "market_breadth",
        ],
        "optional": ["order_flow", "open_interest"],
    },
    "crypto": {
        "required": [
            *OHLCV_FIELDS,
            *TECHNICAL_INDICATOR_FIELDS,
            "order_flow",
            "open_interest",
        ],
        "optional": ["market_breadth"],
    },
    "prediction_markets": {
        "required": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal_line",
            "macd_histogram",
            "macd_divergence",
            "rsi",
            "adx",
            "open_interest",
        ],
        "optional": ["vwap", "order_flow", "market_breadth"],
    },
    "sports_odds": {
        "required": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal_line",
            "macd_histogram",
            "macd_divergence",
            "rsi",
            "adx",
        ],
        "optional": ["vwap", "order_flow", "open_interest", "market_breadth"],
    },
    "0dte_options": {
        "required": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal_line",
            "macd_histogram",
            "macd_divergence",
            "vwap",
            "rsi",
            "adx",
        ],
        "optional": [
            "market_breadth",
            "order_flow",
            "open_interest",
            "bid_size",
            "ask_size",
            "quoted_depth",
            "volume_open_interest_ratio",
            "net_gex",
            "strike_gex",
            "call_gex",
            "put_gex",
            "gamma_flip_level",
            "gex_regime",
            "strike_volume_profile",
            "volume_profile_peak_strike",
            "cpi_day",
            "fomc_day",
            "jobs_day",
            "fed_speaker_day",
        ],
    },
}

SPORT_TECHNICAL_SIGNAL_SCOPE = {
    "basketball_nba": "odds_market_movement",
    "basketball_wnba": "odds_market_movement",
    "americanfootball_nfl": "odds_market_movement",
    "americanfootball_ncaaf": "odds_market_movement",
    "baseball_mlb": "odds_market_movement",
    "icehockey_nhl": "odds_market_movement",
    "soccer": "odds_market_movement",
    "tennis": "odds_market_movement",
    "ufc_mma": "odds_market_movement",
    "boxing": "odds_market_movement",
    "golf": "odds_market_movement",
    "basketball_ncaab": "odds_market_movement",
    "basketball_ncaaw": "odds_market_movement",
}


def technical_fields_for_market(market: str, include_optional: bool = True) -> list[str]:
    spec = TECHNICAL_SIGNAL_FIELDS_BY_MARKET.get(market, {})
    fields = list(spec.get("required", []))
    if include_optional:
        fields.extend(spec.get("optional", []))
    return list(dict.fromkeys(fields))
