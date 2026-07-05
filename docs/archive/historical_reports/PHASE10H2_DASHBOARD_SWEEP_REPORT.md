# Phase 10H2 Dashboard Sweep Report

Generated: `2026-06-13T02:35:21Z`
- Branch: `phase-6-api-slimming`
- HEAD: `b9f461b`

## Executive Counts

```json
{
  "bankroll_signal_files": 404,
  "chart_signal_files": 351,
  "constants_found": 1227,
  "data_preview_paths": 8,
  "discovered_runtime_candidates": 488,
  "files": 1376,
  "functions_found": 7245,
  "json_files": 498,
  "jsonl_files": 1,
  "markdown_files": 45,
  "python_files": 725,
  "regression_signal_files": 269,
  "routes_found": 127,
  "sport_profile_options": 18,
  "sport_signal_files": 481,
  "table_signal_files": 417
}
```

## Professional Dashboard Decision

- `streamlit_should_be_visual_layer_only`: `True`
- `do_not_put_betting_logic_in_streamlit`: `True`
- `dashboard_helpers_should_be_tested_without_streamlit`: `True`
- `support_easy_mode`: `True`
- `support_power_user_mode`: `True`
- `support_raw_json_expandable_views`: `True`
- `support_bankroll_inputs`: `True`
- `support_regression_tactic_dropdown`: `True`
- `support_test_by_sport`: `True`
- `support_test_all_sports`: `True`

## Menu Plan

### Home / Explain Like I'm 8

Purpose: Simple status cards and plain-English explanation of what the model is doing.

**cards:**
- `Is the system safe?`
- `How much money did the test start with?`
- `How much money did the test end with?`
- `Did the graph go up or down?`
- `What sport/profile was tested?`
- `Is this ready or not ready?`

**charts:**
- `Bankroll up/down line`

**friendly_notes:**
- `Green means good.`
- `Red means warning.`
- `No real bet is placed from this screen.`

### Data Library

Purpose: Read all important JSON/Markdown/data files from dropdowns.

**dropdowns:**
- `data/backtests/canonical/latest.jsonl`
- `data/backtests/canonical/schema_report.json`
- `data/paper_ledger/latest.json`
- `data/review_queue/latest.json`
- `data/review_queue/review_queue.json`
- `data/system_health/health.json`

**tables:**
- `Preview rows`
- `Key/value summary`
- `Raw JSON expander`

**inputs:**
- `Preview row limit`
- `Search text`
- `Show raw JSON yes/no`

### Paper Bets

Purpose: Show paper ledger and review queue in readable tables.

**dropdowns:**
- `paper_ledger/latest.json`
- `review_queue/latest.json`
- `review_queue/review_queue.json`

**tables:**
- `Latest paper bets`
- `Review queue`
- `No-bet reasons`
- `Confirmed bet candidates`

**charts:**
- `Paper bets by sport`
- `Paper bets by market`
- `No-bet reason counts`

**inputs:**
- `Sport filter`
- `Market filter`
- `Show confirmed only`
- `Show no-bets only`

### Backtest Dashboard

Purpose: Show dashboard JSON output, performance, coverage, and readiness.

**dropdowns:**
- `latest_dashboard.json`
- `schema_report.json`
- `canonical dataset sample`

**tables:**
- `Field coverage`
- `Sport counts`
- `League counts`
- `Regression profile usage`
- `Failed promotion checks`

**charts:**
- `Bankroll curve`
- `ROI by run`
- `Drawdown`
- `Sport coverage percent`
- `Model probability vs market probability`
- `Edge buckets`
- `CLV buckets`

**inputs:**
- `Max rows`
- `Rebuild dataset yes/no`
- `Require core fields yes/no`

### Test One Sport

Purpose: Select one sport/profile and test current model formation.

**dropdowns:**
- `americanfootball_ncaaf`
- `americanfootball_nfl`
- `baseball_mlb`
- `basketball_nba`
- `basketball_ncaab`
- `basketball_ncaaw`
- `basketball_wnba`
- `combat_sports`
- `context_module`
- `crypto`
- `golf`
- `icehockey_nhl`
- `prediction_market`
- `soccer`
- `sportsbook`
- `stock`
- `tennis`

**tables:**
- `Rows used`
- `Decisions`
- `Bet/no-bet reasons`
- `Feature weights used`
- `Profile metadata`

**charts:**
- `Bankroll curve`
- `Profit/loss over decisions`
- `Edge buckets`
- `Win/loss/push counts`

**inputs:**
- `Sport/profile dropdown`
- `Starting bankroll`
- `Unit size`
- `Max rows`
- `Minimum edge`
- `Minimum model probability`
- `Regression tactic`
- `Intercept`
- `Probability floor`
- `Probability ceiling`
- `Override existing probability yes/no`

### Test All Sports

Purpose: Run all sports with current model formation.

**dropdowns:**
- `all_sports`
- `all_sports + sport_specific profiles`

**tables:**
- `All decisions`
- `Sport counts`
- `Profile usage`
- `Market counts`
- `Failed checks`

**charts:**
- `Bankroll curve`
- `Profit/loss curve`
- `Drawdown curve`
- `Sport contribution`
- `Profile contribution`

**inputs:**
- `Starting bankroll`
- `Unit size`
- `Max rows`
- `Regression tactic`
- `Use all_sports only`
- `Use sport_specific when available`

### Bankroll Settings

Purpose: Let user test bankroll assumptions without changing production logic.

**dropdowns:**
- `Conservative`
- `Moderate`
- `Aggressive`
- `Custom`

**tables:**
- `Current settings`
- `Risk explanation`

**charts:**
- `Bankroll curve preview`
- `Worst drop preview`

**inputs:**
- `Starting bankroll`
- `Unit size`
- `Max stake percent`
- `Daily stop loss`
- `Max drawdown stop`
- `Max bets per run`

**friendly_notes:**
- `Small unit = safer.`
- `Big unit = bigger swings.`
- `Stop loss means stop when losing too much.`

### Regression Tactics

Purpose: Choose how the model probability is formed for tests.

**dropdowns:**
- `Use existing model probability`
- `All-sports regression`
- `Sport-specific regression`
- `Custom feature weights`

**tables:**
- `Available features`
- `Feature weights`
- `Profile selected`
- `Probability calculation explanation`

**charts:**
- `Model probability histogram`
- `Edge histogram`
- `Market probability vs model probability`

**inputs:**
- `Intercept`
- `Feature weights`
- `Probability floor`
- `Probability ceiling`
- `Override model probability`

**friendly_notes:**
- `Intercept is the starting chance.`
- `Feature weights move the chance up or down.`
- `Floor and ceiling keep the chance from getting silly.`

### System Health

Purpose: Show whether repo/API/data paths are healthy.

**dropdowns:**
- `architecture guard`
- `dependency warning`
- `runtime files`
- `API endpoints`

**tables:**
- `Route inventory`
- `Files found`
- `Missing files`
- `Warnings`

**inputs:**
- `Refresh`
- `Run local health check`


## Recommended Dashboard Inputs

### Safe Defaults

```json
{
  "force_rebuild_dataset": false,
  "intercept": 0.5,
  "max_rows": 2000,
  "minimum_edge": 0.0,
  "minimum_model_probability": 0.0,
  "override_existing_probability": true,
  "probability_ceiling": 0.99,
  "probability_floor": 0.01,
  "require_core_fields": false,
  "starting_bankroll": 1000.0,
  "unit_size": 10.0
}
```

### Risk Presets

```json
{
  "Aggressive paper only": {
    "explanation": "Big swings. Paper testing only.",
    "max_drawdown_stop_percent": 25.0,
    "max_stake_percent": 8.0,
    "unit_size_percent": 5.0
  },
  "Conservative": {
    "explanation": "Small bets. Good for learning and paper testing.",
    "max_drawdown_stop_percent": 10.0,
    "max_stake_percent": 2.0,
    "unit_size_percent": 1.0
  },
  "Kid-safe demo / Tiny risk": {
    "explanation": "Tiny bets. Easy to watch. Very slow swings.",
    "max_drawdown_stop_percent": 5.0,
    "max_stake_percent": 0.5,
    "unit_size_percent": 0.25
  },
  "Moderate": {
    "explanation": "Bigger swings. Only for stronger evidence.",
    "max_drawdown_stop_percent": 15.0,
    "max_stake_percent": 4.0,
    "unit_size_percent": 2.0
  }
}
```

### Regression Tactics

```json
{
  "All-sports regression": {
    "friendly": "Use one simple tactic for every sport.",
    "mode": "sport_profiles",
    "profile_scope": "all_sports"
  },
  "Custom feature weights": {
    "friendly": "Let the user type feature weights.",
    "mode": "sport_profiles",
    "profile_scope": "custom"
  },
  "Sport-specific regression": {
    "friendly": "Pick the tactic that matches the sport.",
    "mode": "sport_profiles",
    "profile_scope": "auto"
  },
  "Use existing model probability": {
    "friendly": "Use the chance already in the data.",
    "mode": "existing_probability"
  }
}
```

## Easy Mode Glossary

| Field | Simple Name |
|---|---|
| `all_sports` | One model setup for every sport |
| `bankroll` | Money in the account |
| `bankroll_curve` | Line that shows money going up or down |
| `closing_line` | Final market price |
| `clv` | Closing line value |
| `drawdown` | How far the money dropped from the high point |
| `edge` | Model advantage |
| `ending_bankroll` | Money after test |
| `feature_weights` | Numbers that tell the model what matters more |
| `features_known_at_decision_time` | Info known before the bet |
| `final_result` | Final result |
| `intercept` | Starting chance before features move it |
| `league` | League |
| `market` | Bet type |
| `market_implied_probability` | Market chance |
| `max_drawdown_percent` | Worst drop percent |
| `model_probability` | Model chance |
| `odds` | Odds |
| `override_existing_probability` | Let this tactic replace the old model chance |
| `pnl` | Money won or lost |
| `probability_ceiling` | Highest chance allowed |
| `probability_floor` | Lowest chance allowed |
| `profile` | Model profile |
| `profile_name` | Model profile |
| `profit_loss` | Money won or lost |
| `regression tactic` | A way to turn features into a model chance |
| `roi_percent` | Return percent |
| `selected_profile_key` | Selected model profile |
| `sport` | Sport |
| `sport_specific` | A model setup picked for one sport |
| `stake` | Bet amount |
| `starting_bankroll` | Starting money |
| `unit_size` | Normal bet size |

## Data Preview Files

| Path | Exists | Kind | Size | Rows Estimate |
|---|---:|---|---:|---:|
| `data/backtests/dashboard/latest_dashboard.json` | `False` | `None` | `0` | `0` |
| `data/backtests/dashboard/latest_dashboard.md` | `False` | `None` | `0` | `0` |
| `data/backtests/canonical/latest.jsonl` | `True` | `jsonl` | `163034673` | `200` |
| `data/backtests/canonical/schema_report.json` | `True` | `json` | `27185` | `0` |
| `data/paper_ledger/latest.json` | `True` | `json` | `169349` | `100` |
| `data/review_queue/latest.json` | `True` | `json` | `646644` | `100` |
| `data/review_queue/review_queue.json` | `True` | `json` | `611542` | `100` |
| `data/system_health/health.json` | `True` | `json` | `9034` | `0` |

## Sport/Profile Options

| Label | Value | Scope |
|---|---|---|
| `All sports current formation` | `all_sports` | `all_sports` |
| `americanfootball_ncaaf` | `americanfootball_ncaaf` | `sport_specific` |
| `americanfootball_nfl` | `americanfootball_nfl` | `sport_specific` |
| `baseball_mlb` | `baseball_mlb` | `sport_specific` |
| `basketball_nba` | `basketball_nba` | `sport_specific` |
| `basketball_ncaab` | `basketball_ncaab` | `sport_specific` |
| `basketball_ncaaw` | `basketball_ncaaw` | `sport_specific` |
| `basketball_wnba` | `basketball_wnba` | `sport_specific` |
| `combat_sports` | `combat_sports` | `sport_specific` |
| `context_module` | `context_module` | `sport_specific` |
| `crypto` | `crypto` | `sport_specific` |
| `golf` | `golf` | `sport_specific` |
| `icehockey_nhl` | `icehockey_nhl` | `sport_specific` |
| `prediction_market` | `prediction_market` | `sport_specific` |
| `soccer` | `soccer` | `sport_specific` |
| `sportsbook` | `sportsbook` | `sport_specific` |
| `stock` | `stock` | `sport_specific` |
| `tennis` | `tennis` | `sport_specific` |

## Chart Candidates

| Source | Fields |
|---|---|
| `data/backtests/canonical/latest.jsonl` | `market_implied_probability, paper_roi_estimate` |
| `data/backtests/canonical/schema_report.json` | `closing_line, clv, coverage_percent, edge, market_implied_probability, model_probability, profit_loss` |
| `data/paper_ledger/latest.json` | `paper_roi_estimate` |
| `data/review_queue/latest.json` | `bankroll_id, bankroll_snapshot, drawdown_gate_result, estimated_roi_percent, model_probability` |
| `data/review_queue/review_queue.json` | `bankroll_id, bankroll_snapshot, drawdown_gate_result, estimated_roi_percent, model_probability` |
| `data/system_health/health.json` | `clv_sample_size` |
| `data/backtests/replay_contract-proof_2026-06-13T00_14_44.607133_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-12T18_28_38.815133_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T19_05_02.309603_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T19_24_29.117814_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T22_57_39.056740_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T23_52_50.953109_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T23_53_08.597707_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T23_58_59.484131_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-12T23_59_13.281526_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_00_44.691674_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_01_02.079711_00_00.json` | `model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_05_09.389503_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_05_37.100462_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_07_27.512944_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_07_47.074280_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_13_27.484368_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_13_49.044673_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_19_58.042387_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_20_23.021973_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_33_38.291639_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_34_03.796517_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_37_44.627258_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T00_38_16.908274_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T01_07_03.067151_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T01_07_42.514746_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T01_08_41.723027_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T01_09_23.847327_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T01_21_27.267707_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T01_22_57.159090_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_m2_2026-06-13T02_17_01.392206_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_phase10e-proof_2026-06-13T00_21_26.227956_00_00.json` | `market_implied_probability, model_probability` |
| `data/backtests/replay_phase10f-proof_2026-06-13T00_35_02.089893_00_00.json` | `market_implied_probability, model_probability, pace_edge` |
| `data/backtests/replay_phase10g2-sport-profile-proof_2026-06-13T01_10_26.329971_00_00.json` | `market_implied_probability, model_probability, pace_edge, starter_edge` |
| `data/backtests/replay_phase10g2-sport-profile-proof_2026-06-13T01_24_35.170258_00_00.json` | `market_implied_probability, model_probability, pace_edge, starter_edge` |
| `data/bankroll/test_bankroll.json` | `bankroll_id, closed_pnl, current_bankroll, current_drawdown_percent, peak_bankroll, starting_bankroll` |
| `data/bankroll/test_bankroll_redact.json` | `bankroll_id, closed_pnl, current_bankroll, current_drawdown_percent, peak_bankroll, starting_bankroll` |
| `data/calibration/calibration_2026-06-11T17_11_58.271695_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_13_39.127044_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_15_51.756840_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_22_15.545323_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_29_58.215931_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_38_59.334440_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_42_54.085542_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_46_19.296165_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_50_37.083090_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_52_15.170574_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_56_12.936312_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T17_57_12.379988_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_01_55.520987_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_04_36.145114_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_17_14.210087_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_21_36.544161_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_34_24.794077_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_38_35.316803_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T18_47_53.485204_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T19_47_58.839216_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T19_48_43.525527_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T19_52_57.611132_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T19_56_51.756786_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T21_38_17.140570_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T21_53_42.248392_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T21_58_01.224174_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T21_59_19.120768_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_00_36.841385_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_04_32.214186_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_07_20.336553_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_09_42.242286_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_11_07.140959_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_12_19.937668_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_12_53.259690_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_13_44.062392_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_14_11.255727_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_29_05.068583_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |
| `data/calibration/calibration_2026-06-11T22_35_23.066803_00_00.json` | `paper_ledger_records_count, paper_roi_estimate` |

## Table Candidates

| Source | Fields |
|---|---|
| `data/backtests/canonical/schema_report.json` | `artifacts_seen, dropped_rows, field_coverage, league_counts, raw_rows_found, rows_dropped, rows_written, schema_report_path, sport_counts` |
| `data/paper_ledger/latest.json` | `items, items_written_count` |
| `data/review_queue/latest.json` | `review_queue_gate_result` |
| `data/review_queue/review_queue.json` | `review_queue_gate_result` |
| `data/backtests/replay_contract-proof_2026-06-13T00_14_44.607133_00_00.json` | `rows` |
| `data/backtests/replay_default_model_2026-06-12T19_14_33.163472_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T18_28_38.815133_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T19_05_02.309603_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T19_24_29.117814_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T22_57_39.056740_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T23_52_50.953109_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T23_53_08.597707_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T23_58_59.484131_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-12T23_59_13.281526_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_00_44.691674_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_01_02.079711_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_05_09.389503_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_05_37.100462_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_07_27.512944_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_07_47.074280_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_13_27.484368_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_13_49.044673_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_19_58.042387_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_20_23.021973_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_33_38.291639_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_34_03.796517_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_37_44.627258_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T00_38_16.908274_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T01_07_03.067151_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T01_07_42.514746_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T01_08_41.723027_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T01_09_23.847327_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T01_21_27.267707_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T01_22_57.159090_00_00.json` | `rows` |
| `data/backtests/replay_m2_2026-06-13T02_17_01.392206_00_00.json` | `rows` |
| `data/backtests/replay_phase10e-proof_2026-06-13T00_21_26.227956_00_00.json` | `rows` |
| `data/backtests/replay_phase10f-proof_2026-06-13T00_35_02.089893_00_00.json` | `rows` |
| `data/backtests/replay_phase10g2-sport-profile-proof_2026-06-13T01_10_26.329971_00_00.json` | `rows` |
| `data/backtests/replay_phase10g2-sport-profile-proof_2026-06-13T01_24_35.170258_00_00.json` | `rows` |
| `data/calibration/calibration_2026-06-11T17_11_58.271695_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_13_39.127044_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_15_51.756840_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_22_15.545323_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_29_58.215931_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_38_59.334440_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_42_54.085542_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_46_19.296165_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_50_37.083090_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_52_15.170574_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_56_12.936312_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T17_57_12.379988_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_01_55.520987_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_04_36.145114_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_17_14.210087_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_21_36.544161_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_34_24.794077_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_38_35.316803_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T18_47_53.485204_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T19_47_58.839216_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T19_48_43.525527_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T19_52_57.611132_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T19_56_51.756786_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T21_38_17.140570_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T21_53_42.248392_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T21_58_01.224174_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T21_59_19.120768_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_00_36.841385_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_04_32.214186_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_07_20.336553_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_09_42.242286_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_11_07.140959_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_12_19.937668_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_12_53.259690_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_13_44.062392_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_14_11.255727_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_29_05.068583_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_35_23.066803_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_50_09.574637_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T22_54_37.995557_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |
| `data/calibration/calibration_2026-06-11T23_12_56.527875_00_00.json` | `matched_outcomes_count, paper_decisions_count, paper_ledger_records_count, review_items_available_count, review_items_count, unmatched_outcomes_count` |

## Dropdown Candidates

| Source | Fields |
|---|---|
| `data/backtests/canonical/latest.jsonl` | `market, provider` |
| `data/backtests/canonical/schema_report.json` | `artifact_summaries, league, league_counts, leakage_summary, market, mlb, nba, sport, sport_counts` |
| `data/paper_ledger/latest.json` | `provider` |
| `data/review_queue/latest.json` | `league, market, provider, sport, sport_or_symbol` |
| `data/review_queue/review_queue.json` | `league, market, provider, sport, sport_or_symbol` |
| `data/system_health/health.json` | `kalshi_average_review_priority_score, kalshi_flagged_low_liquidity_count, kalshi_flagged_partial_pricing_count, kalshi_high_priority_count, kalshi_liquidity_tier_counts, kalshi_missing_liquidity_count, kalshi_price_field_telemetry, market` |
| `data/backtests/replay_contract-proof_2026-06-13T00_14_44.607133_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_05_09.389503_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_05_37.100462_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_07_27.512944_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_07_47.074280_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_13_27.484368_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_13_49.044673_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_19_58.042387_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_20_23.021973_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_33_38.291639_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_34_03.796517_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_37_44.627258_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T00_38_16.908274_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T01_07_03.067151_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T01_07_42.514746_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T01_08_41.723027_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T01_09_23.847327_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T01_21_27.267707_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T01_22_57.159090_00_00.json` | `league, sport` |
| `data/backtests/replay_m2_2026-06-13T02_17_01.392206_00_00.json` | `league, sport` |
| `data/backtests/replay_phase10e-proof_2026-06-13T00_21_26.227956_00_00.json` | `league, sport` |
| `data/backtests/replay_phase10f-proof_2026-06-13T00_35_02.089893_00_00.json` | `league, sport` |
| `data/backtests/replay_phase10g2-sport-profile-proof_2026-06-13T01_10_26.329971_00_00.json` | `league, sport` |
| `data/backtests/replay_phase10g2-sport-profile-proof_2026-06-13T01_24_35.170258_00_00.json` | `league, sport` |
| `data/calibration/calibration_2026-06-11T17_11_58.271695_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_13_39.127044_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_15_51.756840_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_22_15.545323_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_29_58.215931_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_38_59.334440_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_42_54.085542_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_46_19.296165_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_50_37.083090_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_52_15.170574_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_56_12.936312_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T17_57_12.379988_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_01_55.520987_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_04_36.145114_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_17_14.210087_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_21_36.544161_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_34_24.794077_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_38_35.316803_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T18_47_53.485204_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T19_47_58.839216_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T19_48_43.525527_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T19_52_57.611132_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T19_56_51.756786_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T21_38_17.140570_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T21_53_42.248392_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T21_58_01.224174_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T21_59_19.120768_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_00_36.841385_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_04_32.214186_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_07_20.336553_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_09_42.242286_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_11_07.140959_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_12_19.937668_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_12_53.259690_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_13_44.062392_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_14_11.255727_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_29_05.068583_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_35_23.066803_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_50_09.574637_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T22_54_37.995557_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T23_12_56.527875_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-11T23_16_54.198289_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T12_21_45.157422_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T12_26_15.798536_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T13_43_00.030994_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T13_47_30.277761_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T13_57_45.199198_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T18_28_33.112137_00_00.json` | `kalshi_prediction_market` |
| `data/calibration/calibration_2026-06-12T18_28_38.676556_00_00.json` | `kalshi_prediction_market, prediction_market` |
| `data/calibration/calibration_2026-06-12T18_28_44.105475_00_00.json` | `kalshi_prediction_market, prediction_market` |

## Route Inventory For Future Dashboard API

| Method | Route | Function | File |
|---|---|---|---|
| `GET` | `/api/automation/health` | `get_automation_scheduler_health` | `/api/automation/health` |
| `GET` | `/api/automation/security-readiness` | `get_automation_security_readiness_endpoint` | `/api/automation/security-readiness` |
| `GET` | `/api/automation/intelligence-readiness` | `get_automation_intelligence_readiness_endpoint` | `/api/automation/intelligence-readiness` |
| `GET` | `/api/automation/strategy-readiness` | `get_automation_strategy_readiness_endpoint` | `/api/automation/strategy-readiness` |
| `GET` | `/api/automation/data-sources/registry` | `get_data_source_registry_endpoint` | `/api/automation/data-sources/registry` |
| `GET` | `/api/automation/data-sources/coverage` | `get_data_source_coverage_endpoint` | `/api/automation/data-sources/coverage` |
| `GET` | `/api/automation/data-sources/research-lanes` | `get_data_source_research_lanes_endpoint` | `/api/automation/data-sources/research-lanes` |
| `GET` | `/api/automation/data-sources/env-vars` | `get_data_source_env_vars_endpoint` | `/api/automation/data-sources/env-vars` |
| `GET` | `/api/automation/data-sources/priorities` | `get_data_source_priorities_endpoint` | `/api/automation/data-sources/priorities` |
| `GET` | `/api/automation/data-sources/public-apis-expansion-report` | `get_public_apis_expansion_report_endpoint` | `/api/automation/data-sources/public-apis-expansion-report` |
| `GET` | `/api/automation/data-sources/data-availability/tiers` | `get_data_availability_tiers_endpoint` | `/api/automation/data-sources/data-availability/tiers` |
| `GET` | `/api/automation/data-sources/health` | `get_data_source_health_endpoint` | `/api/automation/data-sources/health` |
| `POST` | `/api/automation/data-sources/adapters/ncaaf/cfbd/verify` | `verify_ncaaf_cfbd_adapter_endpoint` | `/api/automation/data-sources/adapters/ncaaf/cfbd/verify` |
| `POST` | `/api/automation/data-sources/verify` | `verify_data_source_registry_endpoint` | `/api/automation/data-sources/verify` |
| `POST` | `/api/automation/deepseek-review` | `automation_deepseek_review_endpoint` | `/api/automation/deepseek-review` |
| `POST` | `/api/automation/deepseek-red-team` | `automation_deepseek_red_team_endpoint` | `/api/automation/deepseek-red-team` |
| `GET` | `/api/automation/deepseek-disagreements` | `automation_deepseek_disagreements_endpoint` | `/api/automation/deepseek-disagreements` |
| `GET` | `/api/automation/deepseek-daily-report` | `automation_deepseek_daily_report_endpoint` | `/api/automation/deepseek-daily-report` |
| `GET` | `/api/automation/institutional-lab/health` | `get_institutional_lab_health_endpoint` | `/api/automation/institutional-lab/health` |
| `POST` | `/api/automation/institutional-lab/run` | `run_institutional_lab_endpoint` | `/api/automation/institutional-lab/run` |
| `GET` | `/api/automation/institutional-lab/report` | `get_institutional_lab_report_endpoint` | `/api/automation/institutional-lab/report` |
| `GET` | `/api/automation/institutional-lab/daily-report` | `get_institutional_lab_daily_report_endpoint` | `/api/automation/institutional-lab/daily-report` |
| `POST` | `/api/automation/institutional-lab/deepseek-review` | `institutional_lab_deepseek_review_endpoint` | `/api/automation/institutional-lab/deepseek-review` |
| `POST` | `/api/automation/institutional-lab/execution-desk/simulate` | `institutional_execution_desk_simulate_endpoint` | `/api/automation/institutional-lab/execution-desk/simulate` |
| `GET` | `/api/automation/institutional-lab/audit` | `get_institutional_lab_audit_endpoint` | `/api/automation/institutional-lab/audit` |
| `POST` | `/api/automation/manifold-map` | `automation_manifold_map_endpoint` | `/api/automation/manifold-map` |
| `GET` | `/api/automation/manifold-clusters` | `automation_manifold_clusters_endpoint` | `/api/automation/manifold-clusters` |
| `GET` | `/api/automation/manifold-calibration` | `automation_manifold_calibration_endpoint` | `/api/automation/manifold-calibration` |
| `GET` | `/api/automation/manifold-no-bet-traps` | `automation_manifold_no_bet_traps_endpoint` | `/api/automation/manifold-no-bet-traps` |
| `POST` | `/api/automation/cross-asset-manifold-review` | `automation_cross_asset_manifold_review_endpoint` | `/api/automation/cross-asset-manifold-review` |
| `GET` | `/api/automation/review-queue` | `get_automation_scheduler_review_queue` | `/api/automation/review-queue` |
| `GET` | `/api/automation/calibration` | `get_automation_calibration_endpoint` | `/api/automation/calibration` |
| `POST` | `/api/automation/outcomes/ingest` | `ingest_automation_outcomes_endpoint` | `/api/automation/outcomes/ingest` |
| `POST` | `/api/automation/outcomes/import-local-settlements` | `import_local_kalshi_settlements_endpoint` | `/api/automation/outcomes/import-local-settlements` |
| `GET` | `/api/automation/outcomes` | `get_automation_outcomes_endpoint` | `/api/automation/outcomes` |
| `POST` | `/api/automation/outcomes/discover-settlements` | `discover_automation_outcome_settlements_endpoint` | `/api/automation/outcomes/discover-settlements` |
| `POST` | `/api/automation/calibration-collector/run` | `run_automation_calibration_collector_endpoint` | `/api/automation/calibration-collector/run` |
| `POST` | `/api/automation/calibration-collector/scheduled-run` | `run_automation_calibration_collector_scheduled_endpoint` | `/api/automation/calibration-collector/scheduled-run` |
| `POST` | `/api/automation/run-once` | `run_automation_scheduler_once` | `/api/automation/run-once` |
| `POST` | `/api/automation/pattern-detect` | `detect_small_account_patterns_endpoint` | `/api/automation/pattern-detect` |
| `POST` | `/api/automation/small-account-review` | `run_small_account_review_endpoint` | `/api/automation/small-account-review` |
| `GET` | `/api/automation/pattern-review-queue` | `get_small_account_pattern_review_queue_endpoint` | `/api/automation/pattern-review-queue` |
| `GET` | `/api/automation/pattern-calibration` | `get_small_account_pattern_calibration_endpoint` | `/api/automation/pattern-calibration` |
| `GET` | `/api/automation/micro-outcome-calibration` | `get_small_account_micro_outcome_calibration_endpoint` | `/api/automation/micro-outcome-calibration` |
| `GET` | `/api/automation/broker-quality` | `get_small_account_broker_quality_endpoint` | `/api/automation/broker-quality` |
| `GET` | `/api/automation/balance-sheet-risk/{symbol}` | `get_small_account_balance_sheet_risk_endpoint` | `/api/automation/balance-sheet-risk/{symbol}` |
| `GET` | `/api/automation/basketball-player-impact-readiness` | `get_automation_basketball_player_impact_readiness_endpoint` | `/api/automation/basketball-player-impact-readiness` |
| `POST` | `/api/automation/basketball-player-impact` | `automation_basketball_player_impact_endpoint` | `/api/automation/basketball-player-impact` |
| `GET` | `/api/automation/advanced-red-team-report` | `get_automation_advanced_red_team_report_endpoint` | `/api/automation/advanced-red-team-report` |
| `GET` | `/api/automation/extreme-randomness-report` | `get_automation_extreme_randomness_report_endpoint` | `/api/automation/extreme-randomness-report` |
| `GET` | `/api/automation/football-impact-readiness` | `get_automation_football_impact_readiness_endpoint` | `/api/automation/football-impact-readiness` |
| `POST` | `/api/automation/football-impact-diagnostics` | `automation_football_impact_diagnostics_endpoint` | `/api/automation/football-impact-diagnostics` |
| `GET` | `/api/automation/soccer-impact-readiness` | `get_automation_soccer_impact_readiness_endpoint` | `/api/automation/soccer-impact-readiness` |
| `POST` | `/api/automation/soccer-impact-diagnostics` | `automation_soccer_impact_diagnostics_endpoint` | `/api/automation/soccer-impact-diagnostics` |
| `GET` | `/api/automation/hockey-impact-readiness` | `get_automation_hockey_impact_readiness_endpoint` | `/api/automation/hockey-impact-readiness` |
| `POST` | `/api/automation/hockey-impact-diagnostics` | `automation_hockey_impact_diagnostics_endpoint` | `/api/automation/hockey-impact-diagnostics` |
| `GET` | `/api/automation/baseball-impact-readiness` | `get_automation_baseball_impact_readiness_endpoint` | `/api/automation/baseball-impact-readiness` |
| `POST` | `/api/automation/baseball-impact-diagnostics` | `automation_baseball_impact_diagnostics_endpoint` | `/api/automation/baseball-impact-diagnostics` |
| `GET` | `/api/automation/golf-impact-readiness` | `get_automation_golf_impact_readiness_endpoint` | `/api/automation/golf-impact-readiness` |
| `POST` | `/api/automation/golf-impact-diagnostics` | `automation_golf_impact_diagnostics_endpoint` | `/api/automation/golf-impact-diagnostics` |
| `GET` | `/api/automation/combat-impact-readiness` | `get_automation_combat_impact_readiness_endpoint` | `/api/automation/combat-impact-readiness` |
| `POST` | `/api/automation/combat-impact-diagnostics` | `automation_combat_impact_diagnostics_endpoint` | `/api/automation/combat-impact-diagnostics` |
| `GET` | `/api/automation/tennis-impact-readiness` | `get_automation_tennis_impact_readiness_endpoint` | `/api/automation/tennis-impact-readiness` |
| `POST` | `/api/automation/tennis-impact-diagnostics` | `automation_tennis_impact_diagnostics_endpoint` | `/api/automation/tennis-impact-diagnostics` |
| `POST` | `/api/automation/extreme-signal-diagnostics` | `automation_extreme_signal_diagnostics_endpoint` | `/api/automation/extreme-signal-diagnostics` |
| `POST` | `/api/automation/advanced-shape-diagnostics` | `automation_advanced_shape_diagnostics_endpoint` | `/api/automation/advanced-shape-diagnostics` |
| `GET` | `/api/betting/events/active` | `get_active_betting_events` | `/api/betting/events/active` |
| `GET` | `/api/actions/betting/events/active` | `action_get_active_betting_events` | `/api/actions/betting/events/active` |
| `GET` | `/api/actions/models/sports-registry` | `action_get_sports_model_registry` | `/api/actions/models/sports-registry` |
| `POST` | `/api/actions/models/sport-analysis` | `action_analyze_sport_model` | `/api/actions/models/sport-analysis` |
| `POST` | `/api/actions/ticket/screenshot-analysis` | `action_analyze_ticket_screenshot` | `/api/actions/ticket/screenshot-analysis` |
| `POST` | `/api/actions/betting/log-bet` | `action_log_bet` | `/api/actions/betting/log-bet` |
| `POST` | `/api/actions/betting/log-result` | `action_log_bet_result` | `/api/actions/betting/log-result` |
| `GET` | `/api/actions/betting/logs` | `action_get_bet_logs` | `/api/actions/betting/logs` |
| `GET` | `/api/actions/betting/performance-summary` | `action_get_performance_summary` | `/api/actions/betting/performance-summary` |
| `GET` | `/api/actions/betting/bankroll-summary` | `action_get_bankroll_summary` | `/api/actions/betting/bankroll-summary` |
| `GET` | `/api/actions/betting/clv-report` | `action_get_clv_report` | `/api/actions/betting/clv-report` |
| `GET` | `/api/betting/events/{event_id}/odds` | `get_event_odds_endpoint` | `/api/betting/events/{event_id}/odds` |
| `GET` | `/api/actions/betting/events/{event_id}/odds` | `action_get_event_odds` | `/api/actions/betting/events/{event_id}/odds` |
| `GET` | `/api/betting/first-event-odds` | `get_first_event_odds` | `/api/betting/first-event-odds` |
| `GET` | `/api/actions/betting/first-event-odds` | `action_get_first_event_odds` | `/api/actions/betting/first-event-odds` |
| `POST` | `/api/actions/betting/evaluate-lines` | `action_evaluate_betting_lines` | `/api/actions/betting/evaluate-lines` |
| `POST` | `/api/actions/betting/price-event` | `action_price_betting_event` | `/api/actions/betting/price-event` |
| `POST` | `/api/actions/betting/model-probability` | `action_calculate_model_probability` | `/api/actions/betting/model-probability` |
| `POST` | `/api/actions/betting/analyze-event` | `action_analyze_betting_event` | `/api/actions/betting/analyze-event` |
| `GET` | `/api/betting/providers` | `get_betting_providers` | `/api/betting/providers` |
| `GET` | `/api/betting/sports` | `get_supported_betting_sports` | `/api/betting/sports` |
| `POST` | `/api/bets/log` | `log_bet` | `/api/bets/log` |
| `GET` | `/api/bets/summary` | `get_bet_summary` | `/api/bets/summary` |
| `GET` | `/api/debug/config` | `debug_config` | `/api/debug/config` |
| `GET` | `/api/debug/auth-status` | `auth_status` | `/api/debug/auth-status` |
| `GET` | `/api/governance/health` | `get_governance_health_endpoint` | `/api/governance/health` |
| `GET` | `/api/governance/inventory` | `get_governance_inventory_endpoint` | `/api/governance/inventory` |
| `GET` | `/api/governance/report` | `get_governance_report_endpoint` | `/api/governance/report` |
| `POST` | `/api/governance/validate` | `validate_governance_endpoint` | `/api/governance/validate` |
| `GET` | `/api/markets/providers` | `get_market_providers` | `/api/markets/providers` |
| `GET` | `/api/markets/kalshi/events` | `get_kalshi_events` | `/api/markets/kalshi/events` |
| `GET` | `/api/markets/kalshi/markets` | `get_kalshi_markets` | `/api/markets/kalshi/markets` |
| `GET` | `/api/markets/kalshi/markets/{ticker}/orderbook` | `get_kalshi_orderbook` | `/api/markets/kalshi/markets/{ticker}/orderbook` |
| `GET` | `/odds/live` | `odds_live` | `/odds/live` |
| `GET` | `/odds/the-odds-api/live` | `the_odds_api_live` | `/odds/the-odds-api/live` |
| `GET` | `/odds/the-odds-api/test` | `the_odds_api_test` | `/odds/the-odds-api/test` |
| `GET` | `/math/catalog` | `math_catalog` | `/math/catalog` |
| `GET` | `/odds/opportunities/live` | `odds_opportunities_live` | `/odds/opportunities/live` |
| `GET` | `/model/live-card` | `model_live_card` | `/model/live-card` |
| `GET` | `/model/backtest` | `model_backtest` | `/model/backtest` |
| `GET` | `/api/performance/health` | `get_performance_health_endpoint` | `/api/performance/health` |
| `GET` | `/api/performance/report` | `get_performance_report_endpoint` | `/api/performance/report` |
| `POST` | `/api/performance/backtest` | `run_performance_backtest_endpoint` | `/api/performance/backtest` |
| `POST` | `/api/performance/paper-summary` | `run_performance_paper_summary_endpoint` | `/api/performance/paper-summary` |
| `GET` | `/api/providers/health` | `get_providers_health_endpoint` | `/api/providers/health` |
| `GET` | `/api/providers/registry` | `get_providers_registry_endpoint` | `/api/providers/registry` |
| `GET` | `/api/providers/sharp/health` | `get_sharp_provider_health_endpoint` | `/api/providers/sharp/health` |
| `POST` | `/api/providers/sharp/snapshot` | `create_sharp_provider_snapshot_endpoint` | `/api/providers/sharp/snapshot` |
| `GET` | `/api/providers/kalshi/health` | `get_kalshi_provider_health_endpoint` | `/api/providers/kalshi/health` |
| `POST` | `/api/providers/kalshi/snapshot` | `create_kalshi_provider_snapshot_endpoint` | `/api/providers/kalshi/snapshot` |
| `POST` | `/quant/bet-analysis` | `quant_bet_analysis` | `/quant/bet-analysis` |
| `POST` | `/quant/market-pricing` | `quant_market_pricing` | `/quant/market-pricing` |
| `POST` | `/quant/stock-analysis` | `quant_stock_analysis` | `/quant/stock-analysis` |
| `GET` | `/api/stocks/{ticker}` | `get_stock_data` | `/api/stocks/{ticker}` |
| `GET` | `/api/watchlist` | `get_watchlist_data` | `/api/watchlist` |
| `GET` | `/api/analyze` | `analyze` | `/api/analyze` |
| `GET` | `/` | `root` | `/` |
| `HEAD` | `/` | `root_head` | `/` |
| `GET` | `/health` | `health_check` | `/health` |
| `GET` | `/ping` | `ping` | `/ping` |
| `GET` | `/debug/routes` | `debug_routes` | `/debug/routes` |

## Streamlit Implementation Rules

- Build `automation_scheduler/streamlit_dashboard_data.py` first.
- Keep all logic testable without Streamlit installed.
- `streamlit_app.py` should only render menus, dropdowns, tables, charts, and buttons.
- Every raw JSON preview should have a simple table view and an expandable raw view.
- Every money/risk input should have a plain-English explanation.
- Default mode should be safe and paper-only.

## Next Step

Use this report to build the Streamlit operator dashboard with the exact menus, dropdowns, and safe inputs identified here.

