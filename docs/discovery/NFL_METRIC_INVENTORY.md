# NFL Metric Inventory

This inventory classifies the metrics discovered during the NFL audit.
Metrics are grouped by whether they are raw inputs, derived features, model outputs, risk/performance metrics, or governance metadata.

## Raw Input Metrics

Raw inputs are fields that arrive directly from a source or canonical record.

Examples discovered in the repo include:

- identifiers: `game_id`, `season`, `week`, `team`, `player_id`, `player_name`, `official_id`, `official_name`
- roster fields: `position`, `starter_status`, `depth_position`, `depth_rank`, `jersey_number`
- participation fields: `snap_count`, `offense_snaps`, `defense_snaps`, `st_snaps`, `player_participation`
- game context: `home_team`, `away_team`, `stadium`, `roof`, `surface`, `temp`, `wind`, `weather`
- market context: `spread_line`, `total_line`, `moneyline`, `opening_line`, `closing_line`, `odds_at_decision_time`
- availability context: `injury_status`, `practice_status`, `report_status`, `rest_days`, `travel_distance`
- coaching context: `head_coach`, `offensive_coordinator`, `defensive_coordinator`
- source metadata: `source_id`, `source_type`, `schema_version`, `run_id`, `record_ts`

## Derived Feature Metrics

Derived metrics are calculated from raw inputs or from other derived metrics.

Examples discovered in the repo include:

- efficiency: `epa`, `success_rate`, `yards_per_play`, `explosive_play_rate`, `negative_play_rate`
- drive quality: `drive_success_rate`, `points_per_drive`, `red_zone_td_rate`, `finishing_drives_points_per_trip`
- volume: `plays_per_game`, `seconds_per_play`, `offensive_plays`, `defensive_plays`
- availability: `snap_share_recent`, `route_share`, `target_share`, `carry_share`, `injury_risk_score`, `snap_stability_score`
- coaching: `coaching_continuity_score`, `staff_turnover_candidate`
- matchup: `qb_pressure_risk_score`, `wr_cb_matchup_score`, `ol_dl_run_matchup_score`
- market relevance: `selected_market_relevance_score`, `market_relevance_scores`
- weather: `weather_adjustment_score`, `weather_impact_score`, `wind_risk_score`
- historical similarity: `similarity_score`, `pattern_similarity_score`

## Model Feature Metrics

Metrics that are clearly intended for model or diagnostics usage:

- `role_impact_score`
- `play_impact_score`
- `football_impact_score`
- `calibration_confidence`
- `role_confidence_cap`
- `market_relevance_scores`
- `football_impact_readiness`

## Risk Metrics

Metrics used to suppress confidence or to flag caution:

- `injury_risk_score`
- `starting_qb_market_risk_score`
- `qb_pressure_risk_score`
- `wind_risk_score`
- `narrative_overfit_risk`
- `downgrade_score`
- `leakage_guard_status`
- `validation_guard_status`
- `confidence_cap_reason`

## Performance / Outcome Metrics

Metrics used to assess predictive or betting performance:

- `expected_value`
- `expected_value_per_unit`
- `kelly_fraction`
- `clv_proxy`
- `roi_proxy`
- `calibration_status`
- `calibration_buckets`
- `settled_outcome`
- `actual_result`

## Governance / Metadata Metrics

Metrics that describe the health and provenance of the data or pipeline:

- `data_tier`
- `tier_name`
- `source_id`
- `source_type`
- `blocked_reason`
- `availability_status`
- `schema_version`
- `feature_pack_version`
- `lineage_id`
- `snapshot_id`
- `cutoff_ts`
- `run_id`

## Current Metric Takeaway

The repo already has a rich set of football metrics, but most of the higher-value metrics are still in discovery or contract form rather than fully backed by validated NFL historical data.

That is the right shape for Phase 4.1.

