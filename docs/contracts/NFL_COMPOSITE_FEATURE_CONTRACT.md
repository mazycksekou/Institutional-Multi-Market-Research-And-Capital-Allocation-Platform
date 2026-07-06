# NFL Composite Feature Contract

Composite features are deterministic calculations derived from multiple atomic inputs or approved intermediate features.

## Composite Feature Contract Fields

Each composite feature must define:

- `canonical_name`
- `required_atomic_inputs`
- `formula_or_calculation_description`
- `aggregation_level`
- `time_window`
- `allowed_positions`
- `allowed_markets`
- `required_for_backtest`
- `streamlit_display_group`
- `model_usage`
- `leakage_risk`

## Canonical Composite Feature Examples

| canonical_name | required_atomic_inputs | formula_or_calculation_description | aggregation_level | time_window | allowed_positions | allowed_markets | required_for_backtest | streamlit_display_group | model_usage | leakage_risk |
|---|---|---|---|---|---|---|---|---|---|---|
| `red_zone_percentage` | red-zone opportunities, red-zone conversions | red-zone conversions divided by red-zone opportunities | team / game | season / rolling | all | totals / spreads / props | yes | team efficiency | team model input | medium |
| `offensive_line_score` | pressure allowed proxies, run-block proxies, continuity | weighted blend of protection and run-block measures | unit | rolling | OL | rushing / passing / sacks | yes | offensive line | matchup input | medium |
| `defensive_line_pressure_score` | pressure rate, sack rate, disruption rate | weighted disruption and pressure index | unit | rolling | DL / EDGE | sacks / totals / props | yes | defensive line | matchup input | medium |
| `injury_adjusted_unit_score` | injury status, starter availability, snap share, depth changes | unit score after availability adjustments | unit | pregame | all | all | yes | availability | modifier input | high |
| `rest_advantage` | rest days, short-week flag, travel distance | normalized rest/travel advantage score | game | pregame | all | all | yes | availability | modifier input | medium |
| `travel_fatigue_score` | travel distance, time zone shift, rest days | travel fatigue estimate | game | pregame | all | all | no | availability | modifier input | medium |
| `weather_impact_score` | wind, temp, roof, surface | expected weather effect on market families | game | pregame | all | totals / passing / kicking | yes | weather | modifier input | medium |
| `quarterback_pressure_allowed_rate` | pressure to sack, dropbacks, pressure allowed proxy | pressure allowed per dropback estimate | player / unit | rolling | QB / OL | passing / sacks | yes | quarterback / offensive line | model input | high |
| `run_blocking_index` | run-block success proxy, box count, carry efficiency | weighted run-block measure | unit | rolling | RB / OL | rushing | yes | run game | model input | medium |
| `football_impact_score` | play-drive, role, matchup, availability, market relevance | composite diagnostic score used by the football impact report | game / role / market | pregame | multiple | multiple | no | football impact diagnostics | diagnostic / triage | medium |
| `market_relevance_score` | role impact, matchup context, weather, availability | market-specific relevance blend | market | pregame | multiple | multiple | yes | market relevance | ranking input | medium |
| `calibration_confidence` | matched outcomes, sample size, market role context | confidence level in calibration result | market / role | postgame | multiple | multiple | yes | calibration | governance input | low |
| `clv_proxy` | open odds, close odds | close-line-value proxy | market | postgame | all | all priced markets | yes | calibration / performance | performance input | low |
| `roi_proxy` | stakes, open odds, settled outcomes | return-on-investment proxy | market / run | postgame | all | all | yes | performance | performance input | low |
| `pattern_similarity_score` | team profiles, matchup profiles, season profiles | similarity between historical team/game profiles | team / game | historical | all | all | no | pattern lab | research input | low |

## Composite Feature Policy

- composite features must be deterministic
- formulas should be explicit and versioned
- every composite must be reproducible from archived inputs
- no composite feature should silently use future data

