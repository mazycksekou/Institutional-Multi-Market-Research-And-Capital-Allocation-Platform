# NFL Feature Registry

This registry is the canonical planning reference for NFL features.
It does not implement providers, ingestion, feature engineering, models, dashboards, or backtests.

Every future NFL implementation phase should reference this table before adding a field, calculation, storage column, dashboard widget, research experiment, or model input.

## Discovery Basis

The registry consolidates the current repository evidence from:

- `docs/reports/NFL_FEATURE_PRIORITY_MATRIX.md`
- `docs/contracts/NFL_ATOMIC_FEATURE_CONTRACT.md`
- `docs/contracts/NFL_COMPOSITE_FEATURE_CONTRACT.md`
- `docs/contracts/NFL_POSITION_GROUP_FEATURE_CONTRACT.md`
- `docs/reports/NFL_PROVIDER_SOURCE_MAPPING.md`
- `docs/reports/NFL_STORAGE_JOIN_KEY_BLUEPRINT.md`
- `src/data/nfl_open_data_field_catalog.py`
- `src/providers/nfl_open_data_feature_builders.py`
- `src/providers/nfl_open_data_feature_readiness.py`
- `src/market_intelligence/nfl_cutoff_week_features.py`
- `src/market_intelligence/nfl_coaching_feature_builders.py`
- `src/backtesting/backtest_schema.py`
- `src/services/streamlit_dashboard_data.py`

## Scoring and Status Legend

Scores use `1` to `5`, where `5` is strongest or highest.
For cost, noise, leakage risk, and difficulty, `5` means highest burden or risk.

Readiness statuses:

- `Ready`
- `Needs Provider`
- `Needs Calculation`
- `Needs Validation`
- `Needs Research`
- `Deferred`
- `Blocked`

Leakage classifications:

- `POINT_IN_TIME_SAFE`
- `CUTOFF_REQUIRED`
- `LEAKAGE_RISK`
- `RESULT_ONLY`
- `POST_EVENT_ONLY`
- `DEFERRED_UNKNOWN`

## Canonical Registry

| Feature ID | Feature Name | Feature Family | Feature Category | Atomic/Composite | Owner | Profile Family | Description | Business Purpose | Market Usage | Backtest Usage | Research Usage | Dashboard Usage | Model Usage | Storage Destination | Validation Usage | Leakage Classification | Readiness Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NFL_F001 | game_id season week kickoff home_away | schedule_results | schedule | Atomic | src.data | sports:nfl | Stable game identity and schedule context | deterministic joins | spread moneyline totals | join key and partition | evidence anchor | dataset readiness | partitioning only | nfl_games nfl_schedule | required key validation | POINT_IN_TIME_SAFE | Ready |
| NFL_F002 | team identity | team_identity | identity | Atomic | src.data | sports:nfl | Team identifiers and home away role | stable grouping | spread moneyline totals | grouping key | cohort analysis | dataset readiness | grouping only | nfl_teams nfl_games | required key validation | POINT_IN_TIME_SAFE | Ready |
| NFL_F003 | kickoff timing | schedule_results | timestamp | Atomic | src.data | sports:nfl | Scheduled kickoff and event timing | decision cutoff alignment | all baseline markets | temporal split | timing audits | leakage warnings | cutoff control | nfl_schedule nfl_games | timestamp validation | POINT_IN_TIME_SAFE | Ready |
| NFL_F004 | final score result | schedule_results | outcome | Atomic | src.backtesting | sports:nfl | Settled score and result labels | outcome settlement | all baseline markets | label only | evaluation analysis | backtest summary | not a feature input | nfl_results nfl_backtest_rows | outcome finalization | RESULT_ONLY | Needs Validation |
| NFL_F005 | market open spread | market_odds | odds | Atomic | src.data | sports:nfl | Opening spread line with snapshot metadata | baseline market price | spread | baseline spread row | market efficiency research | odds panel | pricing input | nfl_odds_snapshots | snapshot timestamp validation | CUTOFF_REQUIRED | Needs Provider |
| NFL_F006 | market open total | market_odds | odds | Atomic | src.data | sports:nfl | Opening total line with snapshot metadata | baseline totals price | totals | baseline totals row | totals efficiency research | odds panel | pricing input | nfl_odds_snapshots | snapshot timestamp validation | CUTOFF_REQUIRED | Needs Provider |
| NFL_F007 | market open moneyline | market_odds | odds | Atomic | src.data | sports:nfl | Opening moneyline price | baseline comparison price | moneyline | baseline moneyline row | moneyline efficiency research | odds panel | pricing input | nfl_odds_snapshots | snapshot timestamp validation | CUTOFF_REQUIRED | Needs Provider |
| NFL_F008 | odds at decision time | market_odds | odds | Atomic | src.data | sports:nfl | Price frozen at model decision time | reproducible bet simulation | spread moneyline totals | decision price | cutoff timing research | odds panel | pricing input | nfl_odds_snapshots nfl_backtest_rows | decision_time validation | CUTOFF_REQUIRED | Needs Provider |
| NFL_F009 | pregame market movement | market_odds | market_context | Composite | src.market_intelligence | sports:nfl | Difference between open and pre-decision snapshots | market information flow | spread moneyline totals | market context | line movement ablation | odds movement view | market signal | nfl_market_snapshots nfl_feature_snapshots | cutoff and snapshot order | LEAKAGE_RISK | Needs Calculation |
| NFL_F010 | closing line value | market_odds | performance | Composite | src.backtesting | sports:nfl | Difference between decision price and closing price | post-decision performance evidence | all priced markets | evaluation metric | market efficiency research | CLV summary | not pregame feature | nfl_backtest_results | post-decision only validation | POST_EVENT_ONLY | Needs Validation |
| NFL_F011 | rest days | rest_travel | context | Composite | src.market_intelligence | sports:nfl | Days since prior game for each team | schedule fatigue context | all baseline markets | core context | rest hypothesis testing | feature readiness | model context | nfl_schedule nfl_feature_snapshots | prior-game cutoff | POINT_IN_TIME_SAFE | Needs Calculation |
| NFL_F012 | travel distance | rest_travel | context | Composite | src.market_intelligence | sports:nfl | Estimated travel burden from venue history | fatigue context | all baseline markets | context feature | travel hypothesis testing | feature readiness | model context | nfl_schedule nfl_feature_snapshots | venue and schedule validation | POINT_IN_TIME_SAFE | Needs Calculation |
| NFL_F013 | weather forecast inputs | stadium_weather | weather | Atomic | src.data | sports:nfl | Forecast temperature wind roof precipitation surface | game environment | totals passing kicking | context field | weather research | weather panel | modifier input | nfl_weather_snapshots | forecast_time validation | CUTOFF_REQUIRED | Needs Provider |
| NFL_F014 | weather impact score | stadium_weather | weather | Composite | src.market_intelligence | sports:nfl | Expected market effect from forecast conditions | environment adjustment | totals passing kicking | core context | weather ablation | weather panel | modifier input | nfl_feature_snapshots | forecast cutoff validation | LEAKAGE_RISK | Needs Calculation |
| NFL_F015 | injury status | injury_lineup | availability | Atomic | src.data | sports:nfl | Player injury and report status | availability context | all markets | optional context | availability research | leakage warnings | modifier input | nfl_injury_snapshots | report_time validation | LEAKAGE_RISK | Needs Provider |
| NFL_F016 | injury adjusted availability | injury_lineup | availability | Composite | src.market_intelligence | sports:nfl | Team or unit availability adjusted for player role | core availability signal | all markets | core signal | injury ablation | leakage warnings | modifier input | nfl_feature_snapshots | report_time and decision_time validation | LEAKAGE_RISK | Needs Calculation |
| NFL_F017 | depth chart rank starter status | depth_chart | availability | Atomic | src.data | sports:nfl | Depth chart role and starter status | role context | team and player markets | player context | role research | feature readiness | conditioning input | nfl_injury_snapshots nfl_feature_snapshots | source timestamp validation | LEAKAGE_RISK | Needs Provider |
| NFL_F018 | roster continuity | roster_continuity | availability | Composite | src.market_intelligence | sports:nfl | Continuity of roster and participation across prior weeks | team stability | all baseline markets | stabilizer | continuity ablation | feature readiness | stabilizer input | nfl_team_stats_snapshots nfl_feature_snapshots | prior-week cutoff | CUTOFF_REQUIRED | Needs Calculation |
| NFL_F019 | offensive efficiency recent | play_by_play_efficiency | team_efficiency | Composite | src.market_intelligence | sports:nfl | Rolling offensive efficiency from prior games | team strength signal | spread moneyline totals | core signal | offensive strength research | feature panel | model input | nfl_team_stats_snapshots nfl_feature_snapshots | historical cutoff validation | CUTOFF_REQUIRED | Needs Calculation |
| NFL_F020 | defensive efficiency recent | defensive_profile | team_efficiency | Composite | src.market_intelligence | sports:nfl | Rolling defensive efficiency from prior games | opponent strength signal | spread moneyline totals | core signal | defensive strength research | feature panel | model input | nfl_team_stats_snapshots nfl_feature_snapshots | historical cutoff validation | CUTOFF_REQUIRED | Needs Calculation |
| NFL_F021 | pace play volume recent | pace_play_volume | team_efficiency | Composite | src.market_intelligence | sports:nfl | Rolling play volume and tempo context | totals and opportunity context | spread totals props | core signal | pace research | feature panel | model input | nfl_team_stats_snapshots nfl_feature_snapshots | historical cutoff validation | CUTOFF_REQUIRED | Needs Calculation |
| NFL_F022 | red zone efficiency | play_by_play_efficiency | scoring_profile | Composite | src.market_intelligence | sports:nfl | Red zone conversion rate from prior games | scoring efficiency | spread totals props | efficiency feature | red zone hypothesis | feature panel | model input | nfl_team_stats_snapshots nfl_feature_snapshots | drive cutoff validation | CUTOFF_REQUIRED | Needs Calculation |
| NFL_F023 | third down efficiency | play_by_play_efficiency | scoring_profile | Composite | src.market_intelligence | sports:nfl | Third down conversion or prevention rate | drive sustainability | spread totals | efficiency feature | efficiency ablation | feature panel | model input | nfl_team_stats_snapshots nfl_feature_snapshots | play cutoff validation | CUTOFF_REQUIRED | Needs Calculation |
| NFL_F024 | explosive play rate | play_by_play_efficiency | scoring_profile | Composite | src.market_intelligence | sports:nfl | Prior-game explosive play rate | volatility and upside | spread totals props | optional context | explosiveness research | advanced panel | optional model input | nfl_team_stats_snapshots nfl_feature_snapshots | play cutoff validation | CUTOFF_REQUIRED | Needs Research |
| NFL_F025 | turnover rate trend | play_by_play_efficiency | volatility | Composite | src.market_intelligence | sports:nfl | Rolling turnover rate and luck proxy | volatility context | spread moneyline totals | optional context | turnover regression research | advanced panel | optional model input | nfl_team_stats_snapshots nfl_feature_snapshots | outcome cutoff validation | CUTOFF_REQUIRED | Needs Research |
| NFL_F026 | offensive line score | roster_continuity | position_unit | Composite | src.market_intelligence | sports:nfl | Protection and run-blocking unit score | matchup strength | spread totals player props | unit strength | line matchup research | feature panel | model input | nfl_feature_snapshots | prior-game and roster validation | LEAKAGE_RISK | Needs Research |
| NFL_F027 | defensive line pressure score | defensive_profile | position_unit | Composite | src.market_intelligence | sports:nfl | Pressure and run-stop unit score | matchup strength | spread totals sacks props | unit strength | line matchup research | feature panel | model input | nfl_feature_snapshots | prior-game validation | LEAKAGE_RISK | Needs Research |
| NFL_F028 | pass rush pressure allowed | play_by_play_efficiency | position_unit | Composite | src.market_intelligence | sports:nfl | Pressure allowed per dropback proxy | matchup weakness | passing sacks totals | unit matchup | pressure research | feature panel | model input | nfl_feature_snapshots | source and cutoff validation | LEAKAGE_RISK | Needs Research |
| NFL_F029 | special teams efficiency | play_by_play_efficiency | special_teams | Composite | src.market_intelligence | sports:nfl | Kicking coverage and return efficiency proxy | hidden yardage context | spread totals props | context feature | special teams research | feature panel | optional model input | nfl_team_stats_snapshots nfl_feature_snapshots | prior-game validation | CUTOFF_REQUIRED | Needs Research |
| NFL_F030 | official crew identity | officials | officiating | Atomic | src.data | sports:nfl | Assigned official crew identity | officiating context | totals penalties props | context key | official tendency research | feature readiness | context only | nfl_market_snapshots nfl_feature_snapshots | assignment timestamp validation | CUTOFF_REQUIRED | Needs Provider |
| NFL_F031 | official crew tendency | officials | officiating | Composite | src.market_intelligence | sports:nfl | Historical official tendency derived from prior games | game environment context | totals penalties props | context feature | official ablation | feature panel | optional model input | nfl_feature_snapshots | historical-only validation | LEAKAGE_RISK | Needs Calculation |
| NFL_F032 | coaching staff identity | coaching_staff | coaching | Atomic | src.data | sports:nfl | Head coach and coordinator identity | team context | all baseline markets | context key | staff research | feature readiness | context only | nfl_team_stats_snapshots | season timestamp validation | POINT_IN_TIME_SAFE | Ready |
| NFL_F033 | coaching continuity | coaching_staff | coaching | Composite | src.market_intelligence | sports:nfl | Continuity of head coach coordinator and staff | team stability | all baseline markets | stabilizer | coaching continuity research | feature readiness | stabilizer input | nfl_feature_snapshots | season and staff validation | CUTOFF_REQUIRED | Needs Validation |
| NFL_F034 | draft capital combine context | draft_capital | player_profile | Composite | src.research | sports:nfl | Draft and combine profile context | long-term player prior | player and team markets | optional context | player development research | advanced panel | optional model input | nfl_feature_snapshots | static source validation | POINT_IN_TIME_SAFE | Deferred |
| NFL_F035 | player usage snaps | player_availability | participation | Atomic | src.data | sports:nfl | Prior-game offensive defensive and special teams snaps | role and usage context | team props player props | usage feature | role research | feature panel | model conditioning | nfl_team_stats_snapshots nfl_feature_snapshots | prior-game cutoff validation | CUTOFF_REQUIRED | Needs Validation |
| NFL_F036 | route participation target share | player_availability | participation | Composite | src.market_intelligence | sports:nfl | Route and target share context for skill players | receiving usage | player props totals | deferred player feature | player usage research | deferred | future model input | nfl_feature_snapshots | participation source validation | LEAKAGE_RISK | Deferred |
| NFL_F037 | tracking data bundle | advanced_tracking | player_tracking | Composite | src.research | sports:nfl | Paid or unavailable tracking level features | advanced player modeling | player props | deferred | tracking research | deferred | future model input | deferred_storage | licensing and timing review | DEFERRED_UNKNOWN | Deferred |
| NFL_F038 | player props input bundle | player_props | player_market | Composite | src.market_intelligence | sports:nfl | Player prop feature set requiring stable player data | later player market modeling | player props | deferred | player prop research | deferred | future model input | deferred_storage | provider readiness validation | DEFERRED_UNKNOWN | Deferred |
| NFL_F039 | market relevance score | market_context | ranking | Composite | src.analytics | sports:nfl | Blend of matchup role context and market relevance | opportunity ranking | all priced markets | ranking feature | market triage research | diagnostics | ranking input | nfl_feature_snapshots | feature dependency validation | LEAKAGE_RISK | Needs Research |
| NFL_F040 | calibration confidence | calibration | governance | Composite | src.analytics | sports:nfl | Confidence in calibration based on sample and market context | governance evidence | all markets | pass fail gate | calibration research | calibration chart | governance input | nfl_backtest_results | settled-outcome validation | POST_EVENT_ONLY | Needs Validation |
| NFL_F041 | pattern similarity score | research_patterns | research | Composite | src.research | sports:nfl | Similarity of current matchup to historical profiles | research discovery | all markets | optional research context | pattern lab | research diagnostics | research input | nfl_feature_snapshots | historical partition validation | CUTOFF_REQUIRED | Needs Research |

## Registry Governance

- Result-only and post-event features may support evaluation, but must not enter pregame feature snapshots.
- Deferred features stay documented so future implementation can decide consciously rather than rediscovering the same question.
- Composite features must point to atomic inputs in the dependency graph before implementation.
- A feature is not implementation-ready until its source timing, storage target, validation rule, and leakage class are documented.
