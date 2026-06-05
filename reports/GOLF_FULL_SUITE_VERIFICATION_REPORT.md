# Golf Full Suite Verification Report

- full_suite_status: clean_in_deterministic_chunks_full_command_timeout_only
- original_failure_reproduced: True
- original_failure_type: timeout_only_on_monolithic_pytest_with_300_second_tool_limit; prior stdout OSError not reproduced during verbose rerun
- failing_test_if_any: None
- root_cause: The full monolithic command exceeds the 5-minute command timeout. Deterministic chunks covering every tests/test_*.py file passed, so no filesystem/path, isolation, generated report path, unrelated dirty-file interaction, or real regression was found.
- tests_passed: 3492
- tests_failed: 0
- tests_timed_out: 1
- chunked_full_suite_equivalent: True
- unresolved_risk: Monolithic full-suite invocation remains longer than the 300-second tool timeout; use deterministic chunks or a longer external timeout for single-command full-suite runs.
- safety_flags_clean: True

## Chunks
- chunk 1: files 1-50 status=passed duration_seconds=29.07
- chunk 2: files 51-100 status=passed duration_seconds=42.46
- chunk 3: files 101-150 status=passed duration_seconds=40.96
- chunk 4: files 151-200 status=passed duration_seconds=13.27
- chunk 5: files 201-250 status=passed duration_seconds=44.71
- chunk 6: files 251-300 status=passed duration_seconds=46.11
- chunk 7: files 301-350 status=passed duration_seconds=16.11
- chunk 8: files 351-400 status=passed duration_seconds=28.74
- chunk 9: files 401-450 status=passed duration_seconds=28.26
- chunk 10: files 451-454 status=passed duration_seconds=4.14

## Tests Run
- `python -m pytest tests -q --maxfail=1 -vv`
- `python -m pytest <PowerShell-expanded tests/test_golf*.py> -q`
- `python -m pytest <PowerShell-expanded tests/test_*policy*.py> -q`
- `python -m pytest <PowerShell-expanded tests/test_*source*.py> -q`
- `python -m pytest <PowerShell-expanded tests/test_*loader*.py> -q`
- `python -m pytest <PowerShell-expanded tests/test_*readiness*.py> -q`
- `python -m pytest <PowerShell-expanded tests/test_*final*.py> -q`
- `python -m compileall automation_scheduler scripts tests`
- `python -m pytest tests --collect-only -q`
- `deterministic chunks: python -m pytest <50 test files per chunk> -q for all tests/test_*.py files`

## Unrelated Dirty Files Preserved
- ` M automation_scheduler/combat_availability_context.py`
- ` M automation_scheduler/combat_damage_durability_context.py`
- ` M automation_scheduler/combat_data_availability.py`
- ` M automation_scheduler/combat_grappling_control_impact.py`
- ` M automation_scheduler/combat_impact_calibration.py`
- ` M automation_scheduler/combat_impact_common.py`
- ` M automation_scheduler/combat_impact_readiness.py`
- ` M automation_scheduler/combat_impact_red_team.py`
- ` M automation_scheduler/combat_impact_report.py`
- ` M automation_scheduler/combat_incentive_context.py`
- ` M automation_scheduler/combat_market_relevance.py`
- ` M automation_scheduler/combat_matchup_context.py`
- ` M automation_scheduler/combat_pace_cardio_context.py`
- ` M automation_scheduler/combat_phase_control_context.py`
- ` M automation_scheduler/combat_ruleset_referee_judging_context.py`
- ` M automation_scheduler/combat_striking_impact.py`
- ` M docs/MANUAL_IMPORT_TEMPLATES_BASKETBALL.md`
