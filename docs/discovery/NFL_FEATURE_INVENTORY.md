# NFL Feature Inventory

This inventory groups the discovered NFL features by family and classifies them as atomic or composite.
It is based on the current code and report surfaces, not on hypothetical future NFL wishes.

Legend:

- `ATOMIC` = direct field or direct record attribute
- `COMPOSITE` = derived metric requiring multiple inputs or aggregation

| Feature family | Representative features | Type | Owner | Current maturity | Consumers / notes |
|---|---|---|---|---|---|
| Game identity and schedule | `game_id`, `season`, `week`, `home_team`, `away_team`, `stadium`, `roof`, `surface`, `temp`, `wind` | ATOMIC | `src.data.nfl_open_data_sources`, `src.data.nfl_open_data_field_catalog` | partial | Used in field catalog, scheduling, weather, and matchup summaries. |
| Final results and scoring | `home_score`, `away_score`, `result`, `points`, `yards`, `passing_yards`, `rushing_yards`, `receiving_yards` | ATOMIC / COMPOSITE | `src.data.nfl_open_data_sources`, `src.data.nfl_historical_pattern_lab` | partial | Supports results summaries and pattern-lab features. |
| Play-by-play efficiency | `epa`, `success_rate`, `yards_per_play`, `explosive_play_rate`, `negative_play_rate` | COMPOSITE | `src.providers.nfl_open_data_feature_builders`, `src.analytics.football_impact_report` | partial | Play-drive impact and efficiency diagnostics. |
| Drive and pace volume | `plays_per_game`, `seconds_per_play`, `offensive_plays`, `defensive_plays`, `drive_success_rate`, `points_per_drive` | COMPOSITE | `src.providers.nfl_open_data_feature_builders`, `src.market_intelligence.football_play_drive_impact` | partial | Current feature builders are blocked by no validated records. |
| Player availability | `player_id`, `player_name`, `position`, `snap_count`, `snap_share_recent`, `starter_status`, `injury_status`, `practice_status` | ATOMIC / COMPOSITE | `src.market_intelligence.football_availability_context`, `src.providers.nfl_open_data_feature_readiness` | partial | Availability and role-diagnostics inputs. |
| Roster continuity | `returning_players`, `roster_churn_rate`, `position_group_returning_rate` | COMPOSITE | `src.providers.nfl_open_data_feature_builders`, `src.data.nfl_historical_pattern_lab` | partial | Continuity features are ready in contract form, not yet fully populated. |
| Depth chart stability | `depth_position`, `depth_rank`, `projected_starter`, `depth_chart_changes`, `position_group_stability_proxy` | COMPOSITE | `src.providers.nfl_open_data_feature_builders`, `src.market_intelligence.nfl_cutoff_week_features` | scaffold | Existing code supports the concept; validated data is missing. |
| Injury and lineup context | `report_status`, `questionable_count`, `doubtful_count`, `out_count`, `availability_risk_proxy` | COMPOSITE | `src.providers.nfl_open_data_field_catalog`, `src.analytics.football_impact_report` | partial | Injury context is modeled as a risk modifier, not a live injury system. |
| Weather context | `weather`, `wind`, `temp`, `roof`, `weather_adjustment_score`, `weather_impact_score` | ATOMIC / COMPOSITE | `src.market_intelligence.football_availability_context`, `src.market_intelligence.football_market_relevance` | partial | Weather is a real modifier in the impact diagnostics path. |
| Market odds and price movement | `spread_line`, `total_line`, `moneyline`, `opening_line`, `closing_line`, `implied_probability`, `clv_proxy` | ATOMIC / COMPOSITE | `src.data.data_source_registry`, `src.data.historical_odds`, `src.market_intelligence.football_market_relevance` | partial | Public and historical odds are integrated in the platform, not NFL-specific only. |
| Coaching and staff | `head_coach`, `offensive_coordinator`, `defensive_coordinator`, `coaching_continuity_score`, `staff_turnover_candidate` | ATOMIC / COMPOSITE | `src.market_intelligence.nfl_coaching_sources`, `src.market_intelligence.nfl_coaching_feature_builders` | partial | Source and feature lanes exist, but most source families are blocked. |
| Officials | `official_id`, `official_name`, `position`, `official_tendency_proxy` | ATOMIC / COMPOSITE | `src.data.nfl_open_data_field_catalog`, `src.analytics.football_impact_report` | contract-only | Official fields are catalogued, but no fully validated usable lane was discovered. |
| Position-role context | `role`, `role_confidence_cap`, `role_impact_score`, `player_market_relevance` | COMPOSITE | `src.market_intelligence.football_role_impact` | partial | Central to the current football impact diagnostic surface. |
| Personnel / formation context | `offensive_personnel_rate_11`, `shotgun_rate`, `motion_rate`, `play_action_rate` | COMPOSITE | `src.market_intelligence.football_personnel_context` | partial | Current code models personnel fit and mismatch risk. |
| Matchup context | `qb_pressure_risk_score`, `wr_cb_matchup_score`, `ol_dl_run_matchup_score`, `mismatch_reasons` | COMPOSITE | `src.market_intelligence.football_matchup_context` | partial | Supports side, total, and prop relevance. |
| Incentive context | `contract_year`, `bonus_threshold_fabricated`, `narrative_overfit_risk` | COMPOSITE | `src.market_intelligence.football_incentive_context` | partial | Explicitly treated as modifier-only logic. |
| Market relevance scoring | `selected_market_relevance_score`, `market_relevance_scores`, `strongest_market_links` | COMPOSITE | `src.market_intelligence.football_market_relevance` | partial | Current market relevance engine. |
| Football impact diagnostics | `football_impact_score`, `data_tier`, `tier_name`, `calibration_status`, `red_team_status` | COMPOSITE | `src.analytics.football_impact_report`, `src.market_intelligence.response_compactor` | partial | The main NFL diagnostics payload. |
| Historical similarity / pattern lab | `points_for`, `points_against`, `point_differential`, `similarity_feature_catalog` | COMPOSITE | `src.data.nfl_historical_pattern_lab` | partial | Discovery and similarity work, not final model backtesting. |
| Cutoff-week / leakage controls | `cutoff_ts`, `snapshot_id`, `validation_guard_status`, `leakage_guard_status` | COMPOSITE | `src.market_intelligence.nfl_cutoff_week_features` | partial | This is the right shape for point-in-time feature snapshots. |
| Feature readiness / backfill status | `feature_builders_available`, `feature_builder_blockers`, `nfl_coaching_leakage_guard_status` | COMPOSITE | `src.providers.nfl_open_data_feature_readiness`, `src.providers.nfl_open_data_backfill` | partial | Readiness and backfill are surfaced but still discovery-heavy. |

## What is Already Real

The strongest discovered feature families are:

- game schedule / result context
- play-by-play efficiency
- player availability
- coaching/staff context
- market price context
- football impact diagnostics
- cutoff-week leakage controls

## What is Still Missing

- fully validated point-in-time NFL feature snapshots
- an end-to-end backtest dataset built from those snapshots
- a fully populated live/coaching/injury provider lane
- a stable official officials/injuries lane with validated data

## How to Read This Inventory

This document is intentionally conservative.
If a feature appears in the code but cannot be supported with validated data yet, it is treated as partial or contract-only rather than as production-ready.

