# NFL Storage and Join Key Blueprint

This blueprint defines the table families required for the first reusable NFL vertical slice.
The goal is to make joins and snapshots deterministic before any model is built.

## Table Families

| Table family | Primary key | Natural key | Foreign keys | Timestamp fields | Version fields | Source / provider fields | Quality fields | Lineage fields |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nfl_games | `game_id` | season + week + home_team_id + away_team_id + kickoff_time | home_team_id, away_team_id, venue_id | kickoff_time, created_at, updated_at | schema_version, dataset_version, version_id | source, provider, source_snapshot_time | quality_score, completeness_score | lineage_id |
| nfl_teams | `team_id` | league + team_code | none or conference_id | created_at, updated_at | schema_version, dataset_version | source, provider | quality_score | lineage_id |
| nfl_schedule | `schedule_id` | season + week + game_id | game_id, home_team_id, away_team_id | kickoff_time, created_at, updated_at | schema_version, dataset_version | source, provider | quality_score | lineage_id |
| nfl_results | `result_id` | game_id | game_id | game_time, final_scored_at, created_at | schema_version, dataset_version | source, provider, settlement_source | quality_score, finalization_status | lineage_id |
| nfl_odds_snapshots | `odds_snapshot_id` | game_id + book + market + snapshot_time | game_id | snapshot_time, decision_time, created_at | schema_version, dataset_version, version_id | source, provider, book, market | quality_score, freshness_score | lineage_id |
| nfl_market_snapshots | `market_snapshot_id` | game_id + market + snapshot_time | game_id | snapshot_time, decision_time, created_at | schema_version, dataset_version, version_id | source, provider, market_type | quality_score | lineage_id |
| nfl_team_stats_snapshots | `team_stats_snapshot_id` | team_id + game_id + snapshot_time | team_id, game_id | snapshot_time, created_at | schema_version, dataset_version, version_id | source, provider | quality_score, completeness_score | lineage_id |
| nfl_weather_snapshots | `weather_snapshot_id` | game_id + snapshot_time + source_type | game_id | forecast_time, snapshot_time, created_at | schema_version, dataset_version, version_id | source, provider | quality_score, forecast_freshness | lineage_id |
| nfl_injury_snapshots | `injury_snapshot_id` | team_id + player_id + snapshot_time | team_id, player_id, game_id | report_time, snapshot_time, created_at | schema_version, dataset_version, version_id | source, provider, report_source | quality_score, timing_confidence | lineage_id |
| nfl_feature_snapshots | `snapshot_id` | feature_pack_version + decision_time + game_id | game_id | decision_time, snapshot_time, created_at | feature_pack_version, schema_version, dataset_version | source, provider, feature_pack_name | quality_score, leakage_score | lineage_id |
| nfl_backtest_rows | `backtest_row_id` | game_id + model_version + decision_time | game_id, snapshot_id | decision_time, created_at | model_version, schema_version, dataset_version | source, provider | quality_score, outcome_finalized | lineage_id |
| nfl_backtest_results | `backtest_run_id` | model_version + feature_pack_version + evaluation_window | backtest_row_id, feature_pack_version | run_time, created_at, updated_at | model_version, feature_pack_version, schema_version | source, provider | quality_score, reproducibility_score | lineage_id |

## Join Key Rules

- Every game row must have a stable `game_id`.
- Every snapshot row must carry a timestamp and a version identifier.
- Every feature row must point back to the snapshot that created it.
- Every backtest row must point back to the exact feature snapshot used at decision time.
- No model row may join to postgame truth as if it were a pregame input.

## Required Reproducibility Fields

- `schema_version`
- `dataset_version`
- `version_id`
- `source`
- `provider`
- `snapshot_time`
- `decision_time`
- `lineage_id`
- `quality_score`

