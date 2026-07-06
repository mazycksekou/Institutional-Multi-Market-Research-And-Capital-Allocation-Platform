# NFL Position Group Feature Contract

This contract defines the position-group support boundary for NFL feature work.
It is a planning and discovery contract, not an implementation claim.

## Support Levels

- `IMPLEMENTED` = supported in a meaningful end-to-end way
- `PARTIAL` = some real support exists, but the slice is incomplete
- `CONTRACT_ONLY` = the repo has the contract or helper shape, but not a validated feature lane
- `FUTURE_EXTENSION` = intentionally reserved for later

## Position Group Support Matrix

| Position group | Support level | Discovered feature examples | Required fields | Optional fields | Forbidden fields | Supported market types | Supported models | Supported backtests |
|---|---|---|---|---|---|---|---|---|
| QB | PARTIAL | `snap_share_recent`, `dropbacks`, `epa_per_dropback`, `cpoe`, `pressure_to_sack_rate`, `time_to_throw`, `air_yards_per_attempt` | QB participation, pressure, efficiency | deep attempt rate, turnover proxy | fabricated tracking | passing props, team totals, sides | role impact, market relevance | player and game backtests |
| RB | PARTIAL | `carry_share_recent`, `rush_epa`, `rushing_success_rate`, `target_share`, `route_participation` | carries, route share, rushing efficiency | receiving usage, explosive rate | future-only tracking | rushing props, receptions, TD props | role impact, market relevance | player and game backtests |
| WR | PARTIAL | `route_participation`, `target_share`, `air_yard_share`, `yards_per_route_run` | routes, targets, air yards | separation proxy, red-zone usage | fabricated tracking | receiving props, TD props | role impact, matchup | player and game backtests |
| TE | PARTIAL | `route_participation`, `target_share`, `air_yard_share`, `yards_per_route_run` | routes, targets, red-zone usage | blocking role proxies | fabricated tracking | receptions / yards / TD props | role impact, matchup | player and game backtests |
| Offensive Line | PARTIAL | `run_block_success_proxy`, `ol_pressure_allowed_proxy`, `offensive_line_continuity` | pressure allowed, continuity | run block index | unsupported player-tracking claims | sacks, passing, rushing, totals | matchup, line score | team / unit backtests |
| Defensive Line | PARTIAL | `pressure_rate`, `sack_rate`, `run_stop_rate`, `defensive_run_stop_rate` | pressure, sacks, run stop | disruption rate | fabricated charting | sacks, tackles, game totals | matchup, line score | team / unit backtests |
| Linebackers | CONTRACT_ONLY | tackle rate, blitz rate, coverage proxy | tackle involvement | coverage depth, alignment | hidden tracking | tackles, sacks, defensive props | defensive matchup | future backtests |
| Secondary | PARTIAL | `yards_allowed_per_target`, `explosive_allowed_rate`, `turnover_play_rate` | coverage outcome proxies | alignment, leverage proxy | fabricated tracking | passing props, interceptions | defensive matchup | team / player backtests |
| Special Teams | CONTRACT_ONLY | field goal, punt, kick return proxies | kicking / coverage events | return efficiency | fabricated tracking | field goals, totals, return props | special teams model | future backtests |
| Coaches | PARTIAL | `head_coach`, `coordinator`, `coaching_continuity_score`, `staff_turnover_candidate` | staff identity and continuity | scheme tendencies | hidden scraped claims | all team markets | team impact / diagnostics | team backtests |
| Officials | PARTIAL | `official_id`, `official_name`, `position` | assignment / officiating identity | tendency proxies | fabricated tendencies | totals, penalties, some props | officiating context | team / game backtests |
| Weather | PARTIAL | `temp`, `wind`, `roof`, `surface`, `weather_impact_score` | game weather context | weather risk modifiers | unsupported forecast claims | totals, passing, kicking | weather modifier | game backtests |
| Medical | CONTRACT_ONLY | injury status, practice status, report status | injury and availability | recovery / return estimates | hidden medical claims | player props, team totals | availability modifier | player and team backtests |
| Market Context | PARTIAL | open/close lines, implied probability, CLV proxy | line movement / market state | liquidity / timing proxies | future price leakage | all priced markets | market relevance, calibration | market backtests |

## Contract Notes

- The repo already has enough shape to define these contracts.
- The strongest implemented support is for market context, QB/skill-position relevance, coaching context, and weather modifiers.
- Several position groups remain contract-only because the repo has the language and structure, but not a validated data lane.

