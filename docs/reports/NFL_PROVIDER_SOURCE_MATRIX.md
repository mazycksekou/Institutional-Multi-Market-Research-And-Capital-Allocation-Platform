# NFL Provider Source Matrix

This matrix maps registry features to source categories.
It does not enable providers or perform ingestion.

| Feature IDs | Feature family | Preferred source categories | Historical availability | Point-in-time availability | Local computability | Provider dependency | Licensing concerns | Confidence | Future maintenance cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFL_F001 NFL_F002 NFL_F003 NFL_F004 | schedule_results team_identity | OPEN_DATA LOCAL_CSV LOCAL_JSON SQLITE DUCKDB | high | high | high | low | low | high | low |
| NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F009 NFL_F010 | market_odds | FREE_API LOCAL_CSV LOCAL_JSON OPEN_DATA MANUAL_EXPORT | medium | medium only with snapshots | medium | medium | terms review required | medium | medium |
| NFL_F011 NFL_F012 | rest_travel | COMPUTED OPEN_DATA LOCAL_CSV LOCAL_JSON | high | high | high | low | low | high | low |
| NFL_F013 NFL_F014 | stadium_weather | FREE_API OPEN_DATA LOCAL_JSON COMPUTED | medium | medium only with forecast time | medium | medium | terms review required | medium | medium |
| NFL_F015 NFL_F016 NFL_F017 NFL_F018 NFL_F035 NFL_F036 | injury_lineup depth_chart roster_continuity player_availability | OPEN_DATA LOCAL_JSON MANUAL_EXPORT PAID_OR_DEFERRED COMPUTED | medium | medium only with report timestamps | medium | medium | medium | medium | high |
| NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F024 NFL_F025 | play_by_play_efficiency defensive_profile scoring_profile pace_play_volume | OPEN_DATA LOCAL_PARQUET SQLITE DUCKDB COMPUTED | high | high if cutoff enforced | high | low | low | high | medium |
| NFL_F026 NFL_F027 NFL_F028 NFL_F029 | position_unit special_teams | OPEN_DATA LOCAL_PARQUET SQLITE DUCKDB COMPUTED | medium | medium | medium | medium | medium | medium | high |
| NFL_F030 NFL_F031 | officials | OPEN_DATA FREE_API LOCAL_CSV COMPUTED | medium | medium | medium | medium | terms review required | medium | medium |
| NFL_F032 NFL_F033 | coaching_staff | OPEN_DATA LOCAL_CSV LOCAL_JSON COMPUTED | medium | high if season timestamped | high | low | low to medium | medium | medium |
| NFL_F034 | draft_capital | OPEN_DATA LOCAL_CSV MANUAL_EXPORT | high | high | high | low | low | medium | low |
| NFL_F037 NFL_F038 | advanced_tracking player_props | PAID_OR_DEFERRED UNKNOWN | unknown | unknown | low | high | high | low | high |
| NFL_F039 NFL_F040 NFL_F041 | market_context calibration research_patterns | COMPUTED SQLITE DUCKDB | depends on inputs | depends on inputs | high | inherited | inherited | medium | medium |

## Source Mapping Rule

Future implementation should prefer local and open sources first.
Paid or private data should remain deferred until the baseline team/game slice proves that the added complexity is necessary.
