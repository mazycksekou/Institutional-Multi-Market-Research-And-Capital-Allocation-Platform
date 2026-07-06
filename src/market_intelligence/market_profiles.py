from __future__ import annotations

from typing import Any, Mapping

from src.data.market_profile_contracts import MarketProfileContract, build_market_profile_contract, validate_market_profile_contract
from src.data.market_profile_registry import (
    get_market_profile,
    list_market_profiles,
    register_market_profile,
    reset_market_profile_registry,
)
from src.market_intelligence.sports import normalize_sport


SPORTS_PROFILE = build_market_profile_contract(
    {
        "profile_id": "sports",
        "profile_family": "sports",
        "canonical_identifiers": ("league", "season", "event_id", "team_id", "player_id", "market_id"),
        "required_timestamps": ("decision_time", "snapshot_time", "created_at", "updated_at"),
        "canonical_fields": (
            "league",
            "season",
            "event_id",
            "team_id",
            "player_id",
            "position_group",
            "market_id",
            "odds_snapshot",
            "result",
            "decision_time",
            "snapshot_time",
            "feature_group",
        ),
        "atomic_feature_groups": (
            "league fields",
            "season fields",
            "event identifiers",
            "team fields",
            "player fields",
            "position groups",
        ),
        "composite_feature_groups": ("odds movement", "injury impact", "weather impact", "rest/travel", "market context"),
        "validation_rules": ("point_in_time_safe_inputs_only", "timestamp_required_for_snapshots", "no_post_event_inputs_for_pregame_features"),
        "leakage_rules": ("freeze_pregame_snapshots_at_decision_time", "block_result_fields_from_feature_inputs", "reject_future_odds_leaks"),
        "storage_requirements": ("raw_records", "normalized_records", "feature_snapshots", "backtest_rows", "lineage_records"),
        "feature_store_requirements": ("versioned_feature_packs", "point_in_time_snapshots", "leakage_checks"),
        "backtest_requirements": ("chronological_folds", "settled_outcomes", "walk_forward_validation"),
        "streamlit_requirements": ("dataset_readiness", "feature_readiness", "leakage_warnings", "backtest_summary"),
        "research_requirements": ("hypothesis_testing", "feature_ablation", "fold_comparison"),
        "worldview_permissions": ("hypothesis_generation", "experiment_request", "evidence_review"),
        "paper_trading_requirements": ("simulated_decisions_only", "no_live_money", "record_reasons"),
        "live_execution_gates": ("paper_trading_passes", "governance_approval", "observability_ready"),
        "description": "Canonical sports market profile family.",
        "metadata": {"scope": "sports"},
    }
)

PREDICTION_MARKET_PROFILE = build_market_profile_contract(
    {
        "profile_id": "prediction_markets",
        "profile_family": "prediction_markets",
        "canonical_identifiers": ("event_id", "contract_id", "market_id", "settlement_id"),
        "required_timestamps": ("decision_time", "snapshot_time", "created_at", "updated_at"),
        "canonical_fields": (
            "event_id",
            "contract_id",
            "market_id",
            "settlement_rule",
            "liquidity",
            "bid",
            "ask",
            "order_book_snapshot",
            "decision_time",
            "snapshot_time",
        ),
        "atomic_feature_groups": ("event identifiers", "contract identifiers", "market identifiers", "bid/ask levels", "liquidity fields"),
        "composite_feature_groups": ("spread pressure", "liquidity quality", "settlement confidence", "order book imbalance"),
        "validation_rules": ("point_in_time_safe_inputs_only", "timestamp_required_for_snapshots", "settlement_rules_must_be_explicit"),
        "leakage_rules": ("freeze_order_book_at_snapshot_time", "block_post_settlement_features_from_inputs", "reject_derived_closing_truth_as_inputs"),
        "storage_requirements": ("raw_records", "normalized_records", "feature_snapshots", "backtest_rows", "lineage_records"),
        "feature_store_requirements": ("versioned_feature_packs", "order_book_snapshots", "settlement_aware_features"),
        "backtest_requirements": ("chronological_folds", "settled_outcomes", "liquidity_aware_replay"),
        "streamlit_requirements": ("dataset_readiness", "liquidity_summary", "settlement_summary", "backtest_summary"),
        "research_requirements": ("hypothesis_testing", "market_microstructure_analysis", "liquidity_ablation"),
        "worldview_permissions": ("hypothesis_generation", "experiment_request", "evidence_review"),
        "paper_trading_requirements": ("simulated_contract_only", "no_live_money", "record_reasons"),
        "live_execution_gates": ("paper_trading_passes", "governance_approval", "observability_ready"),
        "description": "Reusable prediction market profile family.",
        "metadata": {"scope": "prediction_markets"},
    }
)

OPTIONS_0DTE_PROFILE = build_market_profile_contract(
    {
        "profile_id": "options_0dte",
        "profile_family": "options_0dte",
        "canonical_identifiers": ("symbol", "expiration", "strike", "option_type", "contract_id"),
        "required_timestamps": ("decision_time", "snapshot_time", "created_at", "updated_at"),
        "canonical_fields": (
            "symbol",
            "expiration",
            "strike",
            "option_type",
            "greeks",
            "implied_volatility",
            "open_interest",
            "volume",
            "dealer_positioning",
            "decision_time",
            "snapshot_time",
        ),
        "atomic_feature_groups": ("symbol fields", "expiration fields", "strike fields", "option greeks", "volume / open interest"),
        "composite_feature_groups": ("gex", "vanna", "dealer positioning", "0dte decay pressure", "volatility regime"),
        "validation_rules": ("point_in_time_safe_inputs_only", "timestamp_required_for_snapshots", "contract_expiry_must_be_explicit"),
        "leakage_rules": ("freeze_option_chain_at_snapshot_time", "block_intraday_oi_as_fresh_truth", "reject_post_close_data_as_inputs"),
        "storage_requirements": ("raw_records", "normalized_records", "feature_snapshots", "backtest_rows", "lineage_records"),
        "feature_store_requirements": ("versioned_feature_packs", "option_chain_snapshots", "expiry_aware_features"),
        "backtest_requirements": ("chronological_folds", "settled_outcomes", "cost_and_slippage_controls"),
        "streamlit_requirements": ("dataset_readiness", "chain_summary", "greeks_summary", "backtest_summary"),
        "research_requirements": ("hypothesis_testing", "volatility_ablation", "dealer_positioning_ablation"),
        "worldview_permissions": ("hypothesis_generation", "experiment_request", "evidence_review"),
        "paper_trading_requirements": ("simulated_contract_only", "no_live_money", "record_reasons"),
        "live_execution_gates": ("paper_trading_passes", "governance_approval", "observability_ready"),
        "description": "Reusable options / 0DTE profile family.",
        "metadata": {"scope": "options_0dte"},
    }
)

NFL_AS_SPORTS_PROFILE_INSTANCE = build_market_profile_contract(
    {
        "profile_id": "sports:nfl",
        "profile_family": "sports",
        "market_scope": "americanfootball_nfl",
        "canonical_identifiers": ("league", "season", "game_id", "team_id", "player_id", "market_id"),
        "required_timestamps": ("decision_time", "snapshot_time", "created_at", "updated_at"),
        "canonical_fields": (
            "league",
            "season",
            "game_id",
            "team_id",
            "player_id",
            "position_group",
            "market_id",
            "odds_snapshot",
            "result",
            "decision_time",
            "snapshot_time",
            "feature_group",
        ),
        "atomic_feature_groups": (
            "QB fields",
            "RB fields",
            "WR fields",
            "TE fields",
            "offensive line fields",
            "defensive line fields",
            "linebacker fields",
            "defensive back fields",
            "special teams fields",
            "coaching fields",
            "officials fields",
        ),
        "composite_feature_groups": ("rest advantage", "weather impact", "market movement", "injury-adjusted unit score", "position-group matchup"),
        "validation_rules": ("point_in_time_safe_inputs_only", "timestamp_required_for_snapshots", "no_post_event_inputs_for_pregame_features"),
        "leakage_rules": ("freeze_pregame_snapshots_at_decision_time", "block_result_fields_from_feature_inputs", "reject_closing_line_leakage"),
        "storage_requirements": ("raw_records", "normalized_records", "feature_snapshots", "backtest_rows", "lineage_records"),
        "feature_store_requirements": ("versioned_feature_packs", "point_in_time_snapshots", "leakage_checks"),
        "backtest_requirements": ("chronological_folds", "settled_outcomes", "walk_forward_validation"),
        "streamlit_requirements": ("dataset_readiness", "feature_readiness", "leakage_warnings", "backtest_summary"),
        "research_requirements": ("hypothesis_testing", "feature_ablation", "fold_comparison"),
        "worldview_permissions": ("hypothesis_generation", "experiment_request", "evidence_review"),
        "paper_trading_requirements": ("simulated_decisions_only", "no_live_money", "record_reasons"),
        "live_execution_gates": ("paper_trading_passes", "governance_approval", "observability_ready"),
        "description": "NFL as the first sports-profile instance.",
        "metadata": {"scope": "americanfootball_nfl", "sport": normalize_sport("nfl"), "league": "NFL"},
    }
)

DEFAULT_MARKET_PROFILE_CATALOG = (
    SPORTS_PROFILE,
    PREDICTION_MARKET_PROFILE,
    OPTIONS_0DTE_PROFILE,
    NFL_AS_SPORTS_PROFILE_INSTANCE,
)


def build_market_profile_catalog() -> tuple[MarketProfileContract, ...]:
    return DEFAULT_MARKET_PROFILE_CATALOG


def register_default_market_profiles() -> tuple[MarketProfileContract, ...]:
    reset_market_profile_registry()
    for profile in DEFAULT_MARKET_PROFILE_CATALOG:
        register_market_profile(profile)
    return list_market_profiles()


def get_market_profile_catalog_entry(profile_id: str) -> MarketProfileContract | None:
    return get_market_profile(profile_id) or next((profile for profile in DEFAULT_MARKET_PROFILE_CATALOG if profile.profile_id == str(profile_id).strip()), None)


def validate_market_profile_catalog(catalog: Mapping[str, Any] | None = None) -> dict[str, Any]:
    profiles = tuple(catalog.values()) if isinstance(catalog, Mapping) else build_market_profile_catalog()
    seen: set[str] = set()
    errors: list[str] = []
    profiles_map: dict[str, MarketProfileContract] = {}

    for profile in profiles:
        contract = profile if isinstance(profile, MarketProfileContract) else build_market_profile_contract(profile)
        validation = validate_market_profile_contract(contract)
        profiles_map[contract.profile_id] = contract
        if not validation["ok"]:
            errors.extend(f"{contract.profile_id}: {message}" for message in validation["errors"])
        if contract.profile_id in seen:
            errors.append(f"duplicate profile_id: {contract.profile_id}")
        seen.add(contract.profile_id)

    return {
        "ok": not errors,
        "errors": errors,
        "profiles": profiles_map,
    }


__all__ = [
    "DEFAULT_MARKET_PROFILE_CATALOG",
    "DEFAULT_MARKET_PROFILE_REGISTRY",
    "NFL_AS_SPORTS_PROFILE_INSTANCE",
    "OPTIONS_0DTE_PROFILE",
    "PREDICTION_MARKET_PROFILE",
    "SPORTS_PROFILE",
    "build_market_profile_catalog",
    "get_market_profile_catalog_entry",
    "register_default_market_profiles",
    "validate_market_profile_catalog",
]
