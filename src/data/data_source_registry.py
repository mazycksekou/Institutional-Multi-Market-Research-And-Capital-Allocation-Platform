from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from src.core.budget_gates import build_budget_gate, default_approval_status
from src.services.scheduler_config import sanitize_filename
from src.data.source_quality_scoring import FUTURE_ONLY_ACCESS_TYPES, score_lane, score_source
from src.market_intelligence.technical_signal_fields import technical_fields_for_market


ACCESS_TYPES = {
    "open_public",
    "free_key",
    "free_tier",
    "open_dataset",
    "public_wrapper_with_terms_review",
    "manual_import",
    "paid_candidate",
    "partner_candidate",
    "institutional_vendor_candidate",
    "broker_data_candidate",
    "sportsbook_account_candidate",
    "internal_proprietary_candidate",
    "unknown",
}

MANDATORY_LANES: tuple[dict[str, str], ...] = (
    {"lane_id": "prediction_markets", "module": "prediction_markets", "sport_or_asset": "Prediction Markets", "category": "prediction_market"},
    {"lane_id": "kalshi", "module": "kalshi", "sport_or_asset": "Kalshi", "category": "prediction_market"},
    {"lane_id": "polymarket", "module": "polymarket", "sport_or_asset": "Polymarket", "category": "prediction_market"},
    {"lane_id": "institutional_stock_pro_analyst", "module": "institutional_stock_pro_analyst", "sport_or_asset": "Institutional Stock Pro Analyst", "category": "stock_analytics"},
    {"lane_id": "cryptocurrency_edge_lab", "module": "cryptocurrency_edge_lab", "sport_or_asset": "Cryptocurrency Edge Lab", "category": "crypto"},
    {"lane_id": "stocks", "module": "stocks", "sport_or_asset": "Stocks", "category": "financial_market"},
    {"lane_id": "ETFs", "module": "ETFs", "sport_or_asset": "ETFs", "category": "financial_market"},
    {"lane_id": "bonds", "module": "bonds", "sport_or_asset": "Bonds", "category": "financial_market"},
    {"lane_id": "rates", "module": "rates", "sport_or_asset": "Rates", "category": "financial_market"},
    {"lane_id": "macro", "module": "macro", "sport_or_asset": "Macro", "category": "financial_market"},
    {"lane_id": "major_assets", "module": "major_assets", "sport_or_asset": "Major Assets", "category": "financial_market"},
    {"lane_id": "fx_currencies", "module": "fx_currencies", "sport_or_asset": "FX / Currencies", "category": "fx"},
    {"lane_id": "sportsbooks", "module": "sportsbooks", "sport_or_asset": "Sportsbooks", "category": "odds"},
    {"lane_id": "odds", "module": "odds", "sport_or_asset": "Odds", "category": "odds"},
    {"lane_id": "weather", "module": "weather", "sport_or_asset": "Weather", "category": "environment"},
    {"lane_id": "news_sentiment", "module": "news_sentiment", "sport_or_asset": "News / Sentiment", "category": "news_sentiment"},
    {"lane_id": "government_open_data", "module": "government_open_data", "sport_or_asset": "Government / Open Data", "category": "government_open_data"},
    {"lane_id": "transportation_logistics", "module": "transportation_logistics", "sport_or_asset": "Transportation / Logistics", "category": "transportation"},
    {"lane_id": "health_public_context", "module": "health_public_context", "sport_or_asset": "Health / Public Context", "category": "health_public_context"},
    {"lane_id": "security_ops", "module": "security_ops", "sport_or_asset": "Security / Ops", "category": "security_ops"},
    {"lane_id": "officials", "module": "officials", "sport_or_asset": "Officials", "category": "context"},
    {"lane_id": "injuries", "module": "injuries", "sport_or_asset": "Injuries", "category": "context"},
    {"lane_id": "lineups", "module": "lineups", "sport_or_asset": "Lineups", "category": "context"},
    {"lane_id": "schedules", "module": "schedules", "sport_or_asset": "Schedules", "category": "context"},
    {"lane_id": "news_context", "module": "news_context", "sport_or_asset": "News/Event Context", "category": "context"},
    {"lane_id": "basketball_nba", "module": "basketball_nba", "sport_or_asset": "NBA", "category": "sport"},
    {"lane_id": "basketball_wnba", "module": "basketball_wnba", "sport_or_asset": "WNBA", "category": "sport"},
    {"lane_id": "americanfootball_nfl", "module": "americanfootball_nfl", "sport_or_asset": "NFL", "category": "sport"},
    {"lane_id": "americanfootball_ncaaf", "module": "americanfootball_ncaaf", "sport_or_asset": "NCAAF", "category": "sport"},
    {"lane_id": "baseball_mlb", "module": "baseball_mlb", "sport_or_asset": "MLB", "category": "sport"},
    {"lane_id": "icehockey_nhl", "module": "icehockey_nhl", "sport_or_asset": "NHL", "category": "sport"},
    {"lane_id": "soccer", "module": "soccer", "sport_or_asset": "Soccer", "category": "sport"},
    {"lane_id": "tennis", "module": "tennis", "sport_or_asset": "Tennis", "category": "sport"},
    {"lane_id": "ufc_mma", "module": "ufc_mma", "sport_or_asset": "UFC/MMA", "category": "sport"},
    {"lane_id": "boxing", "module": "boxing", "sport_or_asset": "Boxing", "category": "sport"},
    {"lane_id": "golf", "module": "golf", "sport_or_asset": "Golf", "category": "sport"},
    {"lane_id": "basketball_ncaab", "module": "basketball_ncaab", "sport_or_asset": "NCAAB", "category": "sport"},
    {"lane_id": "basketball_ncaaw", "module": "basketball_ncaaw", "sport_or_asset": "NCAAW", "category": "sport"},
)

MODULE_ALIASES = {
    "nba": "basketball_nba",
    "wnba": "basketball_wnba",
    "nfl": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "mma": "ufc_mma",
    "ufc": "ufc_mma",
    "ncaab": "basketball_ncaab",
    "ncaaw": "basketball_ncaaw",
    "etfs": "ETFs",
    "etf": "ETFs",
    "prediction_market": "prediction_markets",
    "prediction_markets": "prediction_markets",
    "stock_pro": "institutional_stock_pro_analyst",
    "stock_analyst": "institutional_stock_pro_analyst",
    "institutional_stock_pro_analyst": "institutional_stock_pro_analyst",
    "crypto": "cryptocurrency_edge_lab",
    "cryptocurrency": "cryptocurrency_edge_lab",
    "cryptocurrency_edge_lab": "cryptocurrency_edge_lab",
    "fx": "fx_currencies",
    "currencies": "fx_currencies",
    "news": "news_sentiment",
    "sentiment": "news_sentiment",
    "government": "government_open_data",
    "open_data": "government_open_data",
    "transportation": "transportation_logistics",
    "travel": "transportation_logistics",
    "health": "health_public_context",
    "security": "security_ops",
}

PUBLIC_APIS_BASELINE_TOTAL_LANES = 30
PUBLIC_APIS_BASELINE_TOTAL_SOURCES = 85

STOCK_ANALYST_SCORING_DIMENSIONS = [
    "valuation_score",
    "profitability_score",
    "balance_sheet_score",
    "cash_flow_quality_score",
    "growth_quality_score",
    "earnings_revision_score",
    "earnings_surprise_score",
    "insider_activity_score",
    "institutional_ownership_score",
    "liquidity_score",
    "volatility_score",
    "drawdown_risk_score",
    "macro_sensitivity_score",
    "rates_sensitivity_score",
    "sector_relative_strength_score",
    "news_sentiment_score",
    "event_risk_score",
    "price_momentum_score",
    "mean_reversion_score",
    "technical_structure_score",
    "risk_adjusted_edge_score",
    "confidence_score",
    "analyst_review_priority_score",
]

CRYPTO_EDGE_SCORING_DIMENSIONS = [
    "crypto_liquidity_score",
    "exchange_quality_score",
    "spread_score",
    "volatility_score",
    "trend_score",
    "mean_reversion_score",
    "momentum_score",
    "funding_pressure_score",
    "open_interest_pressure_score",
    "onchain_activity_score",
    "dex_liquidity_score",
    "stablecoin_flow_score",
    "gas_fee_pressure_score",
    "whale_activity_proxy_score",
    "sentiment_score",
    "macro_risk_score",
    "correlation_risk_score",
    "drawdown_risk_score",
    "regime_score",
    "risk_adjusted_edge_score",
    "confidence_score",
    "review_priority_score",
]

CRYPTO_FORBIDDEN_ACTIONS = [
    "place_order",
    "market_order",
    "limit_order",
    "swap",
    "bridge",
    "stake",
    "lend",
    "borrow",
    "withdraw",
    "deposit",
    "transfer",
    "sign_transaction",
    "connect_wallet",
    "reveal_seed_phrase",
]

BROKER_FORBIDDEN_ACTIONS = ["place_order", "cancel_order", "modify_order", "trade", "withdraw", "deposit"]
BETTING_FORBIDDEN_ACTIONS = ["place_bet", "submit_order", "cancel_order", "modify_order", "deposit", "withdraw", "trade", "execute"]

SPORT_REQUIRED_INPUTS = [
    "schedule",
    "team_stats",
    "player_stats",
    "final_results",
    "stable_event_id",
]

ODDS_REQUIRED_INPUTS = [
    "event_id",
    "market_type",
    "selection",
    "odds",
    "line",
    "timestamp",
    "final_results",
]

FINANCIAL_REQUIRED_INPUTS = [
    "symbol",
    "price",
    "timestamp",
    "volume",
    "historical_prices",
    "final_price",
]

PREDICTION_REQUIRED_INPUTS = [
    "ticker",
    "market_status",
    "close_time",
    "bid_ask",
    "settlement_result",
]

CONTEXT_REQUIRED_INPUTS = ["event_id", "timestamp", "source_context", "stable_join_key"]
STOCK_ANALYST_REQUIRED_INPUTS = [
    "equity_price",
    "historical_prices",
    "fundamentals",
    "sec_filings",
    "earnings",
    "macro_context",
    "rates_context",
    "sector_context",
    "liquidity",
    "volatility",
    "news_sentiment",
]
CRYPTO_REQUIRED_INPUTS = [
    "spot_price",
    "ohlcv",
    "exchange_volume",
    "liquidity",
    "spread",
    "volatility",
    "onchain_signals",
    "macro_context",
    "forward_returns",
]
FX_REQUIRED_INPUTS = ["currency_pair", "fx_rate", "timestamp", "historical_rates", "macro_context"]
NEWS_REQUIRED_INPUTS = ["timestamp", "headline", "source", "entity", "sentiment", "event_context"]
TRANSPORT_REQUIRED_INPUTS = ["event_id", "location", "timestamp", "delay_status", "route_context"]
PUBLIC_CONTEXT_REQUIRED_INPUTS = ["timestamp", "location", "public_metric", "source_context", "stable_join_key"]
SECURITY_OPS_REQUIRED_INPUTS = ["timestamp", "indicator", "severity", "source_context", "remediation_context"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_inputs_for(category: str, lane_id: str) -> list[str]:
    if lane_id == "institutional_stock_pro_analyst":
        return list(STOCK_ANALYST_REQUIRED_INPUTS)
    if lane_id == "cryptocurrency_edge_lab":
        return list(CRYPTO_REQUIRED_INPUTS)
    if category == "sport":
        return list(SPORT_REQUIRED_INPUTS)
    if category == "odds":
        return list(ODDS_REQUIRED_INPUTS)
    if category == "financial_market":
        return list(FINANCIAL_REQUIRED_INPUTS)
    if category == "prediction_market":
        return list(PREDICTION_REQUIRED_INPUTS)
    if category == "fx":
        return list(FX_REQUIRED_INPUTS)
    if category == "news_sentiment":
        return list(NEWS_REQUIRED_INPUTS)
    if category == "transportation":
        return list(TRANSPORT_REQUIRED_INPUTS)
    if category in {"government_open_data", "health_public_context"}:
        return list(PUBLIC_CONTEXT_REQUIRED_INPUTS)
    if category == "security_ops":
        return list(SECURITY_OPS_REQUIRED_INPUTS)
    if lane_id == "weather":
        return ["event_id", "location", "timestamp", "temperature", "wind", "precipitation"]
    return list(CONTEXT_REQUIRED_INPUTS)


def _optional_inputs_for(category: str, lane_id: str) -> list[str]:
    if lane_id == "institutional_stock_pro_analyst":
        return [
            "ETF_market_data",
            "earnings_call_text",
            "insider_transactions",
            "institutional_ownership",
            "options_context",
            "position_sizing_simulation",
            "paper_only_portfolio_simulation",
            *technical_fields_for_market("stocks"),
        ]
    if lane_id == "cryptocurrency_edge_lab":
        return [
            "order_book_depth",
            "funding_rates",
            "open_interest",
            "dex_liquidity",
            "gas_fees",
            "stablecoin_flows",
            "whale_activity_proxy",
            "risk_asset_correlation",
            "regime_detection",
            "paper_only_strategy_replay",
            *technical_fields_for_market("crypto"),
        ]
    if category == "sport":
        return ["injuries", "lineups", "officials", "weather", "travel", "rest", "news_context"]
    if category == "financial_market":
        return ["fundamentals", "macro", "rates", "sector", "benchmarks", "corporate_actions"]
    if category == "prediction_market":
        return [
            "volume",
            "open_interest",
            "settlement_rules",
            "category",
            "event_metadata",
            *technical_fields_for_market("prediction_markets"),
        ]
    if category == "odds":
        return [
            "book_count",
            "consensus_line",
            "closing_line",
            "limits",
            "injuries",
            "weather",
            *technical_fields_for_market("sports_odds"),
        ]
    if category == "0dte_options" or "0dte" in lane_id:
        return [
            "underlying_symbol",
            "underlying_price",
            "trade_date",
            "expiration_date",
            "days_to_expiration",
            "minutes_to_expiration",
            "strike",
            "option_type",
            "call_put",
            "bid",
            "ask",
            "mid",
            "mark",
            "last_price",
            "volume",
            "open_interest",
            "implied_volatility",
            "delta",
            "gamma",
            "theta",
            "vega",
            "rho",
            "moneyness",
            "intrinsic_value",
            "extrinsic_value",
            "spread",
            "spread_percent",
            "premium",
            "risk_free_rate",
            *technical_fields_for_market("0dte_options"),
        ]
    return ["manual_notes", "confidence", "source_timestamp"]


def _default_coverage(**overrides: bool) -> dict[str, bool]:
    coverage = {
        "historical": False,
        "live": False,
        "schedules": False,
        "box_scores": False,
        "play_by_play": False,
        "player_stats": False,
        "team_stats": False,
        "injuries": False,
        "lineups": False,
        "officials": False,
        "odds": False,
        "weather": False,
        "fundamentals": False,
        "macro": False,
        "rates": False,
        "filings": False,
        "earnings": False,
        "news": False,
        "sentiment": False,
        "order_book": False,
        "funding": False,
        "open_interest": False,
        "onchain": False,
        "dex": False,
        "fx": False,
        "government": False,
        "transportation": False,
        "health": False,
        "security": False,
        "settlements": False,
        "final_results": False,
    }
    for key, value in overrides.items():
        if key in coverage:
            coverage[key] = bool(value)
    return coverage


def _source(
    *,
    source_id: str,
    source_name: str,
    lane_id: str,
    module: str | None = None,
    display_name: str | None = None,
    module_lane: str | None = None,
    source_category: str | None = None,
    source_access_type: str = "unknown",
    auth_type: str = "none",
    env_var_name: str | list[str] | None = None,
    https_supported: bool | None = True,
    cors_status: str = "unknown",
    current_phase_allowed: bool = False,
    future_source_candidate: bool = False,
    requires_account: bool = False,
    requires_api_key: bool = False,
    requires_oauth: bool = False,
    requires_terms_review: bool = True,
    requires_paid_subscription: bool = False,
    requires_execution_account: bool = False,
    requires_brokerage_account: bool = False,
    requires_sportsbook_account: bool = False,
    trial_only: bool = False,
    credit_card_required: bool = False,
    approval_status: str | None = None,
    adapter_status: str = "planned",
    coverage: dict[str, bool] | None = None,
    cadence: str = "unknown",
    backfill_depth: str = "",
    rate_limit_known: bool = False,
    rate_limit_notes: str = "",
    license_name: str = "unknown",
    terms_url_known: bool = False,
    terms_notes: str = "",
    commercial_use_unclear: bool = True,
    supported_use_cases: list[str] | None = None,
    model_input_mapping_status: str = "planned",
    outcome_mapping_status: str = "planned",
    backfill_mapping_status: str = "planned",
    model_inputs_supported: list[str] | None = None,
    missing_model_inputs: list[str] | None = None,
    join_keys: list[str] | None = None,
    outcome_fields_available: list[str] | None = None,
    historical_backfill_fields_available: list[str] | None = None,
    public_reference_url: str | None = None,
    forbidden_actions: list[str] | None = None,
    adapter_scope: str = "read_only_metadata_planning",
    raw_payload_persistence_allowed: bool = False,
    scoring_dimensions: list[str] | None = None,
    module_priority: str | None = None,
    module_status: str | None = None,
    verified_by: str | None = None,
    notes: list[str] | None = None,
    verified_at: str | None = None,
) -> dict[str, Any]:
    if source_access_type not in ACCESS_TYPES:
        source_access_type = "unknown"
    future_only = source_access_type in FUTURE_ONLY_ACCESS_TYPES or bool(future_source_candidate)
    if approval_status is None:
        approval_status = default_approval_status(
            source_access_type=source_access_type,
            future_source_candidate=future_only,
            requires_paid_subscription=requires_paid_subscription,
            requires_terms_review=requires_terms_review,
            current_phase_allowed=current_phase_allowed,
            verified_at=verified_at,
        )
    env_names = [env_var_name] if isinstance(env_var_name, str) else list(env_var_name or [])
    requires_api_key = bool(requires_api_key or env_names)
    budget_gate = build_budget_gate(
        source_access_type=source_access_type,
        requires_api_key=requires_api_key,
        requires_paid_subscription=bool(requires_paid_subscription or future_only),
        future_source_candidate=future_only,
        approval_status=approval_status,
    )
    current_phase_safe = bool(
        current_phase_allowed
        and approval_status == "approved_for_research"
        and verified_at
        and not future_only
        and not budget_gate["requires_budget_approval"]
        and not requires_paid_subscription
        and not requires_execution_account
        and not requires_brokerage_account
        and not requires_sportsbook_account
        and not trial_only
        and not credit_card_required
    )
    source = {
        "source_id": source_id,
        "source_name": source_name,
        "display_name": display_name or source_name,
        "lane_id": lane_id,
        "module_lane": module_lane or lane_id,
        "module": module or lane_id,
        "source_category": source_category or "uncategorized",
        "source_access_type": source_access_type,
        "auth_type": auth_type,
        "env_var_name": env_names[0] if env_names else None,
        "env_var_names": env_names,
        "https_supported": https_supported,
        "cors_status": cors_status,
        "current_phase_allowed": current_phase_safe,
        "future_source_candidate": bool(future_only),
        "requires_budget_approval": bool(budget_gate["requires_budget_approval"]),
        "verification_phase_allowed": bool(budget_gate["verification_phase_allowed"]),
        "call_budget_level": budget_gate["call_budget_level"],
        "max_provider_calls_default": int(budget_gate["max_provider_calls_default"]),
        "max_provider_calls_hard_cap": int(budget_gate["max_provider_calls_hard_cap"]),
        "paid_upgrade_required": bool(budget_gate["paid_upgrade_required"]),
        "paid_upgrade_allowed": False,
        "substantial_usage_allowed": False,
        "requires_account": bool(requires_account),
        "requires_api_key": bool(requires_api_key),
        "requires_oauth": bool(requires_oauth),
        "requires_terms_review": bool(requires_terms_review),
        "requires_provider_write": False,
        "requires_execution_account": bool(requires_execution_account),
        "requires_brokerage_account": bool(requires_brokerage_account),
        "requires_sportsbook_account": bool(requires_sportsbook_account),
        "requires_paid_subscription": bool(requires_paid_subscription or future_only),
        "trial_only": bool(trial_only),
        "credit_card_required": bool(credit_card_required),
        "approval_status": approval_status,
        "enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "human_approval_required": True,
        "paper_only": True,
        "adapter_status": adapter_status if adapter_status in {"not_started", "planned", "implemented", "verified", "disabled"} else "planned",
        "adapter_scope": adapter_scope,
        "raw_payload_persistence_allowed": bool(raw_payload_persistence_allowed),
        "forbidden_actions": list(forbidden_actions or []),
        "supported_use_cases": list(supported_use_cases or []),
        "model_input_mapping_status": model_input_mapping_status,
        "outcome_mapping_status": outcome_mapping_status,
        "backfill_mapping_status": backfill_mapping_status,
        "public_reference_url": public_reference_url,
        "module_priority": module_priority,
        "module_status": module_status,
        "scoring_dimensions": list(scoring_dimensions or []),
        "coverage": dict(coverage or _default_coverage()),
        "freshness": {
            "expected_update_cadence": cadence,
            "latency_notes": "",
            "backfill_depth": backfill_depth,
        },
        "limits": {
            "rate_limit_known": bool(rate_limit_known),
            "rate_limit_notes": rate_limit_notes,
            "daily_limit": None,
            "monthly_limit": None,
            "throttle_required": True,
            "cache_required": True,
        },
        "legal_terms": {
            "license": license_name,
            "terms_url_known": bool(terms_url_known),
            "terms_notes": terms_notes,
            "terms_caution": bool(requires_terms_review or commercial_use_unclear),
            "commercial_use_unclear": bool(commercial_use_unclear),
            "requires_manual_review": bool(requires_terms_review),
        },
        "model_mapping": {
            "supported_model_modules": [module or lane_id],
            "model_inputs_supported": list(model_inputs_supported or []),
            "missing_model_inputs": list(missing_model_inputs or []),
            "join_keys": list(join_keys or []),
            "outcome_fields_available": list(outcome_fields_available or []),
            "historical_backfill_fields_available": list(historical_backfill_fields_available or []),
        },
        "quality": {
            "source_reliability_score": None,
            "freshness_score": None,
            "coverage_score": None,
            "completeness_score": None,
            "join_quality_score": None,
            "model_input_fill_rate": None,
            "terms_risk_score": None,
            "rate_limit_risk_score": None,
            "historical_depth_score": None,
            "outcome_availability_score": None,
        },
        "notes": list(notes or []),
        "verified_at": verified_at,
        "verified_by": verified_by,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    source["quality"] = score_source(source)
    return source


def _coverage_for_source_category(category: str) -> dict[str, bool]:
    if category == "stock/fundamentals":
        return _default_coverage(historical=True, live=True, fundamentals=True, filings=True, earnings=True, final_results=True)
    if category == "finance":
        return _default_coverage(historical=True, live=True, final_results=True)
    if category == "macro/rates/bonds":
        return _default_coverage(historical=True, macro=True, rates=True, government=True, final_results=True)
    if category == "crypto":
        return _default_coverage(historical=True, live=True, order_book=True, funding=True, open_interest=True, onchain=True, dex=True, final_results=True)
    if category == "FX":
        return _default_coverage(historical=True, live=True, fx=True, macro=True, final_results=True)
    if category == "sports":
        return _default_coverage(historical=True, live=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True)
    if category == "betting/odds":
        return _default_coverage(historical=True, live=True, odds=True, settlements=True, final_results=True)
    if category == "news/sentiment":
        return _default_coverage(historical=True, live=True, news=True, sentiment=True)
    if category == "weather/environment":
        return _default_coverage(historical=True, live=True, weather=True, government=True)
    if category == "government/open data":
        return _default_coverage(historical=True, government=True, macro=True)
    if category == "transportation":
        return _default_coverage(historical=True, live=True, transportation=True, weather=True)
    if category == "health/public context":
        return _default_coverage(historical=True, health=True, government=True)
    if category == "security/ops":
        return _default_coverage(historical=True, live=True, security=True)
    return _default_coverage(historical=True)


def _model_inputs_for_source_category(category: str) -> list[str]:
    if category == "stock/fundamentals":
        return ["symbol", "equity_price", "historical_prices", "fundamentals", "sec_filings", "earnings", "valuation", "final_price"]
    if category == "finance":
        return ["symbol", "equity_price", "price", "timestamp", "volume", "historical_prices", "final_price"]
    if category == "macro/rates/bonds":
        return ["series_id", "timestamp", "macro_context", "rates_context", "historical_rates", "final_value"]
    if category == "crypto":
        return ["asset_symbol", "spot_price", "ohlcv", "exchange_volume", "order_book_depth", "liquidity", "spread", "volatility", "funding_rates", "open_interest", "onchain_signals", "dex_liquidity", "stablecoin_flows", "tvl", "gas_fees", "forward_returns"]
    if category == "FX":
        return ["currency_pair", "fx_rate", "timestamp", "historical_rates", "macro_context"]
    if category == "sports":
        return list(SPORT_REQUIRED_INPUTS)
    if category == "betting/odds":
        return list(ODDS_REQUIRED_INPUTS) + ["book_count", "consensus_line"]
    if category == "news/sentiment":
        return ["timestamp", "headline", "source", "entity", "sentiment", "event_context"]
    if category == "weather/environment":
        return ["event_id", "location", "timestamp", "temperature", "wind", "precipitation", "air_quality"]
    if category == "transportation":
        return list(TRANSPORT_REQUIRED_INPUTS)
    if category in {"government/open data", "health/public context"}:
        return list(PUBLIC_CONTEXT_REQUIRED_INPUTS)
    if category == "security/ops":
        return list(SECURITY_OPS_REQUIRED_INPUTS)
    return ["timestamp", "source_context", "stable_join_key"]


def _use_cases_for_source_category(category: str) -> list[str]:
    return {
        "stock/fundamentals": ["stock analyst planning", "valuation research", "earnings event context", "paper-only stock simulation"],
        "finance": ["market data normalization", "liquidity context", "volatility context", "paper-only price backtests"],
        "macro/rates/bonds": ["macro regime detection", "rates context", "inflation/labor context", "risk-asset correlation"],
        "crypto": ["edge-seeking crypto research", "risk-controlled replay", "calibration-backed forward-return labels", "paper-only strategy simulation"],
        "FX": ["USD strength context", "FX/macro regime features", "crypto/risk-asset cross-correlation", "sports travel context"],
        "sports": ["schedule/team/player context", "final result backfill", "small-sample adapter research"],
        "betting/odds": ["odds context", "prediction market settlement context", "calibration backfill", "read-only market data"],
        "news/sentiment": ["market sentiment", "stock event risk", "crypto sentiment", "sports news context", "macro shock detection"],
        "weather/environment": ["outdoor sports weather", "travel disruption", "climate anomaly context", "public environment context"],
        "government/open data": ["macro regime", "regulatory risk", "economic backtests", "public context enrichment"],
        "transportation": ["team travel fatigue", "flight disruption", "event attendance context", "logistics risk"],
        "health/public context": ["public-health context", "regulatory context", "aggregated public data enrichment"],
        "security/ops": ["secret leak prevention", "dependency vulnerability monitoring", "API ops security hardening"],
    }.get(category, ["registry research"])


def _join_keys_for_source_category(category: str) -> list[str]:
    if category in {"stock/fundamentals", "finance"}:
        return ["symbol", "date"]
    if category == "macro/rates/bonds":
        return ["series_id", "date"]
    if category == "crypto":
        return ["asset_symbol", "exchange", "timestamp"]
    if category == "FX":
        return ["currency_pair", "date"]
    if category == "sports":
        return ["event_id", "team_id", "date"]
    if category == "betting/odds":
        return ["event_id", "market_type", "selection", "timestamp"]
    if category in {"weather/environment", "transportation", "government/open data", "health/public context"}:
        return ["location", "date", "source_id"]
    if category == "news/sentiment":
        return ["entity", "timestamp", "source"]
    return ["source_id", "timestamp"]


def _source_spec(source_id: str, display_name: str, lane_id: str, category: str, url: str, *, access: str = "open_public", auth: str = "none", env: str | list[str] | None = None, oauth: bool = False, account: bool = False, paid: bool = False, future: bool = False, terms: bool = True, cadence: str = "daily", adapter_status: str = "not_started", notes: list[str] | None = None, forbidden_actions: list[str] | None = None, supported_use_cases: list[str] | None = None, inputs: list[str] | None = None) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "display_name": display_name,
        "lane_id": lane_id,
        "source_category": category,
        "public_reference_url": url,
        "source_access_type": access,
        "auth_type": auth,
        "env_var_name": env,
        "requires_oauth": oauth,
        "requires_account": bool(account or env or oauth),
        "requires_paid_subscription": paid,
        "future_source_candidate": future,
        "requires_terms_review": terms,
        "cadence": cadence,
        "adapter_status": adapter_status,
        "notes": list(notes or []),
        "forbidden_actions": list(forbidden_actions or []),
        "supported_use_cases": list(supported_use_cases or _use_cases_for_source_category(category)),
        "model_inputs_supported": list(inputs or _model_inputs_for_source_category(category)),
    }


PUBLIC_API_SOURCE_SPECS: tuple[dict[str, Any], ...] = (
    # Stock, ETF, market data, fundamentals, identifiers.
    _source_spec("alpha_vantage_market_data", "Alpha Vantage", "institutional_stock_pro_analyst", "finance", "https://www.alphavantage.co/", access="free_key", auth="api_key", env="ALPHA_VANTAGE_API_KEY"),
    _source_spec("financial_modeling_prep_market_data", "Financial Modeling Prep", "institutional_stock_pro_analyst", "stock/fundamentals", "https://financialmodelingprep.com/", access="free_tier", auth="api_key", env="FINANCIAL_MODELING_PREP_API_KEY"),
    _source_spec("finnhub_market_data", "Finnhub", "institutional_stock_pro_analyst", "finance", "https://finnhub.io/", access="free_tier", auth="api_key", env="FINNHUB_API_KEY"),
    _source_spec("marketstack_market_data", "Marketstack", "institutional_stock_pro_analyst", "finance", "https://marketstack.com/", access="free_tier", auth="api_key", env="MARKETSTACK_API_KEY"),
    _source_spec("twelve_data_market_data", "Twelve Data", "institutional_stock_pro_analyst", "finance", "https://twelvedata.com/", access="free_tier", auth="api_key", env="TWELVE_DATA_API_KEY"),
    _source_spec("iex_cloud_market_data", "IEX Cloud", "institutional_stock_pro_analyst", "finance", "https://iexcloud.io/", access="free_tier", auth="api_key", env="IEX_CLOUD_API_KEY"),
    _source_spec("polygon_market_data", "Polygon", "institutional_stock_pro_analyst", "finance", "https://polygon.io/", access="free_tier", auth="api_key", env="POLYGON_API_KEY"),
    _source_spec("stockdata_market_data", "StockData", "institutional_stock_pro_analyst", "finance", "https://www.stockdata.org/", access="free_tier", auth="api_key", env="STOCKDATA_API_KEY"),
    _source_spec("tradier_market_data_only", "Tradier market data", "institutional_stock_pro_analyst", "finance", "https://developer.tradier.com/", access="free_tier", auth="access_token", env="TRADIER_ACCESS_TOKEN", forbidden_actions=BROKER_FORBIDDEN_ACTIONS, notes=["Market-data-only candidate; brokerage/order actions are forbidden."]),
    _source_spec("alpaca_market_data_only", "Alpaca market data", "institutional_stock_pro_analyst", "finance", "https://alpaca.markets/data", access="free_tier", auth="api_key_pair", env=["ALPACA_MARKET_DATA_KEY", "ALPACA_MARKET_DATA_SECRET"], forbidden_actions=BROKER_FORBIDDEN_ACTIONS, notes=["Market-data-only candidate; trading account actions are forbidden."]),
    _source_spec("nasdaq_data_link", "Nasdaq Data Link", "institutional_stock_pro_analyst", "stock/fundamentals", "https://data.nasdaq.com/", access="free_tier", auth="api_key", env="NASDAQ_DATA_LINK_API_KEY"),
    _source_spec("yfinance_wrapper", "Yahoo Finance / yfinance wrapper", "institutional_stock_pro_analyst", "finance", "https://pypi.org/project/yfinance/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("stooq_market_data", "Stooq", "institutional_stock_pro_analyst", "finance", "https://stooq.com/", access="open_public", auth="none"),
    _source_spec("tiingo_market_data", "Tiingo", "institutional_stock_pro_analyst", "finance", "https://www.tiingo.com/", access="free_tier", auth="api_key", env="TIINGO_API_KEY"),
    _source_spec("eodhd_market_data", "EOD Historical Data", "institutional_stock_pro_analyst", "finance", "https://eodhd.com/", access="free_tier", auth="api_key", env="EODHD_API_KEY"),
    _source_spec("sec_edgar_data", "SEC EDGAR Data", "institutional_stock_pro_analyst", "stock/fundamentals", "https://www.sec.gov/edgar/sec-api-documentation", access="open_public", auth="user_agent", env="SEC_USER_AGENT", terms=False, inputs=["symbol", "cik", "sec_filings", "fundamentals", "earnings"]),
    _source_spec("sec_company_facts", "SEC Company Facts", "institutional_stock_pro_analyst", "stock/fundamentals", "https://www.sec.gov/edgar/sec-api-documentation", access="open_public", auth="user_agent", env="SEC_USER_AGENT", terms=False, inputs=["symbol", "cik", "fundamentals", "sec_filings"]),
    _source_spec("sec_submissions_api", "SEC Submissions API", "institutional_stock_pro_analyst", "stock/fundamentals", "https://www.sec.gov/edgar/sec-api-documentation", access="open_public", auth="user_agent", env="SEC_USER_AGENT", terms=False, inputs=["symbol", "cik", "sec_filings"]),
    _source_spec("openfigi_identifiers", "OpenFIGI", "institutional_stock_pro_analyst", "stock/fundamentals", "https://www.openfigi.com/api", access="free_key", auth="api_key", env="OPENFIGI_API_KEY", inputs=["symbol", "figi", "security_identifier"]),
    _source_spec("aletheia_candidate", "Aletheia", "institutional_stock_pro_analyst", "stock/fundamentals", "https://aletheiaapi.com/", access="free_tier", auth="api_key"),
    _source_spec("opencorporates_company_context", "OpenCorporates", "institutional_stock_pro_analyst", "stock/fundamentals", "https://opencorporates.com/info/about_api", access="free_tier", auth="api_key", env="OPENCORPORATES_API_KEY"),
    _source_spec("fmp_fundamentals", "Financial Modeling Prep fundamentals", "institutional_stock_pro_analyst", "stock/fundamentals", "https://financialmodelingprep.com/developer/docs/", access="free_tier", auth="api_key", env="FINANCIAL_MODELING_PREP_API_KEY"),
    _source_spec("alpha_vantage_fundamentals", "Alpha Vantage fundamentals", "institutional_stock_pro_analyst", "stock/fundamentals", "https://www.alphavantage.co/documentation/", access="free_key", auth="api_key", env="ALPHA_VANTAGE_API_KEY"),
    _source_spec("finnhub_fundamentals", "Finnhub fundamentals", "institutional_stock_pro_analyst", "stock/fundamentals", "https://finnhub.io/docs/api", access="free_tier", auth="api_key", env="FINNHUB_API_KEY"),
    # Macro, rates, bonds, government, banks.
    _source_spec("fred_macro_rates", "FRED", "macro", "macro/rates/bonds", "https://fred.stlouisfed.org/docs/api/fred/", access="free_key", auth="api_key", env="FRED_API_KEY", terms=False),
    _source_spec("us_treasury_fiscaldata", "U.S. Treasury FiscalData", "bonds", "macro/rates/bonds", "https://fiscaldata.treasury.gov/api-documentation/", access="open_public", auth="none", terms=False),
    _source_spec("treasury_yield_data", "Treasury yield data", "rates", "macro/rates/bonds", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates", access="open_public", auth="none", terms=False),
    _source_spec("data_gov", "Data.gov", "government_open_data", "government/open data", "https://api.data.gov/", access="free_key", auth="api_key", env="DATA_GOV_API_KEY", terms=False),
    _source_spec("world_bank_open_data", "World Bank", "macro", "macro/rates/bonds", "https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information", access="open_public", auth="none", terms=False),
    _source_spec("census_gov", "Census.gov", "government_open_data", "government/open data", "https://www.census.gov/data/developers.html", access="free_key", auth="api_key", env="CENSUS_API_KEY", terms=False),
    _source_spec("data_usa", "Data USA", "government_open_data", "government/open data", "https://datausa.io/about/api/", access="open_public", auth="none", terms=False),
    _source_spec("federal_reserve_datasets", "Federal Reserve datasets", "macro", "macro/rates/bonds", "https://www.federalreserve.gov/data.htm", access="open_public", auth="none", terms=False),
    _source_spec("brazil_central_bank_open_data", "Brazil Central Bank Open Data", "macro", "macro/rates/bonds", "https://dadosabertos.bcb.gov.br/", access="open_public", auth="none", terms=True),
    _source_spec("bank_negara_malaysia_open_data", "Bank Negara Malaysia Open Data", "macro", "macro/rates/bonds", "https://api.bnm.gov.my/portal", access="open_public", auth="none", terms=True),
    _source_spec("ecb_public_data", "European Central Bank public data", "macro", "macro/rates/bonds", "https://data.ecb.europa.eu/help/api/overview", access="open_public", auth="none", terms=True),
    _source_spec("bank_of_england_public_data", "Bank of England public data", "macro", "macro/rates/bonds", "https://www.bankofengland.co.uk/boeapps/database/", access="open_public", auth="none", terms=True),
    # Crypto market/on-chain/context.
    _source_spec("coingecko_crypto_prices", "CoinGecko", "cryptocurrency_edge_lab", "crypto", "https://www.coingecko.com/en/api", access="open_public", auth="none", cadence="near_live"),
    _source_spec("coincap_crypto_prices", "CoinCap", "cryptocurrency_edge_lab", "crypto", "https://docs.coincap.io/", access="open_public", auth="none", cadence="near_live"),
    _source_spec("coinpaprika_crypto_prices", "CoinPaprika", "cryptocurrency_edge_lab", "crypto", "https://api.coinpaprika.com/", access="open_public", auth="none", cadence="near_live"),
    _source_spec("coinlayer_crypto_prices", "Coinlayer", "cryptocurrency_edge_lab", "crypto", "https://coinlayer.com/", access="free_tier", auth="api_key", env="COINLAYER_API_KEY"),
    _source_spec("cryptocompare_crypto_prices", "CryptoCompare", "cryptocurrency_edge_lab", "crypto", "https://min-api.cryptocompare.com/documentation", access="free_tier", auth="api_key", env="CRYPTOCOMPARE_API_KEY"),
    _source_spec("coinmarketcap_free_tier", "CoinMarketCap free tier", "cryptocurrency_edge_lab", "crypto", "https://coinmarketcap.com/api/", access="free_tier", auth="api_key", env="COINMARKETCAP_API_KEY"),
    _source_spec("binance_public_market_data", "Binance public market data", "cryptocurrency_edge_lab", "crypto", "https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints", access="open_public", auth="optional_readonly_key", env="BINANCE_API_KEY_READONLY", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("coinbase_public_market_data", "Coinbase public market data", "cryptocurrency_edge_lab", "crypto", "https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproducts", access="open_public", auth="optional_readonly_key", env="COINBASE_API_KEY_READONLY", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("kraken_public_market_data", "Kraken public market data", "cryptocurrency_edge_lab", "crypto", "https://docs.kraken.com/api/docs/rest-api/get-ticker-information/", access="open_public", auth="optional_readonly_key", env="KRAKEN_API_KEY_READONLY", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("bitfinex_public_market_data", "Bitfinex public market data", "cryptocurrency_edge_lab", "crypto", "https://docs.bitfinex.com/reference/rest-public-ticker", access="open_public", auth="none", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("okx_public_market_data", "OKX public market data", "cryptocurrency_edge_lab", "crypto", "https://www.okx.com/docs-v5/en/", access="open_public", auth="optional_readonly_key", env="OKX_API_KEY_READONLY", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("kucoin_public_market_data", "KuCoin public market data", "cryptocurrency_edge_lab", "crypto", "https://www.kucoin.com/docs/rest/spot-trading/market-data/get-symbols-list", access="open_public", auth="optional_readonly_key", env="KUCOIN_API_KEY_READONLY", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("bybit_public_market_data", "Bybit public market data", "cryptocurrency_edge_lab", "crypto", "https://bybit-exchange.github.io/docs/v5/market/instrument", access="open_public", auth="optional_readonly_key", env="BYBIT_API_KEY_READONLY", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("deribit_public_data", "Deribit public data", "cryptocurrency_edge_lab", "crypto", "https://docs.deribit.com/", access="open_public", auth="none", cadence="near_live", forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("coinapi_free_tier", "CoinAPI", "cryptocurrency_edge_lab", "crypto", "https://www.coinapi.io/", access="free_tier", auth="api_key", env="COINAPI_KEY"),
    _source_spec("etherscan_onchain", "Etherscan", "cryptocurrency_edge_lab", "crypto", "https://docs.etherscan.io/", access="free_key", auth="api_key", env="ETHERSCAN_API_KEY", inputs=["asset_symbol", "onchain_signals", "gas_fees", "stablecoin_flows"]),
    _source_spec("blockchair_onchain", "Blockchair", "cryptocurrency_edge_lab", "crypto", "https://blockchair.com/api/docs", access="free_tier", auth="api_key", env="BLOCKCHAIR_API_KEY", inputs=["asset_symbol", "onchain_signals"]),
    _source_spec("blockchain_com_public_data", "Blockchain.com public data", "cryptocurrency_edge_lab", "crypto", "https://www.blockchain.com/explorer/api", access="open_public", auth="none", inputs=["asset_symbol", "onchain_signals"]),
    _source_spec("solana_json_rpc", "Solana JSON RPC", "cryptocurrency_edge_lab", "crypto", "https://solana.com/docs/rpc", access="open_public", auth="none", inputs=["asset_symbol", "onchain_signals"]),
    _source_spec("the_graph", "The Graph", "cryptocurrency_edge_lab", "crypto", "https://thegraph.com/docs/en/", access="free_tier", auth="api_key", inputs=["asset_symbol", "onchain_signals", "dex_liquidity", "tvl"]),
    _source_spec("defillama", "DeFiLlama", "cryptocurrency_edge_lab", "crypto", "https://defillama.com/docs/api", access="open_public", auth="none", inputs=["asset_symbol", "tvl", "dex_liquidity", "stablecoin_flows"]),
    _source_spec("zero_x", "0x", "cryptocurrency_edge_lab", "crypto", "https://0x.org/docs/api", access="free_tier", auth="api_key", inputs=["asset_symbol", "dex_liquidity", "spread"], forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("one_inch", "1inch", "cryptocurrency_edge_lab", "crypto", "https://portal.1inch.dev/documentation", access="free_tier", auth="api_key", inputs=["asset_symbol", "dex_liquidity", "spread"], forbidden_actions=CRYPTO_FORBIDDEN_ACTIONS),
    _source_spec("covalent", "Covalent", "cryptocurrency_edge_lab", "crypto", "https://www.covalenthq.com/docs/api/", access="free_tier", auth="api_key", env="COVALENT_API_KEY", inputs=["asset_symbol", "onchain_signals"]),
    _source_spec("alchemy_ethereum", "Alchemy Ethereum", "cryptocurrency_edge_lab", "crypto", "https://docs.alchemy.com/reference/ethereum-api-quickstart", access="free_tier", auth="api_key", env="ALCHEMY_API_KEY", inputs=["asset_symbol", "onchain_signals"]),
    _source_spec("infura_ethereum", "Infura", "cryptocurrency_edge_lab", "crypto", "https://docs.infura.io/", access="free_tier", auth="api_key", env="INFURA_API_KEY", inputs=["asset_symbol", "onchain_signals"]),
    _source_spec("moralis", "Moralis", "cryptocurrency_edge_lab", "crypto", "https://docs.moralis.com/web3-data-api/evm/reference", access="free_tier", auth="api_key", env="MORALIS_API_KEY", inputs=["asset_symbol", "onchain_signals"]),
)


PUBLIC_API_SOURCE_SPECS += (
    # FX.
    _source_spec("frankfurter_fx", "Frankfurter", "fx_currencies", "FX", "https://www.frankfurter.app/docs/", access="open_public", auth="none"),
    _source_spec("currency_api_fx", "Currency-api", "fx_currencies", "FX", "https://currencyapi.com/docs", access="free_tier", auth="api_key", env="EXCHANGERATE_API_KEY"),
    _source_spec("exchangerate_api", "ExchangeRate-API", "fx_currencies", "FX", "https://www.exchangerate-api.com/docs/overview", access="free_tier", auth="api_key", env="EXCHANGERATE_API_KEY"),
    _source_spec("exchangerate_host", "Exchangerate.host", "fx_currencies", "FX", "https://exchangerate.host/documentation", access="free_tier", auth="api_key"),
    _source_spec("currencyfreaks", "CurrencyFreaks", "fx_currencies", "FX", "https://currencyfreaks.com/documentation.html", access="free_tier", auth="api_key", env="CURRENCYFREAKS_API_KEY"),
    _source_spec("currencyscoop", "CurrencyScoop", "fx_currencies", "FX", "https://currencyscoop.com/api-documentation", access="free_tier", auth="api_key", env="CURRENCYSCOOP_API_KEY"),
    _source_spec("freeforexapi", "FreeForexAPI", "fx_currencies", "FX", "https://www.freeforexapi.com/Home/Api", access="open_public", auth="none"),
    _source_spec("fixer_fx", "Fixer", "fx_currencies", "FX", "https://fixer.io/documentation", access="free_tier", auth="api_key", env="FIXER_API_KEY"),
    _source_spec("national_bank_of_poland_fx", "National Bank of Poland", "fx_currencies", "FX", "https://api.nbp.pl/en.html", access="open_public", auth="none", terms=True),
    _source_spec("bank_of_russia_fx", "Bank of Russia", "fx_currencies", "FX", "https://www.cbr.ru/development/SXML/", access="open_public", auth="none", terms=True),
    _source_spec("ecb_fx_reference_rates", "European Central Bank FX reference rates", "fx_currencies", "FX", "https://www.ecb.europa.eu/stats/eurofxref/", access="open_public", auth="none", terms=True),
    # Sports.
    _source_spec("collegefootballdata_ncaaf", "CollegeFootballData", "americanfootball_ncaaf", "sports", "https://collegefootballdata.com/", access="free_key", auth="api_key", env="CFBD_API_KEY"),
    _source_spec("sportsdataverse_cfb", "SportsDataverse CFB", "americanfootball_ncaaf", "sports", "https://sportsdataverse.org/", access="open_dataset", auth="none"),
    _source_spec("espn_cfb_public_wrapper", "ESPN CFB public wrapper candidate", "americanfootball_ncaaf", "sports", "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("sportdata_ncaaf", "SportData NCAAF", "americanfootball_ncaaf", "sports", "https://sportdataapi.com/", access="free_tier", auth="api_key", env="SPORTDATA_API_KEY"),
    _source_spec("nflverse", "nflverse", "americanfootball_nfl", "sports", "https://nflverse.nflverse.com/", access="open_dataset", auth="none"),
    _source_spec("nflfastr", "nflfastR", "americanfootball_nfl", "sports", "https://www.nflfastr.com/", access="open_dataset", auth="none"),
    _source_spec("nflreadr", "nflreadr", "americanfootball_nfl", "sports", "https://nflreadr.nflverse.com/", access="open_dataset", auth="none"),
    _source_spec("espn_nfl_public_wrapper", "ESPN NFL public wrapper candidate", "americanfootball_nfl", "sports", "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("sportdata_nfl", "SportData NFL", "americanfootball_nfl", "sports", "https://sportdataapi.com/", access="free_tier", auth="api_key", env="SPORTDATA_API_KEY"),
    _source_spec("balldontlie_nba", "balldontlie", "basketball_nba", "sports", "https://www.balldontlie.io/", access="free_tier", auth="api_key"),
    _source_spec("nba_api", "nba_api", "basketball_nba", "sports", "https://github.com/swar/nba_api", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("hoopr_nba", "hoopR NBA", "basketball_nba", "sports", "https://hoopr.sportsdataverse.org/", access="open_dataset", auth="none"),
    _source_spec("espn_nba_public_wrapper", "ESPN NBA public wrapper candidate", "basketball_nba", "sports", "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("sportdata_nba", "SportData NBA", "basketball_nba", "sports", "https://sportdataapi.com/", access="free_tier", auth="api_key", env="SPORTDATA_API_KEY"),
    _source_spec("wehoop_wnba", "wehoop", "basketball_wnba", "sports", "https://wehoop.sportsdataverse.org/", access="open_dataset", auth="none"),
    _source_spec("wnba_stats_wrapper", "WNBA stats wrapper candidate", "basketball_wnba", "sports", "https://stats.wnba.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("espn_wnba_public_wrapper", "ESPN WNBA public wrapper candidate", "basketball_wnba", "sports", "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("mlb_stats_api", "MLB Stats API", "baseball_mlb", "sports", "https://statsapi.mlb.com/api/", access="open_public", auth="none"),
    _source_spec("pybaseball", "pybaseball", "baseball_mlb", "sports", "https://github.com/jldbc/pybaseball", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("baseball_savant_wrapper", "Baseball Savant wrapper candidate", "baseball_mlb", "sports", "https://baseballsavant.mlb.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("retrosheet", "Retrosheet", "baseball_mlb", "sports", "https://www.retrosheet.org/", access="open_dataset", auth="none"),
    _source_spec("lahman_database", "Lahman database", "baseball_mlb", "sports", "https://github.com/chadwickbureau/baseballdatabank", access="open_dataset", auth="none"),
    _source_spec("fangraphs_wrapper", "FanGraphs wrapper candidate", "baseball_mlb", "sports", "https://www.fangraphs.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("nhl_public_api", "NHL public API references", "icehockey_nhl", "sports", "https://api-web.nhle.com/", access="open_public", auth="none"),
    _source_spec("nhl_records_stats", "NHL Records and Stats", "icehockey_nhl", "sports", "https://records.nhl.com/site/api", access="open_public", auth="none"),
    _source_spec("espn_nhl_public_wrapper", "ESPN NHL public wrapper candidate", "icehockey_nhl", "sports", "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("sportdata_nhl", "SportData NHL", "icehockey_nhl", "sports", "https://sportdataapi.com/", access="free_tier", auth="api_key", env="SPORTDATA_API_KEY"),
    _source_spec("football_data", "Football-Data", "soccer", "sports", "https://www.football-data.org/documentation/quickstart", access="free_key", auth="api_key", env="FOOTBALL_DATA_API_KEY"),
    _source_spec("api_football", "API-FOOTBALL", "soccer", "sports", "https://www.api-football.com/documentation-v3", access="free_tier", auth="api_key", env="API_FOOTBALL_API_KEY"),
    _source_spec("worldfootballr", "worldfootballR", "soccer", "sports", "https://jaseziv.github.io/worldfootballR/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("openfootball", "openfootball", "soccer", "sports", "https://github.com/openfootball", access="open_dataset", auth="none"),
    _source_spec("openligadb", "OpenLigaDB", "soccer", "sports", "https://www.openligadb.de/", access="open_public", auth="none"),
    _source_spec("scorebat", "Scorebat", "soccer", "sports", "https://www.scorebat.com/video-api/", access="open_public", auth="none"),
    _source_spec("football_standings", "Football Standings", "soccer", "sports", "https://github.com/openfootball/football.json", access="open_dataset", auth="none"),
    _source_spec("sportmonks_football", "Sportmonks Football", "soccer", "sports", "https://docs.sportmonks.com/football", access="free_tier", auth="api_key", env="SPORTMONKS_FOOTBALL_API_KEY"),
    _source_spec("understat_wrapper", "Understat wrapper candidate", "soccer", "sports", "https://understat.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("fbref_wrapper", "FBref wrapper candidate", "soccer", "sports", "https://fbref.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("fotmob_wrapper", "Fotmob wrapper candidate", "soccer", "sports", "https://www.fotmob.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("jeff_sackmann_tennis_atp", "Jeff Sackmann tennis_atp", "tennis", "sports", "https://github.com/JeffSackmann/tennis_atp", access="open_dataset", auth="none"),
    _source_spec("jeff_sackmann_tennis_wta", "Jeff Sackmann tennis_wta", "tennis", "sports", "https://github.com/JeffSackmann/tennis_wta", access="open_dataset", auth="none"),
    _source_spec("match_charting_project", "Match Charting Project", "tennis", "sports", "https://github.com/JeffSackmann/tennis_MatchChartingProject", access="open_dataset", auth="none"),
    _source_spec("ufcstats_wrapper", "UFCStats scraper candidates", "ufc_mma", "sports", "http://ufcstats.com/statistics/events/completed", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("scrape_ufc_stats", "scrape_ufc_stats", "ufc_mma", "sports", "https://github.com/WarrierRajeev/scrape_ufc_stats", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("ufc_stats_crawler", "ufc-stats-crawler", "ufc_mma", "sports", "https://github.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("ufcscraper", "UFCscraper", "ufc_mma", "sports", "https://github.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("open_boxing", "Open Boxing", "boxing", "sports", "https://github.com/open-source-sports/", access="unknown", auth="none"),
    _source_spec("public_boxing_datasets", "public boxing datasets", "boxing", "sports", "https://www.kaggle.com/datasets", access="unknown", auth="none"),
    _source_spec("boxing_future_vendor_candidate", "Boxing future vendor candidate", "boxing", "sports", "https://www.sportradar.com/", access="institutional_vendor_candidate", auth="vendor_contract", future=True, paid=True),
    _source_spec("golfastr", "golfastR", "golf", "sports", "https://github.com/sportsdataverse/golfastR", access="open_dataset", auth="none"),
    _source_spec("opengolfapi", "OpenGolfAPI", "golf", "sports", "https://opengolfapi.com/", access="free_tier", auth="api_key"),
    _source_spec("espn_golf_wrapper", "ESPN golf wrapper candidate", "golf", "sports", "https://site.api.espn.com/apis/site/v2/sports/golf/scoreboard", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("owgr_public_data", "OWGR public data if terms-safe", "golf", "sports", "https://www.owgr.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("pga_data_candidates", "PGA data candidates", "golf", "sports", "https://www.pgatour.com/", access="public_wrapper_with_terms_review", auth="none"),
    _source_spec("cfl_api", "CFL API", "americanfootball_nfl", "sports", "https://www.cfl.ca/", access="free_tier", auth="api_key", env="CFL_API_KEY"),
    _source_spec("ergast_f1", "Ergast F1", "schedules", "sports", "https://ergast.com/mrd/", access="open_public", auth="none"),
    _source_spec("racinghub", "RacingHub", "schedules", "sports", "https://racinghub.io/", access="free_tier", auth="api_key"),
    _source_spec("squiggle_afl", "Squiggle", "schedules", "sports", "https://api.squiggle.com.au/", access="open_public", auth="none"),
    _source_spec("suredbits", "SuredBits", "odds", "betting/odds", "https://suredbits.com/", access="free_tier", auth="api_key"),
    _source_spec("thesportsdb", "TheSportsDB", "schedules", "sports", "https://www.thesportsdb.com/api.php", access="free_key", auth="api_key", env="THESPORTSDB_API_KEY"),
    _source_spec("sport_list_data", "Sport List & Data", "schedules", "sports", "https://github.com/openfootball", access="open_dataset", auth="none"),
    _source_spec("sport_places", "Sport Places", "schedules", "sports", "https://www.openstreetmap.org/", access="open_public", auth="none"),
)


PUBLIC_API_SOURCE_SPECS += (
    # Betting, odds, prediction markets.
    _source_spec("kalshi_public_market_data_registry", "Kalshi public market data", "kalshi", "betting/odds", "https://docs.kalshi.com/", access="open_public", auth="optional_readonly_key", env="KALSHI_READONLY_API_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("polymarket_gamma_api_registry", "Polymarket Gamma API", "polymarket", "betting/odds", "https://docs.polymarket.com/", access="open_public", auth="optional_key", env="POLYMARKET_API_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("polymarket_data_api_registry", "Polymarket Data API", "polymarket", "betting/odds", "https://docs.polymarket.com/", access="open_public", auth="optional_key", env="POLYMARKET_API_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("manifold_markets", "Manifold Markets", "prediction_markets", "betting/odds", "https://docs.manifold.markets/api", access="open_public", auth="none", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("metaculus_public_data", "Metaculus public data", "prediction_markets", "betting/odds", "https://www.metaculus.com/api2/", access="open_public", auth="none", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("predictit_public_data", "PredictIt public data", "prediction_markets", "betting/odds", "https://www.predictit.org/api/marketdata/all/", access="open_public", auth="none", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("the_odds_api", "The Odds API", "odds", "betting/odds", "https://the-odds-api.com/liveapi/guides/v4/", access="free_key", auth="api_key", env="THE_ODDS_API_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("sportsgameodds", "SportsGameOdds", "odds", "betting/odds", "https://sportsgameodds.com/", access="free_tier", auth="api_key", env="SPORTSGAMEODDS_API_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("odds_api_io", "Odds-API.io", "odds", "betting/odds", "https://odds-api.io/", access="free_tier", auth="api_key", env="ODDS_API_IO_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("oddsmagnet", "Oddsmagnet", "odds", "betting/odds", "https://oddsmagnet.com/", access="free_tier", auth="api_key", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("cloudbet_odds_only", "Cloudbet odds only", "odds", "betting/odds", "https://www.cloudbet.com/api/", access="free_tier", auth="api_key", env="CLOUDBET_API_KEY", forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    _source_spec("sharp_sportsbook_terms_safe", "Existing Sharp sportsbook source if terms-safe", "sportsbooks", "betting/odds", "https://www.sharpsports.com/", access="sportsbook_account_candidate", auth="account", future=True, forbidden_actions=BETTING_FORBIDDEN_ACTIONS),
    # News and text.
    _source_spec("marketaux", "MarketAux", "news_sentiment", "news/sentiment", "https://www.marketaux.com/documentation", access="free_tier", auth="api_key", env="MARKETAUX_API_KEY"),
    _source_spec("newsapi", "NewsAPI", "news_sentiment", "news/sentiment", "https://newsapi.org/docs", access="free_key", auth="api_key", env="NEWSAPI_KEY"),
    _source_spec("newsdata", "NewsData", "news_sentiment", "news/sentiment", "https://newsdata.io/documentation", access="free_tier", auth="api_key", env="NEWSDATA_API_KEY"),
    _source_spec("gnews", "GNews", "news_sentiment", "news/sentiment", "https://gnews.io/docs/v4", access="free_tier", auth="api_key", env="GNEWS_API_KEY"),
    _source_spec("mediastack", "Mediastack", "news_sentiment", "news/sentiment", "https://mediastack.com/documentation", access="free_tier", auth="api_key", env="MEDIASTACK_API_KEY"),
    _source_spec("thenews", "TheNews", "news_sentiment", "news/sentiment", "https://www.thenewsapi.com/documentation", access="free_tier", auth="api_key", env="THENEWS_API_KEY"),
    _source_spec("currents", "Currents", "news_sentiment", "news/sentiment", "https://currentsapi.services/en/docs/", access="free_tier", auth="api_key", env="CURRENTS_API_KEY"),
    _source_spec("associated_press", "Associated Press", "news_sentiment", "news/sentiment", "https://developer.ap.org/", access="free_tier", auth="api_key", env="AP_API_KEY"),
    _source_spec("new_york_times", "New York Times", "news_sentiment", "news/sentiment", "https://developer.nytimes.com/apis", access="free_key", auth="api_key", env="NYT_API_KEY"),
    _source_spec("the_guardian", "The Guardian", "news_sentiment", "news/sentiment", "https://open-platform.theguardian.com/documentation/", access="free_key", auth="api_key", env="GUARDIAN_API_KEY"),
    _source_spec("finnhub_news", "Finnhub news", "news_sentiment", "news/sentiment", "https://finnhub.io/docs/api/news", access="free_tier", auth="api_key", env="FINNHUB_API_KEY"),
    _source_spec("alpha_vantage_news_sentiment", "Alpha Vantage news sentiment", "news_sentiment", "news/sentiment", "https://www.alphavantage.co/documentation/", access="free_key", auth="api_key", env="ALPHA_VANTAGE_API_KEY"),
    _source_spec("fmp_news", "Financial Modeling Prep news", "news_sentiment", "news/sentiment", "https://financialmodelingprep.com/developer/docs/", access="free_tier", auth="api_key", env="FINANCIAL_MODELING_PREP_API_KEY"),
    _source_spec("meaningcloud", "MeaningCloud", "news_sentiment", "news/sentiment", "https://www.meaningcloud.com/developer/apis", access="free_tier", auth="api_key", env="MEANINGCLOUD_API_KEY"),
    _source_spec("perspective_api", "Perspective API", "news_sentiment", "news/sentiment", "https://developers.perspectiveapi.com/", access="free_key", auth="api_key"),
    _source_spec("hugging_face_public_models", "Hugging Face public models", "news_sentiment", "news/sentiment", "https://huggingface.co/docs/api-inference/index", access="free_tier", auth="api_key"),
    _source_spec("gdelt_project", "GDELT Project", "news_sentiment", "news/sentiment", "https://www.gdeltproject.org/", access="open_public", auth="optional_key", env="GDELT_API_KEY"),
    _source_spec("chronicling_america", "Chronicling America", "news_sentiment", "news/sentiment", "https://chroniclingamerica.loc.gov/about/api/", access="open_public", auth="none", terms=False),
    # Weather and environment.
    _source_spec("open_meteo", "Open-Meteo", "weather", "weather/environment", "https://open-meteo.com/en/docs", access="open_public", auth="none", terms=True),
    _source_spec("national_weather_service", "National Weather Service / US Weather", "weather", "weather/environment", "https://www.weather.gov/documentation/services-web-api", access="open_public", auth="user_agent", env="NWS_USER_AGENT", terms=False),
    _source_spec("weatherstack", "Weatherstack", "weather", "weather/environment", "https://weatherstack.com/documentation", access="free_tier", auth="api_key", env="WEATHERSTACK_API_KEY"),
    _source_spec("openweathermap", "OpenWeatherMap", "weather", "weather/environment", "https://openweathermap.org/api", access="free_key", auth="api_key", env="OPENWEATHER_API_KEY"),
    _source_spec("weatherapi", "WeatherAPI", "weather", "weather/environment", "https://www.weatherapi.com/docs/", access="free_key", auth="api_key", env="WEATHERAPI_KEY"),
    _source_spec("weatherbit", "Weatherbit", "weather", "weather/environment", "https://www.weatherbit.io/api", access="free_key", auth="api_key", env="WEATHERBIT_API_KEY"),
    _source_spec("visual_crossing", "Visual Crossing", "weather", "weather/environment", "https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/", access="free_tier", auth="api_key", env="VISUAL_CROSSING_API_KEY"),
    _source_spec("oikolab", "Oikolab", "weather", "weather/environment", "https://docs.oikolab.com/", access="free_tier", auth="api_key", env="OIKOLAB_API_KEY"),
    _source_spec("aviationweather", "AviationWeather", "weather", "weather/environment", "https://aviationweather.gov/data/api/", access="open_public", auth="none", terms=False),
    _source_spec("met_no", "Meteorologisk Institutt", "weather", "weather/environment", "https://api.met.no/", access="open_public", auth="user_agent", env="MET_NO_USER_AGENT", terms=True),
    _source_spec("pirate_weather", "Pirate Weather", "weather", "weather/environment", "https://docs.pirateweather.net/", access="free_key", auth="api_key"),
    _source_spec("rainviewer", "RainViewer", "weather", "weather/environment", "https://www.rainviewer.com/api.html", access="open_public", auth="none", terms=True),
    _source_spec("storm_glass", "Storm Glass", "weather", "weather/environment", "https://stormglass.io/", access="free_tier", auth="api_key"),
    _source_spec("openaq", "OpenAQ", "weather", "weather/environment", "https://docs.openaq.org/", access="free_tier", auth="api_key", env="OPENAQ_API_KEY"),
    _source_spec("aqicn", "AQICN", "weather", "weather/environment", "https://aqicn.org/api/", access="free_key", auth="api_key", env="AQICN_API_KEY"),
    _source_spec("openuv", "OpenUV", "weather", "weather/environment", "https://www.openuv.io/", access="free_tier", auth="api_key", env="OPENUV_API_KEY"),
    _source_spec("epa", "EPA", "government_open_data", "weather/environment", "https://www.epa.gov/enviro/envirofacts-data-service-api", access="free_key", auth="api_key", env="EPA_API_KEY", terms=False),
    _source_spec("usgs_earthquake_hazards", "USGS Earthquake Hazards", "weather", "weather/environment", "https://earthquake.usgs.gov/fdsnws/event/1/", access="open_public", auth="none", terms=False),
    _source_spec("usgs_water_services", "USGS Water Services", "weather", "weather/environment", "https://waterservices.usgs.gov/", access="open_public", auth="none", terms=False),
    _source_spec("noaa_public_datasets", "NOAA public datasets", "weather", "weather/environment", "https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation", access="open_public", auth="none", terms=True),
)


PUBLIC_API_SOURCE_SPECS += (
    # Government/open data.
    _source_spec("federal_register", "Federal Register", "government_open_data", "government/open data", "https://www.federalregister.gov/developers/documentation/api/v1", access="open_public", auth="none", terms=False),
    _source_spec("fec", "FEC", "government_open_data", "government/open data", "https://api.open.fec.gov/developers/", access="free_key", auth="api_key", env="FEC_API_KEY", terms=False),
    _source_spec("nps", "NPS", "government_open_data", "government/open data", "https://www.nps.gov/subjects/developer/api-documentation.htm", access="free_key", auth="api_key"),
    _source_spec("recreation_gov", "Recreation.gov", "government_open_data", "government/open data", "https://ridb.recreation.gov/docs", access="free_key", auth="api_key"),
    _source_spec("usaspending", "USAspending", "government_open_data", "government/open data", "https://api.usaspending.gov/", access="open_public", auth="none", terms=False),
    _source_spec("socrata", "Socrata", "government_open_data", "government/open data", "https://dev.socrata.com/", access="free_key", auth="app_token", env="SOCRATA_APP_TOKEN"),
    _source_spec("kaggle", "Kaggle", "government_open_data", "government/open data", "https://www.kaggle.com/docs/api", access="free_key", auth="api_key_pair", env=["KAGGLE_USERNAME", "KAGGLE_KEY"]),
    _source_spec("humanitarian_data_exchange", "Humanitarian Data Exchange", "government_open_data", "government/open data", "https://data.humdata.org/", access="open_public", auth="none", terms=True),
    _source_spec("opensanctions", "OpenSanctions", "government_open_data", "government/open data", "https://www.opensanctions.org/docs/api/", access="open_public", auth="none", terms=True),
    _source_spec("enigma_public", "Enigma Public", "government_open_data", "government/open data", "https://www.enigma.com/", access="free_tier", auth="api_key", env="ENIGMA_API_KEY"),
    _source_spec("open_government_usa", "Open Government USA", "government_open_data", "government/open data", "https://www.data.gov/", access="open_public", auth="none", terms=False),
    _source_spec("open_government_uk", "Open Government UK", "government_open_data", "government/open data", "https://www.api.gov.uk/", access="open_public", auth="none", terms=True),
    _source_spec("open_government_eu", "Open Government EU candidates", "government_open_data", "government/open data", "https://data.europa.eu/en", access="open_public", auth="none", terms=True),
    _source_spec("open_government_france", "Open Government France", "government_open_data", "government/open data", "https://www.data.gouv.fr/en/", access="open_public", auth="none", terms=True),
    _source_spec("open_government_germany", "Open Government Germany", "government_open_data", "government/open data", "https://www.govdata.de/", access="open_public", auth="none", terms=True),
    _source_spec("open_government_singapore", "Open Government Singapore", "government_open_data", "government/open data", "https://data.gov.sg/", access="open_public", auth="none", terms=True),
    _source_spec("open_government_new_zealand", "Open Government New Zealand", "government_open_data", "government/open data", "https://catalogue.data.govt.nz/", access="open_public", auth="none", terms=True),
    _source_spec("open_government_mexico", "Open Government Mexico", "government_open_data", "government/open data", "https://datos.gob.mx/", access="open_public", auth="none", terms=True),
    _source_spec("open_government_brazil", "Open Government Brazil", "government_open_data", "government/open data", "https://dados.gov.br/", access="open_public", auth="none", terms=True),
    _source_spec("worldbank_api_context", "World Bank API", "government_open_data", "government/open data", "https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information", access="open_public", auth="optional_key", env="WORLDBANK_API_KEY", terms=False),
    # Transportation/travel/logistics.
    _source_spec("ads_b_exchange", "ADS-B Exchange", "transportation_logistics", "transportation", "https://www.adsbexchange.com/data/", access="free_tier", auth="api_key", env="ADS_B_EXCHANGE_API_KEY"),
    _source_spec("aviationapi", "AviationAPI", "transportation_logistics", "transportation", "https://www.aviationapi.com/", access="free_tier", auth="api_key", env="AVIATIONAPI_KEY"),
    _source_spec("aviationstack", "AviationStack", "transportation_logistics", "transportation", "https://aviationstack.com/documentation", access="free_tier", auth="api_key", env="AVIATIONSTACK_API_KEY"),
    _source_spec("amadeus", "Amadeus", "transportation_logistics", "transportation", "https://developers.amadeus.com/", access="free_tier", auth="oauth", env=["AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"], oauth=True),
    _source_spec("transport_for_london", "Transport for London", "transportation_logistics", "transportation", "https://api-portal.tfl.gov.uk/", access="free_key", auth="api_key", env="TFL_API_KEY"),
    _source_spec("transportapi", "TransportAPI", "transportation_logistics", "transportation", "https://www.transportapi.com/", access="free_tier", auth="api_key", env="TRANSPORTAPI_KEY"),
    _source_spec("transport_rest", "transport.rest", "transportation_logistics", "transportation", "https://transport.rest/", access="open_public", auth="none"),
    _source_spec("opensky_network", "OpenSky Network", "transportation_logistics", "transportation", "https://openskynetwork.github.io/opensky-api/", access="free_tier", auth="basic", env=["OPENSKY_USERNAME", "OPENSKY_PASSWORD"]),
    _source_spec("faa_airport_delay_data", "FAA/NAS airport delay data", "transportation_logistics", "transportation", "https://nasstatus.faa.gov/", access="open_public", auth="none", terms=True),
    # Health/public context.
    _source_spec("openfda", "openFDA", "health_public_context", "health/public context", "https://open.fda.gov/apis/", access="free_key", auth="api_key", env="FDA_API_KEY", terms=False),
    _source_spec("fooddata_central", "FoodData Central", "health_public_context", "health/public context", "https://fdc.nal.usda.gov/api-guide.html", access="free_key", auth="api_key", env="USDA_API_KEY", terms=False),
    _source_spec("open_disease", "Open Disease", "health_public_context", "health/public context", "https://disease.sh/", access="open_public", auth="none", terms=True),
    _source_spec("nppes", "NPPES", "health_public_context", "health/public context", "https://npiregistry.cms.hhs.gov/api-page", access="open_public", auth="none", terms=False),
    _source_spec("cdc_public_data", "CDC public data", "health_public_context", "health/public context", "https://data.cdc.gov/", access="open_public", auth="none", terms=True),
    _source_spec("who_public_data", "WHO public data", "health_public_context", "health/public context", "https://www.who.int/data/gho/info/gho-odata-api", access="open_public", auth="none", terms=True),
    # Security/ops.
    _source_spec("gitguardian", "GitGuardian", "security_ops", "security/ops", "https://api.gitguardian.com/doc", access="free_tier", auth="api_key", env="GITGUARDIAN_API_KEY"),
    _source_spec("nvd", "NVD", "security_ops", "security/ops", "https://nvd.nist.gov/developers", access="free_key", auth="api_key", env="NVD_API_KEY", terms=False),
    _source_spec("virustotal", "VirusTotal", "security_ops", "security/ops", "https://docs.virustotal.com/reference/overview", access="free_key", auth="api_key", env="VIRUSTOTAL_API_KEY"),
    _source_spec("abuseipdb", "AbuseIPDB", "security_ops", "security/ops", "https://docs.abuseipdb.com/", access="free_tier", auth="api_key", env="ABUSEIPDB_API_KEY"),
    _source_spec("greynoise", "GreyNoise", "security_ops", "security/ops", "https://docs.greynoise.io/", access="free_tier", auth="api_key", env="GREYNOISE_API_KEY"),
    _source_spec("shodan", "Shodan", "security_ops", "security/ops", "https://developer.shodan.io/api", access="free_key", auth="api_key", env="SHODAN_API_KEY"),
    _source_spec("haveibeenpwned", "HaveIBeenPwned", "security_ops", "security/ops", "https://haveibeenpwned.com/API/v3", access="free_tier", auth="api_key", env="HIBP_API_KEY"),
    _source_spec("github_security_advisory_database", "GitHub Security Advisory Database", "security_ops", "security/ops", "https://github.com/advisories", access="open_public", auth="none", terms=True),
)


def _add_source_to_lane(collection: dict[str, list[dict[str, Any]]], lane_id: str, source: dict[str, Any]) -> None:
    collection.setdefault(lane_id, [])
    source_id = str(source.get("source_id") or "")
    for index, existing in enumerate(collection[lane_id]):
        if str(existing.get("source_id") or "") == source_id:
            merged = dict(existing)
            merged.update({key: value for key, value in source.items() if value not in (None, [], {})})
            collection[lane_id][index] = merged
            return
    collection[lane_id].append(source)


def _apply_public_api_expansion(collection: dict[str, list[dict[str, Any]]]) -> None:
    for spec in PUBLIC_API_SOURCE_SPECS:
        lane_id = str(spec["lane_id"])
        category = str(spec.get("source_category") or "uncategorized")
        env_names = spec.get("env_var_name")
        notes = list(spec.get("notes") or [])
        if category == "crypto":
            notes.append("Priority cryptocurrency module is edge-seeking, risk-controlled, calibration-backed, paper-only, and makes no guaranteed-win claim.")
        if category == "security/ops":
            notes.append("Project-protection source; not a model-signal source unless explicitly justified later.")
        if category == "health/public context":
            notes.append("Use aggregated/public context only; do not store personal health data or infer sensitive personal attributes.")
        source = _source(
            source_id=str(spec["source_id"]),
            source_name=str(spec["display_name"]),
            display_name=str(spec["display_name"]),
            lane_id=lane_id,
            module=_module_for_lane(lane_id),
            module_lane=lane_id,
            source_category=category,
            source_access_type=str(spec.get("source_access_type") or "open_public"),
            auth_type=str(spec.get("auth_type") or "none"),
            env_var_name=env_names,
            https_supported=True,
            cors_status="unknown",
            current_phase_allowed=False,
            future_source_candidate=bool(spec.get("future_source_candidate", False)),
            requires_account=bool(spec.get("requires_account", False)),
            requires_api_key=bool(env_names),
            requires_oauth=bool(spec.get("requires_oauth", False)),
            requires_terms_review=bool(spec.get("requires_terms_review", True)),
            requires_paid_subscription=bool(spec.get("requires_paid_subscription", False)),
            approval_status="not_approved" if (spec.get("future_source_candidate") or str(spec.get("source_access_type") or "") in FUTURE_ONLY_ACCESS_TYPES) else "needs_review",
            adapter_status=str(spec.get("adapter_status") or "not_started"),
            coverage=_coverage_for_source_category(category),
            cadence=str(spec.get("cadence") or "daily"),
            rate_limit_known=False,
            rate_limit_notes="Must be verified before adapter enablement; throttle and cache required.",
            terms_url_known=bool(spec.get("public_reference_url")),
            terms_notes="Terms/license review required before live adapter enablement." if spec.get("requires_terms_review", True) else "Public documentation reviewed as open government/public endpoint candidate; still verify before enablement.",
            commercial_use_unclear=bool(spec.get("requires_terms_review", True)),
            supported_use_cases=list(spec.get("supported_use_cases") or _use_cases_for_source_category(category)),
            model_input_mapping_status="planned",
            outcome_mapping_status="planned",
            backfill_mapping_status="planned",
            model_inputs_supported=list(spec.get("model_inputs_supported") or _model_inputs_for_source_category(category)),
            join_keys=_join_keys_for_source_category(category),
            outcome_fields_available=["final_result", "settlement_result", "forward_return"] if category in {"sports", "betting/odds", "crypto", "finance", "stock/fundamentals"} else ["public_metric_value"],
            historical_backfill_fields_available=["timestamp", "historical_value", "source_id"],
            public_reference_url=str(spec.get("public_reference_url") or ""),
            forbidden_actions=list(spec.get("forbidden_actions") or []),
            adapter_scope="read_only_market_data" if category in {"crypto", "finance", "stock/fundamentals", "betting/odds"} else "read_only_public_data",
            raw_payload_persistence_allowed=False,
            scoring_dimensions=CRYPTO_EDGE_SCORING_DIMENSIONS if lane_id == "cryptocurrency_edge_lab" else STOCK_ANALYST_SCORING_DIMENSIONS if lane_id == "institutional_stock_pro_analyst" else [],
            module_priority="highest" if lane_id == "cryptocurrency_edge_lab" else "high" if lane_id == "institutional_stock_pro_analyst" else None,
            module_status="planning_registry_only" if lane_id in {"cryptocurrency_edge_lab", "institutional_stock_pro_analyst"} else None,
            notes=notes,
            verified_at=None,
            verified_by=None,
        )
        _add_source_to_lane(collection, lane_id, source)

def _seed_sources() -> dict[str, list[dict[str, Any]]]:
    c: dict[str, list[dict[str, Any]]] = {lane["lane_id"]: [] for lane in MANDATORY_LANES}
    add = lambda lane, **kwargs: c[lane].append(_source(lane_id=lane, module=_module_for_lane(lane), **kwargs))

    add("prediction_markets", source_id="manual_prediction_market_import", source_name="Manual prediction-market result imports", source_access_type="manual_import", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, settlements=True, final_results=True), cadence="daily", model_inputs_supported=["ticker", "settlement_result"], join_keys=["ticker"], outcome_fields_available=["result", "status"], historical_backfill_fields_available=["settled_at", "result"])
    add("kalshi", source_id="kalshi_public_market_data", source_name="Kalshi public market data", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, adapter_status="implemented", coverage=_default_coverage(live=True, historical=True, settlements=True, final_results=True), cadence="near_live", model_inputs_supported=["ticker", "market_status", "close_time", "bid_ask", "settlement_result"], join_keys=["ticker", "market_ticker", "event_ticker"], outcome_fields_available=["result", "status"], historical_backfill_fields_available=["close_time", "settled_at", "result"], notes=["Read-only market and settlement use only; no order path."])
    add("polymarket", source_id="polymarket_gamma_api", source_name="Polymarket Gamma API", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, settlements=True, final_results=True), cadence="near_live", model_inputs_supported=["ticker", "market_status", "close_time", "bid_ask"], join_keys=["condition_id", "market_slug"], outcome_fields_available=["outcome"], historical_backfill_fields_available=["close_time", "outcome"])
    add("polymarket", source_id="polymarket_data_api", source_name="Polymarket Data API", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, settlements=True), cadence="near_live", model_inputs_supported=["ticker", "market_status", "close_time"], join_keys=["condition_id", "market_slug"], outcome_fields_available=["outcome"])

    for lane in ("stocks", "ETFs"):
        add(lane, source_id=f"{lane.lower()}_yfinance", source_name="yfinance", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, fundamentals=lane == "stocks", final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "timestamp", "volume", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["final_price"], historical_backfill_fields_available=["date", "close", "volume"])
        add(lane, source_id=f"{lane.lower()}_stooq", source_name="Stooq", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["close"], historical_backfill_fields_available=["date", "close"])
        add(lane, source_id=f"{lane.lower()}_alpha_vantage", source_name="Alpha Vantage free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "timestamp", "volume", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["adjusted_close"])
    add("stocks", source_id="sec_edgar_companyfacts", source_name="SEC EDGAR companyfacts", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, fundamentals=True), cadence="daily", model_inputs_supported=["symbol", "fundamentals"], join_keys=["cik", "ticker"], historical_backfill_fields_available=["facts", "period_end"])
    add("stocks", source_id="sec_edgar_submissions", source_name="SEC EDGAR submissions", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, fundamentals=True), cadence="daily", model_inputs_supported=["symbol", "fundamentals"], join_keys=["cik", "ticker"], historical_backfill_fields_available=["filing_date", "form"])
    add("stocks", source_id="nasdaq_data_link_future", source_name="Nasdaq Data Link future candidate", source_access_type="paid_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, fundamentals=True, macro=True), model_inputs_supported=["symbol", "historical_prices", "fundamentals"], join_keys=["symbol"])
    add("stocks", source_id="finnhub_future", source_name="Finnhub future candidate", source_access_type="paid_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, live=True, fundamentals=True), model_inputs_supported=["symbol", "price", "fundamentals"], join_keys=["symbol"])

    for lane in ("bonds", "rates", "macro"):
        add(lane, source_id=f"{lane}_fred_api", source_name="FRED API", source_access_type="free_key", current_phase_allowed=True, requires_api_key=True, requires_terms_review=False, coverage=_default_coverage(historical=True, macro=True, rates=True), cadence="daily", model_inputs_supported=["symbol", "historical_prices", "macro", "rates"], join_keys=["series_id", "date"], historical_backfill_fields_available=["date", "value"])
        add(lane, source_id=f"{lane}_treasury_fiscal_data", source_name="U.S. Treasury Fiscal Data API", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, macro=True, rates=True), cadence="daily", model_inputs_supported=["symbol", "historical_prices", "macro", "rates"], join_keys=["series", "date"], historical_backfill_fields_available=["date", "value"])
        add(lane, source_id=f"{lane}_treasury_yield", source_name="Treasury yield data", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, rates=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price", "rates"], join_keys=["maturity", "date"], outcome_fields_available=["yield"], historical_backfill_fields_available=["date", "yield"])
    for lane in ("major_assets", "rates"):
        add(lane, source_id=f"{lane}_stooq_rates_fx_indices", source_name="Stooq rates / FX / indices", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, macro=True, rates=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price", "macro", "rates"], join_keys=["symbol", "date"], outcome_fields_available=["close"], historical_backfill_fields_available=["date", "close"])
    add("major_assets", source_id="major_assets_yfinance_proxies", source_name="yfinance ETFs / indices / FX proxies", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "timestamp", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["close"])
    add("major_assets", source_id="alpha_vantage_fx_commodities", source_name="Alpha Vantage FX / commodities candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price"], join_keys=["symbol"])

    for lane in ("sportsbooks", "odds"):
        add(lane, source_id=f"{lane}_the_odds_api", source_name="The Odds API free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id", "bookmaker_key"])
        add(lane, source_id=f"{lane}_sportsgameodds", source_name="SportsGameOdds free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id"])
        add(lane, source_id=f"{lane}_odds_api_io", source_name="Odds-API.io free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id"])
        add(lane, source_id=f"{lane}_sharp_adapter_existing", source_name="Existing Sharp sportsbook adapter source pending access confirmation", source_access_type="sportsbook_account_candidate", future_source_candidate=True, requires_account=True, requires_sportsbook_account=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id"], notes=["Not enabled by registry; requires future confirmation of account, terms, and no write path."])

    add("weather", source_id="open_meteo_forecast", source_name="Open-Meteo forecast", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(live=True, weather=True), cadence="near_live", model_inputs_supported=["event_id", "location", "timestamp", "temperature", "wind", "precipitation"], join_keys=["latitude", "longitude", "timestamp"])
    add("weather", source_id="open_meteo_historical", source_name="Open-Meteo historical weather", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, weather=True), cadence="daily", model_inputs_supported=["event_id", "location", "timestamp", "temperature", "wind", "precipitation"], join_keys=["latitude", "longitude", "date"], historical_backfill_fields_available=["temperature", "wind", "precipitation"])
    add("schedules", source_id="manual_schedule_import", source_name="Manual schedule import", source_access_type="manual_import", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, schedules=True), cadence="daily", model_inputs_supported=["event_id", "timestamp", "schedule"], join_keys=["event_id", "date"])

    add("basketball_nba", source_id="nba_api", source_name="nba_api", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "player_stats", "final_results", "stable_event_id"], join_keys=["game_id"], outcome_fields_available=["final_score"], historical_backfill_fields_available=["game_id", "box_score"])
    add("basketball_nba", source_id="hoopr_nba", source_name="hoopR NBA", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"], historical_backfill_fields_available=["game_id", "box_score"])
    add("basketball_nba", source_id="espn_nba_public_wrapper", source_name="ESPN NBA public endpoints through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("basketball_wnba", source_id="wehoop_wnba", source_name="wehoop WNBA", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_wnba", source_id="wnba_stats_wrapper", source_name="WNBA Stats through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_wnba", source_id="espn_wnba_public_wrapper", source_name="ESPN WNBA through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("americanfootball_nfl", source_id="nflverse", source_name="nflverse", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"], historical_backfill_fields_available=["game_id", "play_by_play"])
    add("americanfootball_nfl", source_id="nflfastr", source_name="nflfastR", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_nfl", source_id="nflreadr", source_name="nflreadr", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_nfl", source_id="espn_nfl_public_wrapper", source_name="ESPN public endpoints", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("americanfootball_ncaaf", source_id="collegefootballdata", source_name="CollegeFootballData free-key candidate", source_access_type="free_key", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_ncaaf", source_id="sportsdataverse_cfb", source_name="SportsDataverse CFB packages", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, play_by_play=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_ncaaf", source_id="espn_cfb_public_wrapper", source_name="ESPN college football public endpoints", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("baseball_mlb", source_id="pybaseball", source_name="pybaseball", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_pk", "player_id"], outcome_fields_available=["final_score"])
    add("baseball_mlb", source_id="mlb_stats_api", source_name="MLB Stats API public endpoints candidate", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_pk"], outcome_fields_available=["final_score"])
    for src, name in (("baseball_savant_pybaseball", "Baseball Savant through pybaseball"), ("fangraphs_pybaseball", "FanGraphs through pybaseball"), ("baseball_reference_pybaseball", "Baseball Reference through pybaseball")):
        add("baseball_mlb", source_id=src, source_name=name, source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, team_stats=True), cadence="daily", model_inputs_supported=["player_stats", "team_stats"], join_keys=["player_id", "date"], notes=["Terms caution; adapter disabled pending review."])

    add("icehockey_nhl", source_id="nhl_public_api", source_name="NHL public API references", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("icehockey_nhl", source_id="nhl_api_wrappers", source_name="NHL API wrappers if license/terms acceptable", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])

    add("soccer", source_id="football_data_org", source_name="football-data.org free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["match_id"], outcome_fields_available=["final_score"])
    add("soccer", source_id="openfootball", source_name="openfootball datasets", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, schedules=True, final_results=True), cadence="historical_only", model_inputs_supported=["schedule", "final_results", "stable_event_id"], join_keys=["date", "home_team", "away_team"], outcome_fields_available=["final_score"])
    add("soccer", source_id="worldfootballr", source_name="worldfootballR", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["match_id"], outcome_fields_available=["final_score"])
    for src, name in (("understat_wrapper", "Understat through wrapper"), ("fbref_wrapper", "FBref through wrapper"), ("fotmob_wrapper", "Fotmob through wrapper")):
        add("soccer", source_id=src, source_name=name, source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["match_id"], outcome_fields_available=["final_score"], notes=["Terms caution; adapter disabled pending review."])

    add("tennis", source_id="jeff_sackmann_atp", source_name="Jeff Sackmann ATP data", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="historical_only", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tourney_id", "match_num"], outcome_fields_available=["winner"], historical_backfill_fields_available=["match_date", "winner"])
    add("tennis", source_id="jeff_sackmann_wta", source_name="Jeff Sackmann WTA data", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="historical_only", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tourney_id", "match_num"], outcome_fields_available=["winner"], historical_backfill_fields_available=["match_date", "winner"])
    add("tennis", source_id="match_charting_project", source_name="Match Charting Project", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, play_by_play=True, player_stats=True, final_results=True), cadence="historical_only", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["match_id"], outcome_fields_available=["winner"])

    for src, name in (("ufcstats_scraper_candidate", "UFCStats scraper candidates"), ("scrape_ufc_stats", "scrape_ufc_stats candidate"), ("ufc_stats_crawler", "ufc-stats-crawler candidate"), ("ufcscraper", "UFCscraper candidate")):
        add("ufc_mma", source_id=src, source_name=name, source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="daily", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["fight_id"], outcome_fields_available=["winner"], notes=["Adapter disabled pending manual terms review."])

    add("boxing", source_id="open_boxing_api_candidate", source_name="Open Boxing API candidate", source_access_type="unknown", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="unknown", model_inputs_supported=["player_stats", "final_results"], join_keys=["fight_id"], outcome_fields_available=["winner"])
    add("boxing", source_id="boxing_historical_dataset_needed", source_name="Public historical boxing datasets if discovered", source_access_type="unknown", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, final_results=True), cadence="unknown", model_inputs_supported=["final_results"], join_keys=["fight_id"], outcome_fields_available=["winner"])
    add("boxing", source_id="boxing_future_vendor", source_name="Boxing future vendor candidate", source_access_type="institutional_vendor_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, live=True, player_stats=True, final_results=True), model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["fight_id"], outcome_fields_available=["winner"])

    add("golf", source_id="golfastr", source_name="golfastR", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="daily", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tournament_id", "player_id"], outcome_fields_available=["finish_position"])
    add("golf", source_id="opengolfapi", source_name="OpenGolfAPI", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, player_stats=True, final_results=True), cadence="daily", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tournament_id", "player_id"], outcome_fields_available=["finish_position"])
    add("golf", source_id="espn_golf_public_wrapper", source_name="ESPN golf through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, player_stats=True, final_results=True), cadence="near_live", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["event_id", "player_id"], outcome_fields_available=["finish_position"])
    add("golf", source_id="public_pga_owgr_dataset_candidate", source_name="Public PGA / OWGR datasets if license-safe", source_access_type="unknown", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True), cadence="unknown", model_inputs_supported=["player_stats"], join_keys=["player_id"])
    add("golf", source_id="golf_strokes_gained_future_vendor", source_name="Golf future vendor candidate for strokes-gained depth", source_access_type="institutional_vendor_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, live=True, player_stats=True, final_results=True), model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["tournament_id", "player_id"], outcome_fields_available=["finish_position"])

    add("basketball_ncaab", source_id="hoopr_mens_college_basketball", source_name="hoopR men's college basketball", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaab", source_id="sportsdataverse_mbb", source_name="SportsDataverse men's basketball sources", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaab", source_id="espn_mbb_public_wrapper", source_name="ESPN MBB through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("basketball_ncaaw", source_id="wehoop_womens_college_basketball", source_name="wehoop women's college basketball", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaaw", source_id="sportsdataverse_wbb", source_name="SportsDataverse women's basketball sources", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaaw", source_id="espn_wbb_public_wrapper", source_name="ESPN WBB through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])
    _apply_public_api_expansion(c)
    return c


def _module_for_lane(lane_id: str) -> str:
    for lane in MANDATORY_LANES:
        if lane["lane_id"] == lane_id:
            return lane["module"]
    return lane_id


def _lane_status(sources: list[dict[str, Any]], future_sources: list[dict[str, Any]], verified: list[dict[str, Any]]) -> str:
    if verified:
        return "verified_sources_available"
    if sources:
        return "candidate_sources_available"
    if future_sources:
        return "future_vendor_needed"
    return "needs_external_research"


def _lane_planning_metadata(lane_id: str) -> dict[str, Any]:
    if lane_id == "institutional_stock_pro_analyst":
        return {
            "module_lane": "institutional_stock_pro_analyst",
            "module_priority": "high",
            "module_status": "planning_registry_only",
            "enabled": False,
            "adapter_status": "not_started",
            "execution_allowed": False,
            "provider_write": False,
            "planned_inputs": [
                "equity market data",
                "ETF market data",
                "fundamentals",
                "SEC filings",
                "earnings calendar",
                "earnings-call text",
                "insider transactions where terms-safe",
                "macro context",
                "rates context",
                "sector/industry context",
                "liquidity",
                "volatility",
                "options context where available",
                "news/sentiment",
            ],
            "planned_scores": list(STOCK_ANALYST_SCORING_DIMENSIONS),
            "safety_requirements": [
                "no broker order execution",
                "no live trading",
                "no portfolio rebalance execution",
                "no options execution",
                "no margin/leverage execution",
                "simulation only",
                "all sources disabled until reviewed",
                "all keys from environment variables only",
            ],
        }
    if lane_id == "cryptocurrency_edge_lab":
        return {
            "module_lane": "cryptocurrency_edge_lab",
            "module_priority": "highest",
            "module_status": "planning_registry_only",
            "enabled": False,
            "adapter_status": "not_started",
            "execution_allowed": False,
            "provider_write": False,
            "planned_inputs": [
                "spot crypto market data",
                "OHLCV candles",
                "order book depth where available",
                "exchange volume",
                "liquidity",
                "spread",
                "volatility",
                "funding rates where available",
                "open interest where available",
                "on-chain signals",
                "DEX liquidity",
                "gas fees",
                "stablecoin flows",
                "whale/activity proxies where terms-safe",
                "sentiment/news",
                "macro/rates/USD context",
                "correlation to equities/risk assets",
                "drawdown/regime detection",
                "anomaly detection",
                "paper-only strategy replay",
                "calibration against forward returns",
            ],
            "planned_scores": list(CRYPTO_EDGE_SCORING_DIMENSIONS),
            "safety_requirements": [
                "no wallet private keys",
                "no seed phrases",
                "no exchange trading keys",
                "no withdrawals",
                "no deposits",
                "no swaps",
                "no limit/market orders",
                "no live execution",
                "no on-chain transaction signing",
                "no broker/exchange provider writes",
                "paper-only simulation",
                "read-only public data only unless later explicitly approved",
            ],
            "forbidden_actions": list(CRYPTO_FORBIDDEN_ACTIONS),
            "strategy_language": ["edge-seeking", "risk-controlled", "calibration-backed", "paper-only", "no guaranteed wins", "no live execution"],
        }
    return {
        "enabled": False,
        "provider_write": False,
        "execution_allowed": False,
    }


def _lane_from_definition(defn: dict[str, str], sources: list[dict[str, Any]]) -> dict[str, Any]:
    current_sources = [s for s in sources if not bool(s.get("future_source_candidate", False))]
    future_sources = [s for s in sources if bool(s.get("future_source_candidate", False))]
    verified = [s for s in current_sources if s.get("verified_at") and s.get("approval_status") == "approved_for_research"]
    category = defn["category"]
    lane_id = defn["lane_id"]
    required = _required_inputs_for(category, lane_id)
    planning = _lane_planning_metadata(lane_id)
    lane = {
        "lane_id": lane_id,
        "module": defn["module"],
        "module_lane": planning.get("module_lane", lane_id),
        "module_priority": planning.get("module_priority"),
        "module_status": planning.get("module_status"),
        "enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "sport_or_asset": defn["sport_or_asset"],
        "category": category,
        "lane_status": _lane_status(current_sources, future_sources, verified),
        "assigned_research_lane": True,
        "external_research_owner": None,
        "source_candidates": current_sources,
        "verified_sources": verified,
        "future_source_candidates": future_sources,
        "rejected_sources": [],
        "required_model_inputs": required,
        "optional_model_inputs": _optional_inputs_for(category, lane_id),
        "outcome_fields_required": ["final_result"] if category in {"sport", "odds"} else ["settlement_result"] if category == "prediction_market" else ["final_price"] if category == "financial_market" else ["forward_return"] if category in {"crypto", "stock_analytics"} else [],
        "historical_backfill_fields_required": ["stable_id", "timestamp", "historical_value", "final_result"],
        "live_fields_desired": ["timestamp", "status", "current_value"],
        "context_fields_desired": _optional_inputs_for(category, lane_id),
        "adapter_status": str(planning.get("adapter_status") or ("planned" if verified else "blocked_pending_source" if not current_sources else "planned")),
        "planned_inputs": planning.get("planned_inputs", []),
        "planned_scores": planning.get("planned_scores", []),
        "safety_requirements": planning.get("safety_requirements", []),
        "forbidden_actions": planning.get("forbidden_actions", []),
        "strategy_language": planning.get("strategy_language", []),
        "coverage_score": 0,
        "freshness_score": 0,
        "outcome_availability_score": 0,
        "terms_risk_score": 0,
        "external_research_priority_score": 0,
        "notes_for_external_researcher": [
            "Keep provider writes disabled.",
            "Document stable join keys and final outcome fields before adapter work.",
            "Confirm terms and rate limits before enabling any adapter.",
        ],
    }
    scores = score_lane(lane)
    lane.update(scores)
    return lane


def build_registry(*, module: str | None = None) -> dict[str, Any]:
    seeded = _seed_sources()
    lanes = [_lane_from_definition(defn, seeded.get(defn["lane_id"], [])) for defn in MANDATORY_LANES]
    if module:
        needle = MODULE_ALIASES.get(str(module).strip().lower(), str(module).strip())
        lanes = [lane for lane in lanes if lane["module"] == needle or lane["lane_id"] == needle or lane["sport_or_asset"].lower() == needle.lower()]
    sources = [src for lane in lanes for src in lane["source_candidates"] + lane["future_source_candidates"] + lane["verified_sources"]]
    return {
        "ok": True,
        "status": "ok",
        "created_at": utc_now_iso(),
        "schema_version": "data_source_registry_v1",
        "module_filter": module,
        "total_lanes": len(lanes),
        "lanes": lanes,
        "sources": sources,
        "storage_health": get_storage_health(),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def summarize_registry(registry: dict[str, Any]) -> dict[str, Any]:
    lanes = list(registry.get("lanes") or [])
    sources = list(registry.get("sources") or [])
    modules_without_verified = [lane["module"] for lane in lanes if not lane.get("verified_sources")]
    category_counts = Counter(str(src.get("source_category") or "uncategorized") for src in sources)
    lane_counts = Counter(str(src.get("lane_id") or "unknown") for src in sources)
    env_names = sorted({name for src in sources for name in list(src.get("env_var_names") or []) if name})
    trading_capable_disabled_count = sum(
        1
        for src in sources
        if (src.get("forbidden_actions") or src.get("requires_execution_account") or src.get("requires_brokerage_account") or src.get("requires_sportsbook_account"))
        and not src.get("enabled")
    )
    return {
        "total_lanes": len(lanes),
        "lanes_with_verified_sources": sum(1 for lane in lanes if lane.get("verified_sources")),
        "lanes_with_candidate_sources": sum(1 for lane in lanes if lane.get("source_candidates")),
        "lanes_needing_external_research": sum(1 for lane in lanes if lane.get("lane_status") == "needs_external_research"),
        "lanes_blocked_pending_source": sum(1 for lane in lanes if lane.get("adapter_status") == "blocked_pending_source"),
        "lanes_future_vendor_needed": sum(1 for lane in lanes if lane.get("lane_status") == "future_vendor_needed"),
        "total_sources": len(sources),
        "enabled_source_count": sum(1 for src in sources if src.get("enabled")),
        "source_counts_by_lane": dict(sorted(lane_counts.items())),
        "source_counts_by_category": dict(sorted(category_counts.items())),
        "key_required_source_count": sum(1 for src in sources if src.get("requires_api_key")),
        "oauth_required_source_count": sum(1 for src in sources if src.get("requires_oauth")),
        "no_auth_source_count": sum(1 for src in sources if str(src.get("auth_type") or "none") == "none"),
        "trading_capable_disabled_count": trading_capable_disabled_count,
        "provider_write_enabled_count": sum(1 for src in sources if src.get("provider_write") is True or src.get("requires_provider_write") is True),
        "execution_allowed_count": sum(1 for src in sources if src.get("execution_allowed") is True),
        "env_var_names": env_names,
        "current_phase_allowed_count": sum(1 for src in sources if src.get("current_phase_allowed")),
        "candidate_count": sum(1 for src in sources if src.get("approval_status") in {"candidate", "needs_terms_review", "needs_review"}),
        "needs_terms_review_count": sum(1 for src in sources if src.get("requires_terms_review") or src.get("approval_status") in {"needs_terms_review", "needs_review"}),
        "future_source_candidate_count": sum(1 for src in sources if src.get("future_source_candidate")),
        "rejected_count": sum(1 for src in sources if src.get("approval_status") == "rejected"),
        "modules_fully_covered": [lane["module"] for lane in lanes if lane.get("coverage_score", 0) >= 85 and lane.get("verified_sources")],
        "modules_partially_covered": [lane["module"] for lane in lanes if lane.get("source_candidates") and not lane.get("verified_sources")],
        "modules_without_verified_source": modules_without_verified,
        "top_missing_fields_by_module": _top_missing_fields(lanes),
        "safety_flags": _safety_flags(),
    }


def _top_missing_fields(lanes: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for lane in lanes:
        required = set(lane.get("required_model_inputs") or [])
        supported: set[str] = set()
        for src in lane.get("source_candidates") or []:
            supported.update((src.get("model_mapping") or {}).get("model_inputs_supported") or [])
        missing = sorted(required - supported)
        if missing:
            out[str(lane["module"])] = missing[:10]
    return out


def _safety_flags() -> dict[str, Any]:
    return {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
    }


def build_registry_report(*, module: str | None = None) -> dict[str, Any]:
    from src.data.data_source_research_lanes import build_research_tasks
    from src.market_intelligence.model_input_coverage import build_coverage_report

    registry = build_registry(module=module)
    coverage = build_coverage_report(registry=registry)
    research = build_research_tasks(registry["lanes"])
    summary = summarize_registry(registry)
    recommended = recommended_next_adapters(registry, limit=50)
    return {
        **registry,
        **summary,
        "coverage": coverage,
        "research_lanes": research,
        "open_external_research_tasks": len(research.get("tasks", [])),
        "recommended_next_adapters": recommended,
    }


def recommended_next_adapters(registry: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane in registry.get("lanes") or []:
        for src in lane.get("source_candidates") or []:
            q = src.get("quality") or {}
            rows.append(
                {
                    "lane_id": lane.get("lane_id"),
                    "module": lane.get("module"),
                    "source_id": src.get("source_id"),
                    "source_name": src.get("source_name"),
                    "current_phase_usability_score": int(q.get("current_phase_usability_score") or 0),
                    "coverage_score": int(q.get("coverage_score") or 0),
                    "historical_depth_score": int(q.get("historical_depth_score") or 0),
                    "outcome_availability_score": int(q.get("outcome_availability_score") or 0),
                    "model_input_fill_rate": int(q.get("model_input_fill_rate") or 0),
                    "terms_risk_score": int(q.get("terms_risk_score") or 0),
                    "adapter_complexity_score": int(q.get("adapter_complexity_score") or 0),
                    "calibration_value_score": int(q.get("calibration_value_score") or 0),
                    "stock_signal_value_score": int(q.get("stock_signal_value_score") or 0),
                    "crypto_signal_value_score": int(q.get("crypto_signal_value_score") or 0),
                    "quality_tier": q.get("quality_tier"),
                    "module_priority": src.get("module_priority"),
                    "source_category": src.get("source_category"),
                    "adapter_status": src.get("adapter_status"),
                    "enabled": False,
                }
            )
    rows.sort(
        key=lambda row: (
            0 if row.get("module_priority") == "highest" else 1 if row.get("module_priority") == "high" else 2,
            -max(row["crypto_signal_value_score"], row["stock_signal_value_score"], row["calibration_value_score"]),
            row["adapter_complexity_score"],
            -row["current_phase_usability_score"],
            -row["coverage_score"],
            -row["historical_depth_score"],
            -row["outcome_availability_score"],
            -row["model_input_fill_rate"],
            row["terms_risk_score"],
            row["source_name"],
        )
    )
    return rows[: max(1, min(int(limit), 50))]


def build_env_var_registry(*, module: str | None = None) -> dict[str, Any]:
    registry = build_registry(module=module)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in registry.get("sources") or []:
        for name in list(source.get("env_var_names") or []):
            key = (str(source.get("source_id")), str(name))
            if key in seen:
                continue
            seen.add(key)
            auth_type = str(source.get("auth_type") or "")
            rows.append(
                {
                    "source_id": source.get("source_id"),
                    "display_name": source.get("display_name") or source.get("source_name"),
                    "module_lane": source.get("module_lane") or source.get("lane_id"),
                    "source_category": source.get("source_category"),
                    "env_var_name": str(name),
                    "required_for_live_fetch": bool(source.get("requires_api_key") and not auth_type.startswith("optional")),
                    "optional_for_metadata_only": bool(auth_type.startswith("optional") or source.get("adapter_status") in {"not_started", "planned"}),
                    "key_is_configured": bool(os.getenv(str(name))),
                    "secret_value_redacted": True,
                }
            )
    rows.sort(key=lambda row: (str(row["module_lane"]), str(row["source_id"]), str(row["env_var_name"])))
    return {
        "ok": True,
        "status": "ok",
        "module_filter": module,
        "env_var_count": len(rows),
        "env_vars": rows,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_source_priorities(*, module: str | None = None, limit: int = 50) -> dict[str, Any]:
    registry = build_registry(module=module)
    rows = recommended_next_adapters(registry, limit=max(limit, 50))
    stock = [row for row in rows if row.get("module") == "institutional_stock_pro_analyst"][:20]
    crypto = [row for row in rows if row.get("module") == "cryptocurrency_edge_lab"][:20]
    return {
        "ok": True,
        "status": "ok",
        "module_filter": module,
        "priority_count": len(rows[:limit]),
        "priorities": rows[:limit],
        "top_stock_analyst_priorities": stock,
        "top_crypto_edge_priorities": crypto,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_public_apis_expansion_report(*, module: str | None = None) -> dict[str, Any]:
    registry = build_registry(module=module)
    summary = summarize_registry(registry)
    priorities = build_source_priorities(module=module, limit=50)
    sources = list(registry.get("sources") or [])
    source_ids = {str(source.get("source_id")) for source in sources}
    expansion_source_ids = {str(spec.get("source_id")) for spec in PUBLIC_API_SOURCE_SPECS}
    added_ids = sorted(source_ids & expansion_source_ids)
    category_counts = dict(summary.get("source_counts_by_category") or {})
    stock_top = [row for row in priorities["priorities"] if row.get("module") == "institutional_stock_pro_analyst"][:20]
    crypto_top = [row for row in priorities["priorities"] if row.get("module") == "cryptocurrency_edge_lab"][:20]
    return {
        "ok": True,
        "status": "ok",
        "created_at": utc_now_iso(),
        "module_filter": module,
        "total_sources_before": PUBLIC_APIS_BASELINE_TOTAL_SOURCES,
        "total_sources_after": int(summary.get("total_sources", len(sources))),
        "total_lanes_before": PUBLIC_APIS_BASELINE_TOTAL_LANES,
        "total_lanes_after": int(summary.get("total_lanes", len(registry.get("lanes") or []))),
        "sources_added": max(0, int(summary.get("total_sources", len(sources))) - PUBLIC_APIS_BASELINE_TOTAL_SOURCES),
        "sources_updated": len(added_ids),
        "added_source_ids": added_ids,
        "enabled_source_count": int(summary.get("enabled_source_count", 0)),
        "source_counts_by_lane": dict(summary.get("source_counts_by_lane") or {}),
        "source_counts_by_category": category_counts,
        "key_required_source_count": int(summary.get("key_required_source_count", 0)),
        "oauth_required_source_count": int(summary.get("oauth_required_source_count", 0)),
        "no_auth_source_count": int(summary.get("no_auth_source_count", 0)),
        "terms_review_required_count": int(summary.get("needs_terms_review_count", 0)),
        "trading_capable_disabled_count": int(summary.get("trading_capable_disabled_count", 0)),
        "provider_write_enabled_count": int(summary.get("provider_write_enabled_count", 0)),
        "execution_allowed_count": int(summary.get("execution_allowed_count", 0)),
        "top_20_adapter_priorities": priorities["priorities"][:20],
        "top_stock_analyst_priorities": stock_top,
        "top_crypto_edge_priorities": crypto_top,
        "env_var_names_required": list(summary.get("env_var_names") or []),
        "raw_payload_included": False,
        "secrets_included": False,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
    }


def _data_sources_root(base_data_dir: str | Path | None = None) -> Path:
    if base_data_dir is None:
        root = get_data_sources_dir()
    else:
        root = resolve_base_data_dir(base_data_dir) / "data_sources"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def render_registry_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Source Registry Report",
        "",
        f"- created_at: {report.get('created_at')}",
        f"- total_lanes: {report.get('total_lanes')}",
        f"- total_sources: {report.get('total_sources')}",
        f"- current_phase_allowed_count: {report.get('current_phase_allowed_count')}",
        f"- needs_terms_review_count: {report.get('needs_terms_review_count')}",
        f"- future_source_candidate_count: {report.get('future_source_candidate_count')}",
        "- provider_write: false",
        "- execution_allowed: false",
        "- live_execution_enabled: false",
        "",
        "## Lanes",
    ]
    for lane in report.get("lanes") or []:
        lines.append(
            f"- {lane.get('lane_id')}: {lane.get('lane_status')}, candidates={len(lane.get('source_candidates') or [])}, future={len(lane.get('future_source_candidates') or [])}, coverage_score={lane.get('coverage_score')}"
        )
    return "\n".join(lines) + "\n"


def render_public_apis_expansion_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Public APIs Expansion Report",
        "",
        f"- created_at: {report.get('created_at')}",
        f"- total_sources_before: {report.get('total_sources_before')}",
        f"- total_sources_after: {report.get('total_sources_after')}",
        f"- sources_added: {report.get('sources_added')}",
        f"- enabled_source_count: {report.get('enabled_source_count')}",
        f"- provider_write_enabled_count: {report.get('provider_write_enabled_count')}",
        f"- execution_allowed_count: {report.get('execution_allowed_count')}",
        "- raw_payload_included: false",
        "- secrets_included: false",
        "",
        "## Category Counts",
    ]
    for category, count in sorted(dict(report.get("source_counts_by_category") or {}).items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Top Adapter Priorities"])
    for row in list(report.get("top_20_adapter_priorities") or [])[:20]:
        lines.append(f"- {row.get('module')} / {row.get('source_name')} ({row.get('quality_tier')})")
    return "\n".join(lines) + "\n"


def write_registry_artifacts(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    root = _data_sources_root(base_data_dir)
    run_id = sanitize_filename(f"data_sources_{str(report.get('created_at') or utc_now_iso()).replace(':', '-')}")
    latest = root / "latest.json"
    item = root / "items" / f"{run_id}.json"
    report_md = root / "reports" / f"{run_id}.md"
    daily = root / "daily" / f"{utc_now_iso()[:10]}.json"
    research_latest = root / "research_lanes.latest.json"
    _atomic_write_json(latest, report)
    _atomic_write_json(item, report)
    _atomic_write_text(report_md, render_registry_markdown(report))
    _atomic_write_json(daily, report)
    _atomic_write_json(research_latest, report.get("research_lanes") or {})
    return {
        "latest_path": _rel(latest, base_data_dir),
        "item_path": _rel(item, base_data_dir),
        "report_path": _rel(report_md, base_data_dir),
        "daily_path": _rel(daily, base_data_dir),
        "research_lanes_latest_path": _rel(research_latest, base_data_dir),
    }


def write_public_apis_expansion_report(report: dict[str, Any] | None = None, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    payload = report or build_public_apis_expansion_report()
    root = _data_sources_root(base_data_dir) / "public_apis_expansion"
    run_id = sanitize_filename(f"public_apis_{str(payload.get('created_at') or utc_now_iso()).replace(':', '-')}")
    day = utc_now_iso()[:10]
    latest = root / "latest.json"
    item = root / "items" / f"{run_id}.json"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    _atomic_write_json(latest, payload)
    _atomic_write_json(item, payload)
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, render_public_apis_expansion_markdown(payload))
    return {
        "public_apis_expansion_latest_path": _rel(latest, base_data_dir),
        "public_apis_expansion_item_path": _rel(item, base_data_dir),
        "public_apis_expansion_daily_json_path": _rel(daily_json, base_data_dir),
        "public_apis_expansion_daily_markdown_path": _rel(daily_md, base_data_dir),
    }


def verify_registry(*, module: str | None = None, persist_report: bool = True, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_registry_report(module=module)
    lanes = report.get("lanes") or []
    errors: list[str] = []
    lane_ids = {lane.get("lane_id") for lane in lanes}
    if module is None:
        for lane in MANDATORY_LANES:
            if lane["lane_id"] not in lane_ids:
                errors.append(f"missing_lane:{lane['lane_id']}")
    for src in report.get("sources") or []:
        if src.get("enabled") and not (src.get("approval_status") == "approved_for_research" and src.get("current_phase_allowed")):
            errors.append(f"unsafe_enabled_source:{src.get('source_id')}")
        if src.get("future_source_candidate") and src.get("enabled"):
            errors.append(f"future_source_enabled:{src.get('source_id')}")
        if src.get("requires_provider_write") or src.get("provider_write"):
            errors.append(f"provider_write_source:{src.get('source_id')}")
        if src.get("execution_allowed"):
            errors.append(f"execution_allowed_source:{src.get('source_id')}")
        if src.get("raw_payload_persistence_allowed"):
            errors.append(f"raw_payload_persistence_allowed:{src.get('source_id')}")
        if src.get("paid_upgrade_allowed"):
            errors.append(f"paid_upgrade_allowed:{src.get('source_id')}")
        if src.get("substantial_usage_allowed"):
            errors.append(f"substantial_usage_allowed:{src.get('source_id')}")
    report.update(
        {
            "status": "verified" if not errors else "verification_failed",
            "verification_errors": errors,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "raw_payload_included": False,
        }
    )
    if persist_report:
        report.update(write_registry_artifacts(report, base_data_dir=base_data_dir))
        report.update(write_public_apis_expansion_report(base_data_dir=base_data_dir))
    return report
