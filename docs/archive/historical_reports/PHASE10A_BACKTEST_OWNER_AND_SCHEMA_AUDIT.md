# Phase 10A Backtest Owner and Schema Audit

Generated: 2026-06-12T19:44:34

- HEAD: `ef175eb`
- Git clean at audit start: `False`
```text
?? PHASE10_MODEL_BACKTEST_READINESS_SCAN.md
```

## Target Files
- `automation_scheduler/backtesting.py`: `67` lines, `3` functions, `0` classes, `7` dict literals
- `automation_scheduler/backtesting_engine.py`: `223` lines, `6` functions, `0` classes, `7` dict literals
- `automation_scheduler/historical_replay.py`: `77` lines, `5` functions, `0` classes, `3` dict literals

## Function / Class Inventory

### automation_scheduler/backtesting.py

Functions:
- `_group_counts` line `8`
- `_reason_counts` line `16`
- `run_backtesting_scaffold` line `28`

Classes:
- none

### automation_scheduler/backtesting_engine.py

Functions:
- `_to_float` line `22`
- `_paper_rows_from_replay_rows` line `29`
- `compare_expected_vs_realized` line `65`
- `run_backtest` line `80`
- `run_paper_summary` line `189`
- `generate_backtest_report` line `205`

Classes:
- none

### automation_scheduler/historical_replay.py

Functions:
- `_to_float` line `11`
- `load_historical_rows` line `18`
- `replay_rows` line `32`
- `write_replay_result` line `58`
- `summarize_replay_result` line `69`

Classes:
- none

## Import Sites

### automation_scheduler.backtesting
- Import sites: `1`
- `tests/test_backtesting.py` line `3`: `from automation_scheduler.backtesting import run_backtesting_scaffold`

### automation_scheduler.backtesting_engine
- Import sites: `1`
- `tests/test_backtesting_engine.py` line `6`: `from automation_scheduler.backtesting_engine import generate_backtest_report, run_backtest`

### automation_scheduler.historical_replay
- Import sites: `1`
- `tests/test_historical_replay.py` line `5`: `from automation_scheduler.historical_replay import (`

## Required Dataset Field / Alias Coverage
- `event_id` aliases found in `245` python files. aliases=`event_id, event, game_id, match_id, fixture_id`
- `contract_id` aliases found in `111` python files. aliases=`contract_id, kalshi_contract_id, ticker, market_id`
- `sport` aliases found in `294` python files. aliases=`sport, sport_key, league_sport`
- `league` aliases found in `101` python files. aliases=`league, competition, season_league`
- `market` aliases found in `472` python files. aliases=`market, market_type, bet_type, prop_type`
- `decision_time` aliases found in `122` python files. aliases=`decision_time, created_at, timestamp, bet_time, placed_at, paper_created_at`
- `odds_at_decision_time` aliases found in `285` python files. aliases=`odds_at_decision_time, odds, american_odds, price, line_price, entry_odds`
- `features_known_at_decision_time` aliases found in `45` python files. aliases=`features_known_at_decision_time, features, feature_snapshot, model_features, pre_event_features`
- `model_probability` aliases found in `188` python files. aliases=`model_probability, model_prob, predicted_probability, probability, win_probability`
- `market_implied_probability` aliases found in `115` python files. aliases=`market_implied_probability, implied_probability, market_probability, book_probability`
- `edge` aliases found in `227` python files. aliases=`edge, edge_percent, ev_percent, estimated_edge, model_edge`
- `stake` aliases found in `126` python files. aliases=`stake, paper_stake, recommended_stake, unit_size, bet_size`
- `final_result` aliases found in `360` python files. aliases=`final_result, result, result_status, outcome, final_outcome, settlement_result, paper_result`
- `profit_loss` aliases found in `93` python files. aliases=`profit_loss, pnl, profit, loss, closed_pnl, realized_pnl`
- `closing_line` aliases found in `57` python files. aliases=`closing_line, closing_odds, closing_price, close_price, closing_line_value`
- `clv` aliases found in `59` python files. aliases=`clv, clv_percent, closing_line_value, closing_line_value_pct`

## Target File Field Hits

### automation_scheduler/backtesting.py
- `event_id`: `0` hits
- `contract_id`: `0` hits
- `sport`: `0` hits
- `league`: `0` hits
- `market`: `2` hits
  - line `44`: `"market_type": _group_counts(rows, "market_type"),`
  - line `63`: `"market_type": _group_counts(rows, "market_type"),`
- `decision_time`: `0` hits
- `odds_at_decision_time`: `0` hits
- `features_known_at_decision_time`: `0` hits
- `model_probability`: `0` hits
- `market_implied_probability`: `0` hits
- `edge`: `0` hits
- `stake`: `0` hits
- `final_result`: `4` hits
  - line `5`: `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage`
  - line `30`: `coverage = summarize_outcome_coverage(rows)`
  - line `47`: `"next_required_data": ["settlement_results"],`
  - line `66`: `"next_required_data": [] if status == "metrics_ready" else ["additional_settlement_results"],`
- `profit_loss`: `0` hits
- `closing_line`: `0` hits
- `clv`: `0` hits

### automation_scheduler/backtesting_engine.py
- `event_id`: `0` hits
- `contract_id`: `0` hits
- `sport`: `0` hits
- `league`: `0` hits
- `market`: `1` hits
  - line `50`: `"market_type": row.get("market_type"),`
- `decision_time`: `0` hits
- `odds_at_decision_time`: `7` hits
  - line `14`: `from .clv_tracker import calculate_clv_for_american_odds`
  - line `34`: `odds = _to_float(row.get("recommended_odds"))`
  - line `36`: `pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0`
  - line `51`: `"recommended_odds": row.get("recommended_odds"),`
  - line `52`: `"closing_odds": row.get("closing_odds"),`
  - line `100`: `calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))`
- `features_known_at_decision_time`: `0` hits
- `model_probability`: `1` hits
  - line `53`: `"model_probability": row.get("model_probability"),`
- `market_implied_probability`: `0` hits
- `edge`: `7` hits
  - line `17`: `from .paper_trade_ledger import load_paper_ledger, summarize_paper_ledger`
  - line `58`: `"ev_percent": row.get("ev_percent", 0.0),`
  - line `191`: `ledger_base = str(Path(base_data_dir) / "paper_ledger")`
  - line `192`: `ledger_entries = load_paper_ledger(base_dir=ledger_base)`
  - line `193`: `summary = summarize_paper_ledger(base_dir=ledger_base)`
  - line `194`: `metrics = calculate_performance_metrics(ledger_entries)`
- `stake`: `5` hits
  - line `33`: `stake = _to_float(row.get("paper_stake"), default=1.0)`
  - line `36`: `pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0`
  - line `39`: `pnl = -stake`
  - line `56`: `"paper_stake": stake,`
  - line `59`: `"recommended_stake_percent": row.get("recommended_stake_percent", 1.0),`
- `final_result`: `10` hits
  - line `15`: `from .historical_replay import load_historical_rows, replay_rows, summarize_replay_result, write_replay_result`
  - line `32`: `result_status = str(row.get("result_status", "pending")).lower()`
  - line `35`: `if result_status == "win":`
  - line `38`: `elif result_status == "loss":`
  - line `41`: `elif result_status == "push":`
  - line `54`: `"result_status": result_status,`
- `profit_loss`: `10` hits
  - line `11`: `calculate_log_loss,`
  - line `36`: `pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0`
  - line `38`: `elif result_status == "loss":`
  - line `39`: `pnl = -stake`
  - line `42`: `pnl = 0.0`
  - line `45`: `pnl = 0.0`
- `closing_line`: `3` hits
  - line `52`: `"closing_odds": row.get("closing_odds"),`
  - line `100`: `calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))`
  - line `102`: `if entry.get("recommended_odds") is not None and entry.get("closing_odds") is not None`
- `clv`: `18` hits
  - line `14`: `from .clv_tracker import calculate_clv_for_american_odds`
  - line `88`: `Path(base_data_dir, "clv").mkdir(parents=True, exist_ok=True)`
  - line `99`: `clv_values = [`
  - line `100`: `calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))`
  - line `104`: `average_clv_percent = round(sum(clv_values) / len(clv_values), 4) if clv_values else 0.0`
  - line `105`: `positive_clv_rate = round(sum(1 for v in clv_values if v > 0) / len(clv_values), 4) if clv_values else 0.0`

### automation_scheduler/historical_replay.py
- `event_id`: `2` hits
  - line `37`: `"event_id": row.get("event_id"),`
  - line `39`: `"event_name": row.get("event_name"),`
- `contract_id`: `0` hits
- `sport`: `0` hits
- `league`: `0` hits
- `market`: `2` hits
  - line `38`: `"market_type": row.get("market_type"),`
  - line `40`: `"market_name": row.get("market_name"),`
- `decision_time`: `1` hits
  - line `46`: `"timestamp": row.get("timestamp") or utc_now_iso(),`
- `odds_at_decision_time`: `2` hits
  - line `42`: `"recommended_odds": row.get("odds"),`
  - line `43`: `"closing_odds": row.get("closing_odds"),`
- `features_known_at_decision_time`: `0` hits
- `model_probability`: `1` hits
  - line `44`: `"model_probability": _to_float(row.get("model_probability")),`
- `market_implied_probability`: `0` hits
- `edge`: `0` hits
- `stake`: `0` hits
- `final_result`: `9` hits
  - line `45`: `"result_status": row.get("result_status", "pending"),`
  - line `58`: `def write_replay_result(result: dict[str, Any], base_dir: str = "data/backtests") -> str:`
  - line `62`: `model_id = sanitize_filename(str(result.get("model_id") or "unknown_model"))`
  - line `63`: `replay_id = sanitize_filename(str(result.get("replayed_at") or utc_now_iso()))`
  - line `65`: `path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")`
  - line `69`: `def summarize_replay_result(result: dict[str, Any]) -> dict[str, Any]:`
- `profit_loss`: `1` hits
  - line `71`: `settled = [row for row in rows if str(row.get("result_status")).lower() in {"win", "loss", "push"}]`
- `closing_line`: `1` hits
  - line `43`: `"closing_odds": row.get("closing_odds"),`
- `clv`: `0` hits

## No-Leakage Sensitive Field Hits in Target Files

### automation_scheduler/backtesting.py
- Leakage-sensitive references: `4`
- line `5`: `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage`
- line `30`: `coverage = summarize_outcome_coverage(rows)`
- line `47`: `"next_required_data": ["settlement_results"],`
- line `66`: `"next_required_data": [] if status == "metrics_ready" else ["additional_settlement_results"],`

### automation_scheduler/backtesting_engine.py
- Leakage-sensitive references: `35`
- line `14`: `from .clv_tracker import calculate_clv_for_american_odds`
- line `15`: `from .historical_replay import load_historical_rows, replay_rows, summarize_replay_result, write_replay_result`
- line `32`: `result_status = str(row.get("result_status", "pending")).lower()`
- line `35`: `if result_status == "win":`
- line `36`: `pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0`
- line `38`: `elif result_status == "loss":`
- line `39`: `pnl = -stake`
- line `41`: `elif result_status == "push":`
- line `42`: `pnl = 0.0`
- line `45`: `pnl = 0.0`
- line `52`: `"closing_odds": row.get("closing_odds"),`
- line `54`: `"result_status": result_status,`
- line `57`: `"paper_profit_loss": round(pnl, 4),`
- line `88`: `Path(base_data_dir, "clv").mkdir(parents=True, exist_ok=True)`
- line `94`: `replay_path = write_replay_result(replay, base_dir=str(Path(base_data_dir) / "backtests"))`
- line `99`: `clv_values = [`
- line `100`: `calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))`
- line `102`: `if entry.get("recommended_odds") is not None and entry.get("closing_odds") is not None`
- line `104`: `average_clv_percent = round(sum(clv_values) / len(clv_values), 4) if clv_values else 0.0`
- line `105`: `positive_clv_rate = round(sum(1 for v in clv_values if v > 0) / len(clv_values), 4) if clv_values else 0.0`
- line `114`: `clv_path = Path(base_data_dir) / "clv" / f"clv_{model_slug}_{stamp}.json"`
- line `115`: `clv_path.write_text(`
- line `119`: `"sample_size": len(clv_values),`
- line `120`: `"average_clv_percent": average_clv_percent,`
- line `121`: `"positive_clv_rate": positive_clv_rate,`
- line `155`: `if average_clv_percent < 0:`
- line `156`: `blocked_reasons.append("negative_clv")`
- line `157`: `elif clv_values:`
- line `158`: `blocked_reasons.append("positive_clv")`
- line `171`: `"average_clv_percent": average_clv_percent,`
- line `172`: `"positive_clv_rate": positive_clv_rate,`
- line `181`: `"replay_summary": summarize_replay_result(replay),`
- line `184`: `"clv_path": str(clv_path),`
- line `213`: `result = run_backtest(model_id=model_id, historical_rows_path=historical_rows_path, rows=rows, base_data_dir=base_data_dir)`
- line `214`: `report = write_model_performance_report(result, base_dir=str(Path(base_data_dir) / "performance_reports"))`

### automation_scheduler/historical_replay.py
- Leakage-sensitive references: `10`
- line `43`: `"closing_odds": row.get("closing_odds"),`
- line `45`: `"result_status": row.get("result_status", "pending"),`
- line `58`: `def write_replay_result(result: dict[str, Any], base_dir: str = "data/backtests") -> str:`
- line `62`: `model_id = sanitize_filename(str(result.get("model_id") or "unknown_model"))`
- line `63`: `replay_id = sanitize_filename(str(result.get("replayed_at") or utc_now_iso()))`
- line `65`: `path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")`
- line `69`: `def summarize_replay_result(result: dict[str, Any]) -> dict[str, Any]:`
- line `70`: `rows = list(result.get("rows") or [])`
- line `71`: `settled = [row for row in rows if str(row.get("result_status")).lower() in {"win", "loss", "push"}]`
- line `73`: `"model_id": result.get("model_id"),`

## Initial Canonical Owner Recommendation
CANONICAL_OWNER_RECOMMENDATION: `automation_scheduler/backtesting_engine.py`

Reason: this file already connects historical replay, paper ledger, CLV tracker, calibration metrics, PnL, and bankroll/stake-style fields.

## Slimming Rule

- If `backtesting.py` is only a scaffold, convert it to a thin compatibility wrapper or delete after import sites are migrated.
- If `historical_replay.py` only loads/replays rows, keep it as private plumbing under `backtesting_engine.py`, not as a public competing engine.
- The public owner should expose one canonical function that runs replay + strategy + bankroll simulation + result summary.

## Required Canonical API

```python
run_backtest(
    rows,
    strategy=None,
    bankroll=1000.0,
    unit_size=10.0,
    risk_profile='conservative',
)
```

## Required Canonical Schema Fields
- `event_id`
- `contract_id`
- `sport`
- `league`
- `market`
- `decision_time`
- `odds_at_decision_time`
- `features_known_at_decision_time`
- `model_probability`
- `market_implied_probability`
- `edge`
- `stake`
- `final_result`
- `profit_loss`
- `closing_line`
- `clv`
