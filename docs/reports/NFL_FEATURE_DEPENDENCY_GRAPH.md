# NFL Feature Dependency Graph

This graph describes dependencies between canonical NFL features.
It is a design artifact only; it does not implement calculations.

## Dependency Summary

| Feature ID | Feature | Required inputs | Optional inputs | Parent features | Child features | Validation dependencies | Storage dependencies | Research dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFL_F009 | pregame market movement | NFL_F005 NFL_F006 NFL_F007 NFL_F008 | book count market timestamp | market open lines | NFL_F039 | snapshot order and cutoff | nfl_market_snapshots | line movement ablation |
| NFL_F010 | closing line value | NFL_F008 closing price | market type book | odds at decision time | NFL_F040 | post-decision isolation | nfl_backtest_results | CLV research |
| NFL_F011 | rest days | NFL_F001 NFL_F003 | prior game venue | schedule context | NFL_F039 | prior-game cutoff | nfl_feature_snapshots | rest hypothesis |
| NFL_F012 | travel distance | NFL_F001 NFL_F002 | venue location | schedule context | NFL_F039 | venue completeness | nfl_feature_snapshots | travel hypothesis |
| NFL_F014 | weather impact score | NFL_F013 NFL_F003 | roof surface | weather forecast inputs | NFL_F039 | forecast_time cutoff | nfl_feature_snapshots | weather ablation |
| NFL_F016 | injury adjusted availability | NFL_F015 NFL_F017 NFL_F035 | position value | injury and role inputs | NFL_F039 | report_time and role cutoff | nfl_feature_snapshots | availability ablation |
| NFL_F018 | roster continuity | NFL_F002 NFL_F035 | transactions | team and participation inputs | NFL_F026 NFL_F033 | prior-week cutoff | nfl_feature_snapshots | continuity research |
| NFL_F019 | offensive efficiency recent | NFL_F001 prior play data | opponent strength | historical team stats | NFL_F039 | cutoff week validation | nfl_team_stats_snapshots | offensive strength |
| NFL_F020 | defensive efficiency recent | NFL_F001 prior play data | opponent strength | historical team stats | NFL_F039 | cutoff week validation | nfl_team_stats_snapshots | defensive strength |
| NFL_F021 | pace play volume recent | NFL_F001 prior play data | game script | historical team stats | NFL_F014 NFL_F039 | cutoff week validation | nfl_team_stats_snapshots | pace research |
| NFL_F022 | red zone efficiency | red zone trips red zone conversions NFL_F019 | drive context | offensive efficiency | NFL_F039 | drive cutoff validation | nfl_team_stats_snapshots | scoring research |
| NFL_F023 | third down efficiency | third downs conversions NFL_F019 NFL_F020 | game state | offensive and defensive efficiency | NFL_F039 | play cutoff validation | nfl_team_stats_snapshots | efficiency research |
| NFL_F024 | explosive play rate | explosive plays total plays NFL_F021 | opponent strength | pace and play-by-play | NFL_F039 | play cutoff validation | nfl_team_stats_snapshots | explosiveness research |
| NFL_F025 | turnover rate trend | turnovers plays games | turnover margin | play-by-play history | NFL_F039 | postgame label isolation | nfl_team_stats_snapshots | turnover regression |
| NFL_F026 | offensive line score | NFL_F018 pressure allowed proxy run block proxy | injuries | roster continuity and line data | NFL_F028 NFL_F039 | roster and prior-game cutoff | nfl_feature_snapshots | unit matchup |
| NFL_F027 | defensive line pressure score | pressure rate sack rate run stop rate | injuries | defensive profile | NFL_F028 NFL_F039 | prior-game cutoff | nfl_feature_snapshots | unit matchup |
| NFL_F028 | pass rush pressure allowed | NFL_F026 NFL_F027 dropbacks pressure proxy | QB profile | line scores | NFL_F039 | source cutoff validation | nfl_feature_snapshots | pressure matchup |
| NFL_F029 | special teams efficiency | field goal punt kick return events | weather | prior special teams data | NFL_F039 | prior-game cutoff | nfl_feature_snapshots | hidden yardage |
| NFL_F031 | official crew tendency | NFL_F030 historical official data | penalty rates | official identity | NFL_F039 | assignment timing | nfl_feature_snapshots | officiating research |
| NFL_F033 | coaching continuity | NFL_F032 historical staff identity | coordinator role | coaching identity | NFL_F039 | season timestamp validation | nfl_feature_snapshots | coaching research |
| NFL_F039 | market relevance score | NFL_F009 NFL_F011 NFL_F012 NFL_F014 NFL_F016 NFL_F019 NFL_F020 NFL_F026 NFL_F027 | NFL_F029 NFL_F031 NFL_F033 | market and matchup context | research triage | dependency completeness | nfl_feature_snapshots | market triage |
| NFL_F040 | calibration confidence | NFL_F004 NFL_F010 backtest sample size | market buckets | outcomes and CLV | governance gate | settled outcome validation | nfl_backtest_results | calibration research |
| NFL_F041 | pattern similarity score | NFL_F019 NFL_F020 NFL_F021 NFL_F039 | season profile | historical feature profiles | research suggestions | historical partition validation | nfl_feature_snapshots | pattern lab |

## Graph Rules

- Feature snapshots must store dependency versions.
- Composite features must not consume post-event fields unless the feature is explicitly marked `POST_EVENT_ONLY`.
- Backtests must join to the exact snapshot used at decision time.
- Research features may be exploratory, but their source timing must still be documented.
