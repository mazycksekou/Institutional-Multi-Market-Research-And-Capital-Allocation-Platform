# NFL Position Group Feature Inventory

This inventory lists the position groups discovered in the repo and the feature families already associated with them.

| Position group | Discovered features / signals | Support level | Evidence | Notes |
|---|---|---|---|---|
| QB | `snap_share_recent`, `dropbacks`, `epa_per_dropback`, `cpoe`, `pressure_to_sack_rate`, `time_to_throw`, `air_yards_per_attempt`, `deep_attempt_rate`, `turnover_worthy_proxy` | PARTIAL | `src/market_intelligence/football_role_impact.py`, `tests/test_football_impact_intelligence.py` | Strongest player-group discovery lane. |
| RB | `carry_share_recent`, `rush_epa`, `rushing_success_rate`, `target_share`, `route_participation` | PARTIAL | `src/market_intelligence/football_role_impact.py` | Useful for rushing and receiving props. |
| WR | `route_participation`, `target_share`, `air_yard_share`, `yards_per_route_run` | PARTIAL | `src/market_intelligence/football_role_impact.py` | Prop relevance is already modeled. |
| TE | `route_participation`, `target_share`, `air_yard_share`, `yards_per_route_run` | PARTIAL | `src/market_intelligence/football_role_impact.py` | Similar to WR but narrower. |
| Offensive Line | `run_block_success_proxy`, `ol_pressure_allowed_proxy`, `offensive_line_continuity` | PARTIAL | `src/market_intelligence/football_matchup_context.py`, `src/market_intelligence/football_role_impact.py` | Key unit-level gap remains validated coverage. |
| Defensive Line | `pressure_rate`, `sack_rate`, `run_stop_rate`, `defensive_run_stop_rate` | PARTIAL | `src/market_intelligence/football_role_impact.py`, `src/market_intelligence/football_matchup_context.py` | Useful for sacks and disruption models. |
| Linebackers | tackle / blitz / coverage proxies | CONTRACT_ONLY | inferred from football role coverage | Contract reserved; weak direct source lane. |
| Secondary | `yards_allowed_per_target`, `explosive_allowed_rate`, `turnover_play_rate` | PARTIAL | `src/market_intelligence/football_role_impact.py` | Defensive pass-context lane exists. |
| Special Teams | kicking / return / coverage proxies | CONTRACT_ONLY | field/market context only | Contract reserved; no full lane proven. |
| Coaches | `head_coach`, `offensive_coordinator`, `defensive_coordinator`, `coaching_continuity_score` | PARTIAL | `src/market_intelligence/nfl_coaching_sources.py`, `src/market_intelligence/nfl_coaching_feature_builders.py` | Strong discovery lane, but source blocked. |
| Officials | `official_id`, `official_name`, `position` | PARTIAL | `src/data/nfl_open_data_field_catalog.py` | Catalogued, but no validated operational lane yet. |
| Weather | `temp`, `wind`, `roof`, `surface`, `weather_impact_score` | PARTIAL | `src/market_intelligence/football_availability_context.py` | Already used as a market modifier. |
| Medical | `injury_status`, `practice_status`, `report_status`, availability risk proxies | CONTRACT_ONLY | `src/market_intelligence/football_availability_context.py` | Contract exists; a stable medical provider lane does not. |
| Market Context | `spread_line`, `total_line`, `moneyline`, `opening_line`, `closing_line`, `implied_probability`, `clv_proxy` | PARTIAL | `src/data/historical_odds.py`, `src/market_intelligence/football_market_relevance.py` | This is a real and reusable lane. |

## Inventory Summary

- The repo already supports the language needed for all major football position groups.
- The deepest real support is for QB, RB, WR, TE, OL, DL, coaching, weather, and market context.
- The weakest support is special teams, linebackers, and medical as end-to-end validated data lanes.

