# Phase 10X Full Repo Professional Architect Review

Generated: `2026-06-13T02:07:41Z`
- Repo root: `C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration`
- Branch: `phase-6-api-slimming`
- HEAD: `0a22606`
- Git clean: `True`

## Executive Counts

```json
{
  "all_files_scanned": 1356,
  "ast_error_files": 1,
  "category_counts": {
    "api_routes": 31,
    "app_entrypoint": 1,
    "automation_scheduler": 296,
    "backtesting": 6,
    "generated_runtime_data": 505,
    "ledger_review": 8,
    "model_strategy": 13,
    "other": 202,
    "phase_reports": 20,
    "risk_bankroll": 9,
    "scheduler": 2,
    "services": 5,
    "tests": 258
  },
  "duplicate_basename_groups": 29,
  "duplicate_file_hash_groups": 17,
  "generated_or_runtime_files": 512,
  "import_main_hits": 2,
  "main_route_hits": 0,
  "python_files_scanned": 723,
  "risky_name_files": 14,
  "route_decorator_files": 22,
  "suffix_counts": {
    ".code-workspace": 1,
    ".csv": 13,
    ".db": 1,
    ".example": 1,
    ".ini": 1,
    ".joblib": 1,
    ".json": 481,
    ".jsonl": 1,
    ".md": 43,
    ".ps1": 76,
    ".py": 724,
    ".txt": 6,
    ".yaml": 2,
    "<none>": 5
  },
  "tracked_files": 843,
  "tracked_generated_or_runtime_files": 0,
  "untracked_generated_or_runtime_files": 512
}
```

## Category Counts

| Category | Count |
|---|---:|
| `api_routes` | `31` |
| `app_entrypoint` | `1` |
| `automation_scheduler` | `296` |
| `backtesting` | `6` |
| `generated_runtime_data` | `505` |
| `ledger_review` | `8` |
| `model_strategy` | `13` |
| `other` | `202` |
| `phase_reports` | `20` |
| `risk_bankroll` | `9` |
| `scheduler` | `2` |
| `services` | `5` |
| `tests` | `258` |

## Critical Findings

### `python_files_import_from_main`
- Reason: Tests/services importing from main.py usually indicate stale compatibility ownership.
```json
[
  {
    "import": {
      "level": 0,
      "line": 1,
      "module": "main",
      "names": [
        "app",
        "custom_openapi"
      ],
      "type": "from"
    },
    "line": 1,
    "path": "api_server.py"
  },
  {
    "import": {
      "line": 8,
      "module": "main",
      "name": "main",
      "type": "import"
    },
    "line": 8,
    "path": "tests/support/action_imports.py"
  }
]
```

### `python_ast_parse_errors`
- Reason: Syntax errors block safe automated refactors.
```json
[
  {
    "error": "invalid non-printable character U+FEFF (<unknown>, line 1)",
    "path": "src/api/schemas/__init__.py",
    "tracked": true
  }
]
```

## Warnings

### `risky_legacy_or_temp_file_names`
- Reason: Files with _v2/_new/_fixed/_compat/legacy/shim names should be reviewed for deletion or merge.
```json
[
  {
    "path": "data/manual_import_templates/combat_remaining_fields_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_import_templates/completed_sports_policy_review_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_import_templates/golf_remaining_fields_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_import_templates/nhl_remaining_fields_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_import_templates/soccer_remaining_fields_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_import_templates/tennis_remaining_fields_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_imports/nfl_coaching/templates/coordinators_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_imports/nfl_coaching/templates/current_staff_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "data/manual_imports/nfl_coaching/templates/head_coaches_template.csv",
    "patterns": [
      "temp"
    ],
    "tracked": false
  },
  {
    "path": "scripts/live_sport_template.ps1",
    "patterns": [
      "temp"
    ],
    "tracked": true
  },
  {
    "path": "scripts/run_nfl_partial_backfills_v2.ps1",
    "patterns": [
      "_v2"
    ],
    "tracked": true
  },
  {
    "path": "tests/test_institutional_fixed_income_rates.py",
    "patterns": [
      "_fixed"
    ],
    "tracked": true
  },
  {
    "path": "tests/test_news_event_monitor.py",
    "patterns": [
      "_new"
    ],
    "tracked": true
  },
  {
    "path": "tests/test_news_events_adapter_contract.py",
    "patterns": [
      "_new"
    ],
    "tracked": true
  }
]
```

### `duplicate_file_hashes`
- Reason: Exact duplicate files may indicate accidental copies.
```json
{
  "2c32fe1948bf900876e2fb22692fac20c2fa9772bfb3707b7a1d6eed2c6e676a": [
    "data/outcomes/collector/items/kalshi_calibration_408fc51a80095fc7.json",
    "data/outcomes/collector/latest_cycle.json"
  ],
  "2da2078f53cf9af480491a117f68bc5c8e6d533c4ed73ed05af48018576bc428": [
    "data/prediction_market_outcome_candidates/daily/2026-06-12.md",
    "data/prediction_market_outcome_candidates/items/prediction_market_outcome_candidates_2026-06-12T11-20-38.205896_00-00_999fbd93.md",
    "data/prediction_market_outcome_candidates/latest.md"
  ],
  "3de7d37a2b1bf68e544bb7de1b8267e9c924e99227ea3ae7555ae9b02aa9f446": [
    "data/clv/clv_m2_2026-06-12T18_28_38.816213_00_00.json",
    "data/clv/clv_m2_2026-06-12T19_05_02.310724_00_00.json",
    "data/clv/clv_m2_2026-06-12T19_24_29.117814_00_00.json",
    "data/clv/clv_m2_2026-06-12T22_57_39.057427_00_00.json",
    "data/clv/clv_m2_2026-06-12T23_52_50.954152_00_00.json",
    "data/clv/clv_m2_2026-06-12T23_53_08.599714_00_00.json",
    "data/clv/clv_m2_2026-06-12T23_58_59.485127_00_00.json",
    "data/clv/clv_m2_2026-06-12T23_59_13.282606_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_00_44.692670_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_01_02.080714_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_05_09.390530_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_05_37.101592_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_07_27.515390_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_07_47.075764_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_13_27.485447_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_13_49.045796_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_19_58.043384_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_20_23.023296_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_33_38.292635_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_34_03.797664_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_37_44.630259_00_00.json",
    "data/clv/clv_m2_2026-06-13T00_38_16.908274_00_00.json",
    "data/clv/clv_m2_2026-06-13T01_07_03.067151_00_00.json",
    "data/clv/clv_m2_2026-06-13T01_07_42.514746_00_00.json",
    "data/clv/clv_m2_2026-06-13T01_08_41.723027_00_00.json",
    "data/clv/clv_m2_2026-06-13T01_09_23.847327_00_00.json",
    "data/clv/clv_m2_2026-06-13T01_21_27.267707_00_00.json",
    "data/clv/clv_m2_2026-06-13T01_22_57.161254_00_00.json"
  ],
  "5f2a8dcf6863063febb95a13ab2a82fe0873468c3673b32842c5a5eb64c40820": [
    "data/data_sources/data_availability/daily/2026-06-12.json",
    "data/data_sources/data_availability/items/data_availability_2026-06-12T11-20-37.659573_00-00_7f9aefe0.json",
    "data/data_sources/data_availability/latest.json"
  ],
  "64e019200a8d23a3cec5f6426a49d224081603e78f6ad0a0ba67574a90696260": [
    "data/ops_checks/daily/2026-06-12.json",
    "data/ops_checks/items/ops_20260612T112026Z_4406cd61.json",
    "data/ops_checks/latest.json"
  ],
  "844216d1d450e8b0be88a068d5aeea81c6bd1ac1d38198cebf58849fed5f056d": [
    "data/manual_imports/nfl_coaching/templates/coordinators_template.csv",
    "data/manual_imports/nfl_coaching/templates/current_staff_template.csv",
    "data/manual_imports/nfl_coaching/templates/head_coaches_template.csv"
  ],
  "860ac5ddeaf0dd3562789f19a6a95fe885d51e3cc1b4c15cbb856435dbe8f18f": [
    "data/calibration/calibration_phase10g2-sport-profile-proof_2026-06-13T01_10_26.331487_00_00.json",
    "data/calibration/calibration_phase10g2-sport-profile-proof_2026-06-13T01_24_35.170258_00_00.json"
  ],
  "87768b3c340ec37a49c4efb28ba5f31792ca57513603fafea4cc812839836db0": [
    "data/deepseek_data_checks/daily/2026-06-12.md",
    "data/deepseek_data_checks/items/deepseek_data_check_2026-06-12T11-20-38.243478_00-00_ae5f90f3.md",
    "data/deepseek_data_checks/latest.md"
  ],
  "95d8f5e1115e9f2a24331d3e0c1b7c7f4b990afa7e23882853ef5ac2c4e7c25a": [
    "data/outcomes/migration/daily/2026-06-01.json",
    "data/outcomes/migration/items/kalshi_outcome_migration_81b1dcdaf8e4553b.json",
    "data/outcomes/migration/kalshi_local_outcomes_migration.latest.json"
  ],
  "9790c81c223f5036b921604c7444264eeecfabba6c646c4242b22ad9f2382001": [
    "data/paper_ledger/items/run_e067673ba7b6.json",
    "data/paper_ledger/latest.json"
  ],
  "a4d1e98577473c33f57b237e226912eaeb5665b0fbc0c3da0a44ddc1a3194334": [
    "data/manifold/clusters/history/2026-06-12.json",
    "data/manifold/clusters/latest.json"
  ],
  "b7bf74cd30c66db891fb90d0ea0ed430834645e5d01a0894ab7adab826cbc1f8": [
    "data/manifold/calibration/2026-06-13.json",
    "data/manifold/calibration/latest.json"
  ],
  "bdd34a0a4f67cad0e8440c17b13649a2e4e48ece879a479d2261046258246050": [
    "data/calibration/calibration_m2_2026-06-12T18_28_38.816213_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T19_05_02.310724_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T19_24_29.117814_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T22_57_39.057427_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T23_52_50.954152_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T23_53_08.599714_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T23_58_59.485127_00_00.json",
    "data/calibration/calibration_m2_2026-06-12T23_59_13.282606_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_00_44.692670_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_01_02.080714_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_05_09.390530_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_05_37.101592_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_07_27.515390_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_07_47.075764_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_13_27.485447_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_13_49.045796_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_19_58.043384_00_00.json",
    "data/calibration/calibration_m2_2026-06-13T00_20_23.023296_00_00.json",
    "data/calibration
```

## Public Owner Function Hits

| Function | Count | Locations |
|---|---:|---|
| `apply_regression_strategy_to_rows` | `1` | `automation_scheduler/backtest_strategy_bankroll.py:351` |
| `build_canonical_backtest_dataset` | `1` | `automation_scheduler/backtest_dataset_builder.py:190` |
| `calculate_regression_probability` | `1` | `automation_scheduler/backtest_strategy_bankroll.py:303` |
| `describe_regression_profiles` | `1` | `automation_scheduler/backtest_strategy_profiles.py:214` |
| `evaluate_data_availability` | `1` | `automation_scheduler/data_availability_tiers.py:374` |
| `generate_backtest_report` | `1` | `automation_scheduler/backtesting_engine.py:392` |
| `get_regression_profile` | `1` | `automation_scheduler/backtest_strategy_profiles.py:130` |
| `get_tier_profile` | `1` | `automation_scheduler/data_availability_tiers.py:255` |
| `run_backtest` | `1` | `automation_scheduler/backtesting_engine.py:256` |
| `run_backtesting_scaffold` | `1` | `automation_scheduler/backtesting_engine.py:44` |
| `simulate_backtest_bankroll` | `1` | `automation_scheduler/backtest_strategy_bankroll.py:121` |

## Recommended Subtractions / Cleanup Candidates

| Action | Path | Reason | Tracked |
|---|---|---|---:|
| `review_for_delete_or_merge` | `data/manual_import_templates/combat_remaining_fields_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_import_templates/completed_sports_policy_review_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_import_templates/golf_remaining_fields_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_import_templates/nhl_remaining_fields_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_import_templates/soccer_remaining_fields_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_import_templates/tennis_remaining_fields_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_imports/nfl_coaching/templates/coordinators_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_imports/nfl_coaching/templates/current_staff_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `data/manual_imports/nfl_coaching/templates/head_coaches_template.csv` | Risky/stale naming patterns: ['temp'] | `False` |
| `review_for_delete_or_merge` | `scripts/live_sport_template.ps1` | Risky/stale naming patterns: ['temp'] | `True` |
| `review_for_delete_or_merge` | `scripts/run_nfl_partial_backfills_v2.ps1` | Risky/stale naming patterns: ['_v2'] | `True` |
| `review_for_delete_or_merge` | `tests/test_institutional_fixed_income_rates.py` | Risky/stale naming patterns: ['_fixed'] | `True` |
| `review_for_delete_or_merge` | `tests/test_news_event_monitor.py` | Risky/stale naming patterns: ['_new'] | `True` |
| `review_for_delete_or_merge` | `tests/test_news_events_adapter_contract.py` | Risky/stale naming patterns: ['_new'] | `True` |

## Recommended Merges / Moves

- `rewrite_imports_to_canonical_owners`: Remove from-main imports and import schemas/services directly from canonical owners. Count: `2`

## Recommended Additions

- `add_dashboard_api_read_endpoints` (10H2_or_after_dashboard_report): Expose latest dashboard/paper/backtest JSON for Streamlit/React UI without direct file coupling.
- `add_model_promotion_gate_threshold_config` (10J): Promotion criteria should be explicit, versioned, and adjustable by sport/profile.
- `add_sport_label_backfill_or_inference_layer` (10I_or_10J): Dataset builder has shown very low sport coverage; sport/profile routing needs better labels.
- `add_paper_run_append_learning_loop` (10I): Repeated paper runs should append, rebuild dataset, compare results, and track CLV/outcomes.
- `add_dependency_cleanup_gate` (13): Known python_multipart warning and dependency hygiene should be handled before live.

## No-Touch Without Targeted Review

- `automation_scheduler/backtesting_engine.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `automation_scheduler/backtest_schema.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `automation_scheduler/backtest_leakage.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `automation_scheduler/backtest_strategy_bankroll.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `automation_scheduler/backtest_strategy_profiles.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `automation_scheduler/backtest_dataset_builder.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `automation_scheduler/data_availability_tiers.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `src/services/action_betting_service.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.
- `src/api/betting_action_routes.py` ? Canonical owner or core architecture module. Modify only with targeted evidence.

## Dependency Files

- `Dockerfile`
- `render.yaml`
- `requirements.txt`

## Top Generated / Runtime Files

| Path | Size | Tracked |
|---|---:|---:|
| `data/backtests/canonical/latest.jsonl` | `163034673` | `False` |
| `data/reports/scheduler_run_run_e067673ba7b6.json` | `8592126` | `False` |
| `data/reports/scheduler_run_run_a01fb4349e35.json` | `7951197` | `False` |
| `data/review_queue/items/run_e067673ba7b6.json` | `7557500` | `False` |
| `data/review_queue/latest.json` | `7557500` | `False` |
| `data/reports/scheduler_run_run_cceedfd77cbb.json` | `7269294` | `False` |
| `data/review_queue/review_queue.json` | `7152345` | `False` |
| `reports/json_data_audit/latest_summary.json` | `7037286` | `False` |
| `data/review_queue/items/run_a01fb4349e35.json` | `6940101` | `False` |
| `data/reports/scheduler_run_run_1621f541328e.json` | `6672218` | `False` |
| `data/review_queue/items/run_cceedfd77cbb.json` | `6297021` | `False` |
| `data/reports/scheduler_run_run_c16122b189a2.json` | `5997981` | `False` |
| `data/review_queue/items/run_1621f541328e.json` | `5732169` | `False` |
| `data/reports/scheduler_run_run_0ef22f23e0de.json` | `5333761` | `False` |
| `data/review_queue/items/run_c16122b189a2.json` | `5093483` | `False` |
| `data/reports/scheduler_run_run_9226f0cccdea.json` | `4722844` | `False` |
| `data/reports/scheduler_run_run_2cf48386fb0a.json` | `4658837` | `False` |
| `data/review_queue/items/run_0ef22f23e0de.json` | `4455661` | `False` |
| `data/reports/scheduler_run_run_b832d5167563.json` | `4038882` | `False` |
| `data/reports/scheduler_run_run_7ef89d739bd8.json` | `3985695` | `False` |
| `data/reports/scheduler_run_run_614dca3fba6f.json` | `3895762` | `False` |
| `data/review_queue/items/run_9226f0cccdea.json` | `3871032` | `False` |
| `data/review_queue/items/run_2cf48386fb0a.json` | `3820028` | `False` |
| `reports/json_data_audit/schema_inventory.json` | `3443766` | `False` |
| `data/reports/scheduler_run_run_ab397f4ebf3b.json` | `3354597` | `False` |
| `data/reports/scheduler_run_run_cc4c6f72fe66.json` | `3305756` | `False` |
| `data/review_queue/items/run_614dca3fba6f.json` | `3223667` | `False` |
| `data/review_queue/items/run_b832d5167563.json` | `3223667` | `False` |
| `data/review_queue/items/run_7ef89d739bd8.json` | `3180573` | `False` |
| `data/reports/scheduler_run_run_25533c9ec51a.json` | `2681909` | `False` |
| `data/reports/scheduler_run_run_2800a835aba1.json` | `2637543` | `False` |
| `data/review_queue/items/run_ab397f4ebf3b.json` | `2577973` | `False` |
| `data/review_queue/items/run_cc4c6f72fe66.json` | `2540872` | `False` |
| `data/reports/scheduler_run_run_4ec8eed57097.json` | `2004317` | `False` |
| `data/reports/scheduler_run_run_5427deeb2944.json` | `1994921` | `False` |
| `data/reports/scheduler_run_run_c28446cf84d7.json` | `1987031` | `False` |
| `data/paper_ledger/items/run_e067673ba7b6.json` | `1960980` | `False` |
| `data/paper_ledger/latest.json` | `1960980` | `False` |
| `data/review_queue/items/run_25533c9ec51a.json` | `1935180` | `False` |
| `data/review_queue/items/run_2800a835aba1.json` | `1905205` | `False` |
| `data/paper_ledger/paper_decisions.json` | `1866168` | `False` |
| `data/paper_ledger/items/run_a01fb4349e35.json` | `1801381` | `False` |
| `data/paper_ledger/items/run_cceedfd77cbb.json` | `1633579` | `False` |
| `data/paper_ledger/items/run_1621f541328e.json` | `1485989` | `False` |
| `data/reports/scheduler_run_run_b2f7d026bc7e.json` | `1329376` | `False` |
| `data/paper_ledger/items/run_c16122b189a2.json` | `1320325` | `False` |
| `data/reports/scheduler_run_run_a5c6a32aaeb7.json` | `1317772` | `False` |
| `data/reports/scheduler_run_run_33b9c252c6ca.json` | `1313928` | `False` |
| `data/reports/scheduler_run_run_c8e0d33b5227.json` | `1306896` | `False` |
| `data/review_queue/items/run_4ec8eed57097.json` | `1289564` | `False` |
| `data/review_queue/items/run_5427deeb2944.json` | `1289467` | `False` |
| `data/review_queue/items/run_c28446cf84d7.json` | `1280983` | `False` |
| `data/reports/scheduler_run_run_e7b7d178636b.json` | `1172996` | `False` |
| `data/paper_ledger/items/run_0ef22f23e0de.json` | `1155171` | `False` |
| `data/paper_ledger/items/run_9226f0cccdea.json` | `1012772` | `False` |
| `data/paper_ledger/items/run_2cf48386fb0a.json` | `989668` | `False` |
| `data/paper_ledger/items/run_614dca3fba6f.json` | `842829` | `False` |
| `data/paper_ledger/items/run_b832d5167563.json` | `842829` | `False` |
| `data/paper_ledger/items/run_7ef89d739bd8.json` | `823810` | `False` |
| `data/paper_ledger/items/run_ab397f4ebf3b.json` | `673732` | `False` |
| `data/paper_ledger/items/run_cc4c6f72fe66.json` | `657795` | `False` |
| `data/review_queue/items/run_b2f7d026bc7e.json` | `648458` | `False` |
| `data/review_queue/items/run_a5c6a32aaeb7.json` | `643745` | `False` |
| `data/review_queue/items/run_33b9c252c6ca.json` | `642241` | `False` |
| `data/review_queue/items/run_e7b7d178636b.json` | `642241` | `False` |
| `data/review_queue/items/run_c8e0d33b5227.json` | `639477` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_25533c9ec51a.json` | `602095` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_4ec8eed57097.json` | `596950` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_b2f7d026bc7e.json` | `594896` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_9226f0cccdea.json` | `592878` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_614dca3fba6f.json` | `585560` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_b832d5167563.json` | `585560` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_c28446cf84d7.json` | `579008` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_0ef22f23e0de.json` | `573520` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_a5c6a32aaeb7.json` | `570014` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_a01fb4349e35.json` | `568822` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_33b9c252c6ca.json` | `560879` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_e7b7d178636b.json` | `560879` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_ab397f4ebf3b.json` | `559384` | `False` |
| `data/snapshots/snapshots/kalshi_snapshot_run_5427deeb2944.json` | `558533` | `False` |

## Next Professional Action

Do not delete files yet. Review this report and apply targeted cleanup patches only where evidence supports a canonical owner decision.

Recommended immediate next step:

```text
Paste the summary command output back into ChatGPT.
Then patch additions/subtractions based on actual repo evidence.
```

