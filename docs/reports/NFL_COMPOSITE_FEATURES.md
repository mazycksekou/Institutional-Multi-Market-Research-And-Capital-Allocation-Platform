# NFL Composite Features

Composite features are deterministic calculations derived from atomic inputs or approved intermediate features.
They must declare their dependencies before implementation.

| Feature ID | Feature | Required atomic or parent inputs | Calculation description | Aggregation level | Time window | Market scope | Backtest role | Streamlit group | Model usage | Leakage classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFL_F009 | pregame market movement | NFL_F005 NFL_F006 NFL_F007 NFL_F008 | compare open and pre-decision snapshots | market game | pregame cutoff | spread moneyline totals | market context | odds movement | market signal | LEAKAGE_RISK |
| NFL_F010 | closing line value | NFL_F008 closing price | compare decision price to closing price | market run | post-decision | all priced markets | evaluation metric | CLV summary | excluded from pregame input | POST_EVENT_ONLY |
| NFL_F011 | rest days | NFL_F001 NFL_F003 | days between previous kickoff and current kickoff | team game | pregame | all markets | core context | feature readiness | model context | POINT_IN_TIME_SAFE |
| NFL_F012 | travel distance | NFL_F001 NFL_F002 venue geography | estimate travel burden | team game | pregame | all markets | context feature | feature readiness | model context | POINT_IN_TIME_SAFE |
| NFL_F014 | weather impact score | NFL_F013 | weighted effect of wind temperature roof surface | game market | pregame forecast | totals passing kicking | core context | weather panel | modifier input | LEAKAGE_RISK |
| NFL_F016 | injury adjusted availability | NFL_F015 NFL_F017 NFL_F035 | adjust unit strength for unavailable players | unit game | pregame report | all markets | core signal | leakage warnings | modifier input | LEAKAGE_RISK |
| NFL_F018 | roster continuity | NFL_F002 NFL_F035 | compare current participation to prior weeks | team unit | rolling prior games | all markets | stabilizer | feature readiness | stabilizer input | CUTOFF_REQUIRED |
| NFL_F019 | offensive efficiency recent | prior play and drive data | rolling offensive efficiency | team | rolling prior games | spread moneyline totals | core signal | feature panel | model input | CUTOFF_REQUIRED |
| NFL_F020 | defensive efficiency recent | prior play and drive data | rolling defensive efficiency | team | rolling prior games | spread moneyline totals | core signal | feature panel | model input | CUTOFF_REQUIRED |
| NFL_F021 | pace play volume recent | prior plays drives snaps | rolling play volume and tempo | team | rolling prior games | spread totals props | core signal | feature panel | model input | CUTOFF_REQUIRED |
| NFL_F022 | red zone efficiency | red zone trips conversions | conversions divided by trips | team | rolling prior games | spread totals props | efficiency feature | feature panel | model input | CUTOFF_REQUIRED |
| NFL_F023 | third down efficiency | third downs conversions | conversion or stop rate | team | rolling prior games | spread totals | efficiency feature | feature panel | model input | CUTOFF_REQUIRED |
| NFL_F024 | explosive play rate | explosive plays total plays | explosive plays divided by plays | team | rolling prior games | spread totals props | optional context | advanced panel | optional input | CUTOFF_REQUIRED |
| NFL_F025 | turnover rate trend | turnovers plays games | rolling turnover rate and regression proxy | team | rolling prior games | spread moneyline totals | optional context | advanced panel | optional input | CUTOFF_REQUIRED |
| NFL_F026 | offensive line score | pressure allowed run block continuity | weighted unit score | unit | rolling prior games | team and player markets | unit strength | feature panel | model input | LEAKAGE_RISK |
| NFL_F027 | defensive line pressure score | pressure sacks run stops | weighted disruption score | unit | rolling prior games | team and player markets | unit strength | feature panel | model input | LEAKAGE_RISK |
| NFL_F028 | pass rush pressure allowed | NFL_F026 NFL_F027 dropbacks | pressure allowed matchup proxy | unit matchup | rolling prior games | passing sacks totals | unit matchup | feature panel | model input | LEAKAGE_RISK |
| NFL_F029 | special teams efficiency | kicking returns coverage | weighted special teams index | team unit | rolling prior games | spread totals props | context feature | feature panel | optional input | CUTOFF_REQUIRED |
| NFL_F031 | official crew tendency | NFL_F030 historical tendencies | historical official tendency index | crew game | prior assignments | totals penalties props | context feature | feature panel | optional input | LEAKAGE_RISK |
| NFL_F033 | coaching continuity | NFL_F032 staff history | staff continuity and turnover score | team season | pregame season | all markets | stabilizer | feature readiness | stabilizer input | CUTOFF_REQUIRED |
| NFL_F034 | draft capital combine context | draft pick combine measures | long-term player prior | player | static historical | player and team markets | optional context | advanced panel | optional input | POINT_IN_TIME_SAFE |
| NFL_F036 | route participation target share | snaps routes targets | route and target usage blend | player | rolling prior games | player props totals | deferred | deferred | future input | LEAKAGE_RISK |
| NFL_F037 | tracking data bundle | tracking source fields | paid or advanced tracking features | player | unknown | player props | deferred | deferred | future input | DEFERRED_UNKNOWN |
| NFL_F038 | player props input bundle | player usage matchup market fields | player prop feature pack | player market | pregame | player props | deferred | deferred | future input | DEFERRED_UNKNOWN |
| NFL_F039 | market relevance score | NFL_F009 NFL_F011 NFL_F012 NFL_F014 NFL_F016 NFL_F019 NFL_F020 NFL_F026 NFL_F027 | rank signal relevance by market | market game | pregame | all priced markets | ranking feature | diagnostics | ranking input | LEAKAGE_RISK |
| NFL_F040 | calibration confidence | NFL_F004 NFL_F010 sample size | confidence in calibrated evidence | market run | postgame | all markets | governance gate | calibration chart | governance input | POST_EVENT_ONLY |
| NFL_F041 | pattern similarity score | historical feature profiles | similarity against prior matchup profiles | game team | historical prior periods | all markets | optional research | research diagnostics | research input | CUTOFF_REQUIRED |
