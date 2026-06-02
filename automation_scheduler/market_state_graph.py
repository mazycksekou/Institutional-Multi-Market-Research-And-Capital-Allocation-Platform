from __future__ import annotations

from typing import Any

from .manifold_feature_builder import infer_asset_type


GRAPH_RELATIONSHIP_VERSION = "compact_market_state_graph_v1"

RELATIONSHIP_CATALOG: dict[str, list[dict[str, Any]]] = {
    "sportsbook": [
        {"path": ["player", "injury", "usage_change", "prop_line"], "hypothesis": "injury_confirmed_increases_player_usage", "fields": ["injury_news_score", "prop_context_score"]},
        {"path": ["team", "pace", "total", "player_points"], "hypothesis": "pace_up_increases_total_points_prop_hit_rate", "fields": ["game_script_score"]},
        {"path": ["team", "defensive_weakness", "player_stat_category"], "hypothesis": "defensive_weakness_increases_matching_prop_rate", "fields": ["prop_context_score"]},
        {"path": ["weather", "passing_volume", "total_props"], "hypothesis": "weather_shift_changes_passing_volume", "fields": ["weather_score"]},
        {"path": ["official_referee", "foul_rate", "free_throws_total"], "hypothesis": "foul_rate_environment_changes_free_throw_volume", "fields": ["official_score", "referee_score"]},
        {"path": ["lineup", "spacing", "three_point_props"], "hypothesis": "lineup_spacing_changes_three_point_prop_quality", "fields": ["lineup_confirmation_score"]},
        {"path": ["lineup", "rebound_profile", "rebound_props"], "hypothesis": "lineup_rebound_profile_changes_rebound_prop_quality", "fields": ["lineup_confirmation_score", "prop_context_score"]},
    ],
    "prediction_market": [
        {"path": ["contract", "event", "settlement_rule", "liquidity_zone"], "hypothesis": "settlement_rule_uncertainty_changes_liquidity_quality", "fields": ["settlement_uncertainty_score", "liquidity_score"]},
        {"path": ["event", "news_catalyst", "price_movement"], "hypothesis": "news_catalyst_moves_contract_price", "fields": ["catalyst_score"]},
        {"path": ["market", "close_time", "settlement_uncertainty"], "hypothesis": "close_time_pressure_increases_settlement_uncertainty", "fields": ["close_time_pressure_score", "time_to_close_seconds"]},
        {"path": ["orderbook", "spread", "fake_edge_risk"], "hypothesis": "wide_spread_creates_fake_prediction_market_edge", "fields": ["bid_ask_spread", "spread_score"]},
    ],
    "stock": [
        {"path": ["company", "balance_sheet", "dilution_risk", "momentum_trap"], "hypothesis": "poor_balance_sheet_increases_dilution_trap_risk", "fields": ["balance_sheet_quality_score", "dilution_risk_score"]},
        {"path": ["catalyst", "volume_expansion", "breakout_candidate"], "hypothesis": "catalyst_volume_expansion_increases_breakout_follow_through", "fields": ["catalyst_quality_score", "relative_volume"]},
        {"path": ["float", "supply_constraint", "rate_of_change"], "hypothesis": "low_float_plus_catalyst_increases_momentum_follow_through", "fields": ["float_shares", "float_rotation"]},
        {"path": ["spread", "slippage", "review_downgrade"], "hypothesis": "wide_spread_increases_slippage_review_downgrade", "fields": ["spread_percent", "spread_score"]},
    ],
    "etf": [
        {"path": ["macro_event", "yield_move", "etf_reaction"], "hypothesis": "macro_event_surprise_increases_etf_rate_sensitivity", "fields": ["macro_event_score", "yield_change"]},
        {"path": ["credit_spread", "risk_off_regime", "etf_drawdown_risk"], "hypothesis": "credit_spread_widening_increases_risk_off_etf_pressure", "fields": ["credit_spread_score", "risk_on_risk_off_score"]},
    ],
    "crypto": [
        {"path": ["funding", "leverage_pressure", "liquidation_risk"], "hypothesis": "funding_extreme_increases_crypto_reversal_risk", "fields": ["funding_rate", "liquidation_cluster_risk"]},
        {"path": ["open_interest", "squeeze_potential"], "hypothesis": "open_interest_expansion_increases_squeeze_potential", "fields": ["open_interest"]},
        {"path": ["orderbook_depth", "slippage"], "hypothesis": "thin_orderbook_depth_increases_slippage", "fields": ["orderbook_depth_1pct", "spread_percent"]},
        {"path": ["exchange", "liquidity_quality"], "hypothesis": "exchange_quality_changes_crypto_liquidity", "fields": ["exchange_dislocation_score"]},
    ],
    "bond_rate": [
        {"path": ["macro_event", "yield_move", "etf_reaction"], "hypothesis": "macro_event_surprise_increases_bond_rate_volatility", "fields": ["macro_event_score", "yield_change"]},
        {"path": ["inflation_print", "policy_repricing"], "hypothesis": "inflation_print_changes_policy_repricing", "fields": ["inflation_repricing_score", "policy_repricing_score"]},
        {"path": ["credit_spread", "risk_off_regime"], "hypothesis": "credit_spread_widening_signals_risk_off_regime", "fields": ["credit_spread_score"]},
        {"path": ["treasury_auction", "rate_volatility"], "hypothesis": "treasury_auction_increases_rate_volatility", "fields": ["rate_volatility_score"]},
    ],
    "major_asset": [
        {"path": ["macro_event", "risk_on_risk_off", "major_asset_reaction"], "hypothesis": "macro_event_changes_risk_regime", "fields": ["macro_event_score", "risk_on_risk_off_score"]},
        {"path": ["policy_repricing", "duration_sensitivity", "major_asset_reaction"], "hypothesis": "policy_repricing_changes_duration_sensitive_assets", "fields": ["policy_repricing_score", "duration_sensitivity_score"]},
    ],
}


def infer_graph_asset_type(item: dict[str, Any] | None) -> str:
    asset_type = infer_asset_type(dict(item or {}))
    if asset_type in RELATIONSHIP_CATALOG:
        return asset_type
    return "stock"


def relationship_templates_for_item(item: dict[str, Any] | None) -> list[dict[str, Any]]:
    asset_type = infer_graph_asset_type(item)
    return list(RELATIONSHIP_CATALOG.get(asset_type, []))
