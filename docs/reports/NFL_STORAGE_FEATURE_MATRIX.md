# NFL Storage Feature Matrix

This matrix maps registry features to storage families.
It does not create tables or migrate data.

| Table family | Feature IDs | Primary join keys | Snapshot requirement | Lineage requirement | Versioning requirement | Validation requirement | Retention note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nfl_games | NFL_F001 NFL_F002 NFL_F003 | game_id season week team_id | schedule snapshot | source lineage_id | schema_version dataset_version | required key validation | permanent |
| nfl_teams | NFL_F002 | team_id league season | team identity snapshot | source lineage_id | schema_version dataset_version | canonical team validation | permanent |
| nfl_schedule | NFL_F001 NFL_F003 NFL_F011 NFL_F012 | schedule_id game_id team_id | kickoff snapshot | source lineage_id | schema_version dataset_version | kickoff and prior-game validation | permanent |
| nfl_results | NFL_F004 | result_id game_id | finalization snapshot | settlement lineage_id | schema_version dataset_version | outcome finalization | permanent |
| nfl_odds_snapshots | NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F010 | odds_snapshot_id game_id market book snapshot_time | odds snapshot | provider lineage_id | schema_version dataset_version version_id | decision_time and market validation | permanent |
| nfl_market_snapshots | NFL_F009 NFL_F039 | market_snapshot_id game_id market snapshot_time | market snapshot | provider lineage_id | feature_pack_version | snapshot order validation | permanent |
| nfl_team_stats_snapshots | NFL_F018 NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F024 NFL_F025 NFL_F029 NFL_F035 | team_stats_snapshot_id team_id game_id snapshot_time | prior-game snapshot | source lineage_id | schema_version dataset_version | historical cutoff validation | permanent |
| nfl_weather_snapshots | NFL_F013 NFL_F014 | weather_snapshot_id game_id forecast_time snapshot_time | forecast snapshot | provider lineage_id | schema_version dataset_version | forecast cutoff validation | permanent |
| nfl_injury_snapshots | NFL_F015 NFL_F016 NFL_F017 | injury_snapshot_id team_id player_id report_time | report snapshot | provider lineage_id | schema_version dataset_version | report_time validation | permanent |
| nfl_feature_snapshots | NFL_F009 NFL_F011 NFL_F012 NFL_F014 NFL_F016 NFL_F018 NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F024 NFL_F025 NFL_F026 NFL_F027 NFL_F028 NFL_F029 NFL_F031 NFL_F033 NFL_F034 NFL_F035 NFL_F036 NFL_F039 NFL_F041 | snapshot_id game_id feature_pack_version decision_time | feature snapshot | lineage_id dependency_versions | feature_pack_version schema_version | dependency and leakage validation | permanent |
| nfl_backtest_rows | NFL_F004 NFL_F008 NFL_F010 NFL_F040 | backtest_row_id game_id snapshot_id decision_time | decision snapshot | feature lineage_id | model_version schema_version | no future data validation | permanent |
| nfl_backtest_results | NFL_F010 NFL_F040 | backtest_run_id model_version feature_pack_version | run snapshot | run lineage_id | model_version feature_pack_version | reproducibility validation | permanent |
| deferred_storage | NFL_F037 NFL_F038 | pending | pending | pending | pending | provider and licensing review | no storage until approved |
