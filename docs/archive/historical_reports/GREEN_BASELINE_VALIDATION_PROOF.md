# Green Baseline Validation Proof

## Validation Commands

- `pytest -m smoke -q`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1 -Mode full`
- background process check for `pytest` / `run_tests.ps1`
- top-level scheduler absence check

## Recorded Results

- Smoke result: `19 passed`
- Ops result: `verification_ok`
- Full gate result: `4375 passed, 519 subtests passed in 1113.83s (0:18:33)`
- Background process result: `NO_BACKGROUND_PYTEST_OR_RUN_TESTS_PS1_PROCESSES`
- Top-level scheduler result: `TOP_LEVEL_AUTOMATION_SCHEDULER_ABSENT`

## Safety Notes

- The checkpoint preserves a green validated state.
- No background `pytest` or `run_tests.ps1` processes remained after validation completed.
- Top-level `automation_scheduler/` remains absent.
- The dirty tree at validation time already contained the large legacy-retirement payload; this proof confirms that payload was green when captured.
