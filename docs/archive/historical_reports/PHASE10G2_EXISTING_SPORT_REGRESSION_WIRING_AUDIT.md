# Phase 10G2 Existing Sport Regression Wiring Audit

Generated: 2026-06-12T20:54:02
- HEAD: `b6c782b`
- Git clean at audit start: `True`

## Backtest Module Inventory

### `automation_scheduler/backtest_dataset_builder.py`
- Classes:
  - none
- Functions:
  - `_load_json` line `42`
  - `_write_json` line `46`
  - `_find_row_lists` line `51`
  - `discover_backtest_artifacts` line `73`
  - `extract_backtest_rows_from_artifact` line `114`
  - `build_canonical_backtest_dataset` line `148`
  - `load_canonical_backtest_dataset` line `271`
  - `summarize_canonical_dataset_report` line `287`

### `automation_scheduler/backtest_leakage.py`
- Classes:
  - none
- Functions:
  - `_present` line `57`
  - `evaluate_backtest_row_leakage` line `61`
  - `evaluate_backtest_rows_leakage` line `104`
  - `assert_backtest_rows_no_hard_leakage` line `131`
  - `summarize_backtest_leakage_report` line `138`

### `automation_scheduler/backtest_schema.py`
- Classes:
  - none
- Functions:
  - `_first_present` line `85`
  - `normalize_backtest_row` line `92`
  - `normalize_backtest_rows` line `127`
  - `get_backtest_feature_snapshot` line `131`
  - `find_leakage_fields_in_features` line `141`
  - `walk` line `148`
  - `validate_no_leakage_features` line `164`
  - `missing_required_backtest_fields` line `177`
  - `describe_backtest_schema` line `186`

### `automation_scheduler/backtest_strategy_bankroll.py`
- Classes:
  - none
- Functions:
  - `_to_float` line `26`
  - `_american_profit` line `35`
  - `_bucket` line `45`
  - `decide_backtest_bet` line `56`
  - `simulate_backtest_bankroll` line `98`
  - `summarize_strategy_bankroll_report` line `260`
  - `_clamp_probability` line `276`
  - `calculate_regression_probability` line `280`
  - `apply_regression_strategy_to_rows` line `328`

### `automation_scheduler/backtesting_engine.py`
- Classes:
  - none
- Functions:
  - `_group_counts` line `27`
  - `_reason_counts` line `33`
  - `run_backtesting_scaffold` line `43`
  - `load_historical_rows` line `83`
  - `replay_rows` line `95`
  - `write_replay_result` line `135`
  - `summarize_replay_result` line `153`
  - `_to_float` line `165`
  - `_paper_rows_from_replay_rows` line `172`
  - `compare_expected_vs_realized` line `210`
  - `run_backtest` line `225`
  - `run_paper_summary` line `345`
  - `generate_backtest_report` line `361`


## Public Backtest / Strategy Function Pattern Hits

- `automation_scheduler/backtest_strategy_bankroll.py` line `98`: `def simulate_backtest_bankroll(`
- `automation_scheduler/backtest_strategy_bankroll.py` line `280`: `def calculate_regression_probability(`
- `automation_scheduler/backtest_strategy_bankroll.py` line `328`: `def apply_regression_strategy_to_rows(`
- `automation_scheduler/backtesting_engine.py` line `225`: `def run_backtest(`
- `automation_scheduler/backtesting_engine.py` line `361`: `def generate_backtest_report(`
- `automation_scheduler/backtesting_engine.py` line `345`: `def run_paper_summary(`

## Existing All-Sports / Sport-Specific / Regression Mentions

### `automation_scheduler/__init__.py`
- Terms: `run_backtest`
- line `11`: `from .backtesting_engine import generate_backtest_report, run_backtest, run_paper_summary`

### `automation_scheduler/backtest_dataset_builder.py`
- Terms: `run_backtest`
- line `6`: `automation_scheduler.backtesting_engine.run_backtest`

### `automation_scheduler/backtest_strategy_bankroll.py`
- Terms: `feature_weights, calculate_regression_probability, apply_regression_strategy`
- line `280`: `def calculate_regression_probability(`
- line `283`: `feature_weights: Mapping[str, float] | None = None,`
- line `304`: `weights = dict(feature_weights or {})`
- line `322`: `"feature_weights": weights,`
- line `328`: `def apply_regression_strategy_to_rows(`
- line `331`: `feature_weights: Mapping[str, float] | None = None,`
- line `343`: `result = calculate_regression_probability(`
- line `345`: `feature_weights=feature_weights,`

### `automation_scheduler/backtesting_engine.py`
- Terms: `apply_regression_strategy, run_backtest, backtest_strategy`
- line `24`: `from .backtest_strategy_bankroll import apply_regression_strategy_to_rows, simulate_backtest_bankroll, summarize_strategy_bankroll_report`
- line `43`: `def run_backtesting_scaffold(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:`
- line `225`: `def run_backtest(`
- line `242`: `source_rows = apply_regression_strategy_to_rows(source_rows, **strategy_config)`
- line `369`: `result = run_backtest(model_id=model_id, historical_rows_path=historical_rows_path, rows=rows, base_data_dir=base_data_dir)`

### `automation_scheduler/baseball_impact_common.py`
- Terms: `all_sports`
- line `10`: `SUPPORTED_BASEBALL_SPORTS = ("baseball_mlb",)`

### `automation_scheduler/baseball_impact_readiness.py`
- Terms: `all_sports`
- line `6`: `from .baseball_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_BASEBALL_MARKETS, SUPPORTED_BASEBALL_ROLES, SUPPORTED_BASEBALL_SPORTS, finalize_baseball_response`
- line `13`: `"supported_sports": list(SUPPORTED_BASEBALL_SPORTS),`

### `automation_scheduler/basketball_player_impact_common.py`
- Terms: `all_sports`
- line `17`: `SUPPORTED_BASKETBALL_SPORTS = (`
- line `74`: `return BASKETBALL_SPORT_ALIASES.get(raw, raw if raw in SUPPORTED_BASKETBALL_SPORTS else "basketball_nba")`

### `automation_scheduler/basketball_player_impact_readiness.py`
- Terms: `all_sports`
- line `5`: `from .basketball_player_impact_common import SUPPORTED_BASKETBALL_SPORTS, SPORT_CONTRACTS, finalize_safe_response`
- line `42`: `"supported_sports": list(SUPPORTED_BASKETBALL_SPORTS),`

### `automation_scheduler/data_availability_tiers.py`
- Terms: `sport_profiles`
- line `121`: `SPORT_PROFILES: dict[str, dict[str, Any]] = {`
- line `257`: `return SPORT_PROFILES.get(key) or SPORT_PROFILES["context_module"]`

### `automation_scheduler/football_impact_common.py`
- Terms: `all_sports`
- line `10`: `SUPPORTED_FOOTBALL_SPORTS,`

### `automation_scheduler/football_impact_report.py`
- Terms: `all_sports`
- line `14`: `SUPPORTED_FOOTBALL_SPORTS,`
- line `245`: `"supported_sports": list(SUPPORTED_FOOTBALL_SPORTS),`

### `automation_scheduler/football_impact_schema.py`
- Terms: `all_sports`
- line `10`: `SUPPORTED_FOOTBALL_SPORTS = (`
- line `148`: `return FOOTBALL_SPORT_ALIASES.get(raw, raw if raw in SUPPORTED_FOOTBALL_SPORTS else "americanfootball_nfl")`

### `automation_scheduler/manifold_feature_builder.py`
- Terms: `feature_weights`
- line `127`: `FEATURE_WEIGHTS = {`
- line `460`: `weights = [round(float(FEATURE_WEIGHTS.get(name, 0.65)), 6) for name in FEATURE_NAMES]`
- line `474`: `"feature_weights": weights,`

### `automation_scheduler/market_state_manifold.py`
- Terms: `feature_weights`
- line `49`: `weights = list(feature_payload.get("feature_weights") or [1.0 for _ in FEATURE_NAMES])`
- line `85`: `weights = list(feature_payload.get("feature_weights") or [1.0 for _ in FEATURE_NAMES])`

### `automation_scheduler/scheduler_runner.py`
- Terms: `run_backtest`
- line `14`: `from .backtesting_engine import run_backtesting_scaffold`
- line `1254`: `backtesting_summary = run_backtesting_scaffold(paper_decisions)`

### `PHASE10_MODEL_BACKTEST_READINESS_SCAN.md`
- Terms: `all_sports, run_backtest`
- line `187`: `| `automation_scheduler/backtesting.py` | 28 | `def run_backtesting_scaffold(rows: list[dict[str, Any]] \| None = None) -> dict[str, Any]:` |`
- line `410`: `| `automation_scheduler/baseball_impact_readiness.py` | 6 | `from .baseball_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_BASEBALL_MARKETS, SUPPORTED_BASEBALL_ROLES, SUPPORTED_BASEBALL_SPORTS, finalize_baseball_response` |`
- line `949`: `| `tests/test_backtesting.py` | 3 | `from automation_scheduler.backtesting import run_backtesting_scaffold` |`
- line `951`: `| `tests/test_backtesting.py` | 8 | `result = run_backtesting_scaffold([{"provider": "kalshi"}])` |`
- line `952`: `| `tests/test_backtesting_engine.py` | 6 | `from automation_scheduler.backtesting_engine import generate_backtest_report, run_backtest` |`
- line `1179`: `| `tests/test_backtesting.py` | 12 | `result = run_backtesting_scaffold([{"provider": "kalshi", "final_outcome": 1}, {"provider": "sharp", "final_outcome": 0}])` |`
- line `1274`: `| `automation_scheduler/backtesting.py` | `` | `_group_counts, _reason_counts, run_backtesting_scaffold` |`
- line `1275`: `| `automation_scheduler/backtesting_engine.py` | `` | `_to_float, _paper_rows_from_replay_rows, compare_expected_vs_realized, run_backtest, run_paper_summary, generate_backtest_report` |`

### `PHASE10A_BACKTEST_OWNER_AND_SCHEMA_AUDIT.md`
- Terms: `run_backtest`
- line `23`: `- `run_backtesting_scaffold` line `28``
- line `34`: `- `run_backtest` line `80``
- line `57`: `- `tests/test_backtesting.py` line `3`: `from automation_scheduler.backtesting import run_backtesting_scaffold``
- line `61`: `- `tests/test_backtesting_engine.py` line `6`: `from automation_scheduler.backtesting_engine import generate_backtest_report, run_backtest``
- line `247`: `- line `213`: `result = run_backtest(model_id=model_id, historical_rows_path=historical_rows_path, rows=rows, base_data_dir=base_data_dir)``
- line `277`: `run_backtest(`

### `PHASE10B_BACKTEST_OWNER_SLIMMING.md`
- Terms: `run_backtest`
- line `10`: `- `automation_scheduler\backtesting.py:run_backtesting_scaffold``

### `PHASE10B_BACKTEST_OWNER_SLIMMING_REPAIR.md`
- Terms: `run_backtest`
- line `6`: `- `scheduler_runner.py` now imports `run_backtesting_scaffold` from canonical owner `automation_scheduler/backtesting_engine.py`.`

### `PHASE10D_SHARP_STYLE_NO_LEAKAGE_GATE.md`
- Terms: `run_backtest`
- line `15`: `- `automation_scheduler/backtesting_engine.py` now emits a leakage report in `run_backtest()`.`

### `PHASE10E_UNIFIED_REPLAY_STRATEGY_BANKROLL.md`
- Terms: `run_backtest, backtest_strategy`
- line `6`: `- `automation_scheduler/backtest_strategy_bankroll.py``
- line `7`: `- `tests/test_backtest_strategy_bankroll.py``
- line `10`: `- `automation_scheduler/backtesting_engine.py` now includes `strategy_bankroll_summary` and `strategy_bankroll_report` in `run_backtest()` output.`

### `PHASE10F_REGRESSION_STRATEGY_HOOKS.md`
- Terms: `regression strategy, run_backtest, backtest_strategy`
- line `1`: `# Phase 10F Regression Strategy Hooks`
- line `6`: `- Regression-style probability hook inside `automation_scheduler/backtest_strategy_bankroll.py`.`
- line `11`: `- `run_backtest()` can apply transparent feature weights before leakage, replay, and bankroll simulation.`

### `PHASE10G_CANONICAL_HISTORICAL_DATASET_BUILDER.md`
- Terms: `run_backtest`
- line `18`: `- It produces clean input rows for `automation_scheduler.backtesting_engine.run_backtest()`.`

### `tests/test_backtest_leakage.py`
- Terms: `run_backtest`
- line `9`: `from automation_scheduler.backtesting_engine import run_backtest`
- line `123`: `result = run_backtest(`

### `tests/test_backtest_regression_strategy.py`
- Terms: `feature_weights, calculate_regression_probability, apply_regression_strategy, run_backtest, backtest_strategy`
- line `1`: `from automation_scheduler.backtest_strategy_bankroll import (`
- line `2`: `apply_regression_strategy_to_rows,`
- line `3`: `calculate_regression_probability,`
- line `6`: `from automation_scheduler.backtesting_engine import run_backtest`
- line `9`: `def test_calculate_regression_probability_from_feature_weights():`
- line `10`: `result = calculate_regression_probability(`
- line `18`: `feature_weights={`
- line `30`: `result = calculate_regression_probability(`
- line `33`: `feature_weights={"steam": 1.0},`
- line `41`: `def test_apply_regression_strategy_to_rows_sets_model_probability():`
- line `42`: `rows = apply_regression_strategy_to_rows(`
- line `51`: `feature_weights={"pace_edge": 0.02},`

### `tests/test_backtest_schema.py`
- Terms: `run_backtest`
- line `10`: `from automation_scheduler.backtesting_engine import replay_rows, run_backtest`

### `tests/test_backtest_strategy_bankroll.py`
- Terms: `run_backtest, backtest_strategy`
- line `1`: `from automation_scheduler.backtest_strategy_bankroll import (`
- line `6`: `from automation_scheduler.backtesting_engine import run_backtest`
- line `83`: `def test_run_backtest_includes_strategy_bankroll_report(tmp_path):`
- line `84`: `result = run_backtest(`

### `tests/test_backtesting.py`
- Terms: `run_backtest`
- line `3`: `from automation_scheduler.backtesting_engine import run_backtesting_scaffold`
- line `8`: `result = run_backtesting_scaffold([{"provider": "kalshi"}])`
- line `12`: `result = run_backtesting_scaffold([{"provider": "kalshi", "final_outcome": 1}, {"provider": "sharp", "final_outcome": 0}])`
- line `17`: `result = run_backtesting_scaffold(`
- line `27`: `result = run_backtesting_scaffold(`

### `tests/test_backtesting_engine.py`
- Terms: `run_backtest`
- line `6`: `from automation_scheduler.backtesting_engine import generate_backtest_report, run_backtest`
- line `37`: `result = run_backtest(`

### `tests/test_data_availability_tiers.py`
- Terms: `sport_profiles`
- line `6`: `SPORT_PROFILES,`
- line `39`: `self.assertIn(module, SPORT_PROFILES)`

### `tests/test_multi_sport_model_registry.py`
- Terms: `all_sports, sport_specific`
- line `481`: `def test_officials_module_uses_sport_specific_official_type(self):`
- line `516`: `self.assertTrue(module["same_module_for_all_sports"])`

### `tests/test_sport_model_routing.py`
- Terms: `sport_specific`
- line `273`: `def test_sport_specific_component_requirements(self):`


## Verdict

- Existing dedicated profile module: `False`
- Existing all-sports wiring mentions: `True`
- Existing sport-specific wiring mentions: `True`
- Existing regression hook functions: `True`

DECISION: `do_not_add_new_profile_module_until_reviewed`

Reason: repo appears to already contain some all-sports / sport-specific profile wiring.
