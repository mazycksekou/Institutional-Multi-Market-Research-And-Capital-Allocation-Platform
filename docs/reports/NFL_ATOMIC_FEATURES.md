# NFL Atomic Features

Atomic features are direct fields or normalized source fields.
They may be used as inputs, join keys, labels, or dashboard fields, but they do not hide derived calculations.

| Feature ID | Feature | Source field examples | Datatype | Unit | Position scope | Market scope | Backtest role | Streamlit group | Model usage | Leakage classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFL_F001 | game_id season week kickoff home_away | game_id season week kickoff_time home_team away_team | string integer datetime | mixed | all | all baseline markets | join key | dataset readiness | partitioning only | POINT_IN_TIME_SAFE |
| NFL_F002 | team identity | team team_abbr home_team away_team | string | id | all | all baseline markets | grouping key | dataset readiness | grouping only | POINT_IN_TIME_SAFE |
| NFL_F003 | kickoff timing | kickoff_time event_date game_date | datetime | timestamp | all | all baseline markets | cutoff control | leakage warnings | cutoff control | POINT_IN_TIME_SAFE |
| NFL_F004 | final score result | home_score away_score final_result margin total | number string | points result | all | all baseline markets | label only | backtest summary | excluded from feature inputs | RESULT_ONLY |
| NFL_F005 | market open spread | spread_line open_spread | number | points | all | spread | price input | odds panel | pricing input | CUTOFF_REQUIRED |
| NFL_F006 | market open total | total_line open_total | number | points | all | totals | price input | odds panel | pricing input | CUTOFF_REQUIRED |
| NFL_F007 | market open moneyline | moneyline open_moneyline | number | price | all | moneyline | price input | odds panel | pricing input | CUTOFF_REQUIRED |
| NFL_F008 | odds at decision time | odds_at_decision_time recommended_odds | number | price | all | all priced markets | decision price | odds panel | pricing input | CUTOFF_REQUIRED |
| NFL_F013 | weather forecast inputs | temp wind precipitation roof surface | number string | weather units | all | totals passing kicking | context input | weather panel | modifier input | CUTOFF_REQUIRED |
| NFL_F015 | injury status | injury_status report_status practice_status | string | status | all players | all markets | optional context | leakage warnings | modifier input | LEAKAGE_RISK |
| NFL_F017 | depth chart rank starter status | pos_rank depth_team starter_status | string integer bool | rank state | all players | team and player markets | context input | feature readiness | conditioning input | LEAKAGE_RISK |
| NFL_F030 | official crew identity | official_id official_name position | string | id text | officials | totals penalties props | context key | feature readiness | context only | CUTOFF_REQUIRED |
| NFL_F032 | coaching staff identity | head_coach coordinator coach_id | string | id text | coaches | all baseline markets | context key | feature readiness | context only | POINT_IN_TIME_SAFE |
| NFL_F035 | player usage snaps | offense_snaps defense_snaps st_snaps | integer | snaps | all players | team and player markets | usage input | feature panel | conditioning input | CUTOFF_REQUIRED |

## Atomic Feature Policy

- Atomic features are allowed to be keys, source fields, labels, or model inputs depending on leakage class.
- Atomic does not mean model-safe.
- `RESULT_ONLY` atomic fields are required for backtesting but forbidden from pregame feature snapshots.
