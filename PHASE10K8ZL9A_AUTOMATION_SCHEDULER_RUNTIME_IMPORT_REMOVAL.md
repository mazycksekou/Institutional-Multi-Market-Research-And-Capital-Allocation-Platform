# PHASE 10K8ZL9A Automation Scheduler Runtime Import Removal

Starting HEAD: `c11e9f0fbf9f5cb640ff20adb6459a2dbda3dc8f`

Scope: remove direct `automation_scheduler` imports from the eight runtime entrypoints only. No scheduler deletion, no test mass-redirection, no live behavior changes.

## Runtime files updated

- `main.py`
- `streamlit_app.py`
- `src/api/automation_review_outcomes_routes.py`
- `src/api/provider_status_routes.py`
- `src/brokerage/readiness.py`
- `src/services/execution_service.py`
- `src/services/ledger_service.py`
- `src/services/settlement_service.py`

## Redirection summary

- `main.py` now imports scheduler-facing helpers through `src.services.automation_scheduler_facade`.
- `streamlit_app.py` now imports dashboard helpers through `src.services.streamlit_dashboard_facade`.
- `src/api/automation_review_outcomes_routes.py` now uses the already injected `src.api.automation_security.validate_cron_token` instead of importing scheduler validation helpers locally.
- `src/api/provider_status_routes.py` now imports provider compaction helpers from `src.services.automation_scheduler_facade`.
- `src/brokerage/readiness.py` now imports disabled-readiness support from `src.brokerage.readiness_support` plus canonical `src.providers`, `src.research`, and `src.services` helpers.
- `src/services/execution_service.py` now imports execution helpers from `src.services.execution_support`.
- `src/services/ledger_service.py` now imports ledger helpers from `src.services.ledger_support`.
- `src/services/settlement_service.py` now imports settlement helpers from `src.services.settlement_support`.

## Exact runtime imports removed

- `import automation_scheduler`
- `from automation_scheduler.data_paths import get_runtime_data_path, get_automation_data_dir`
- `from automation_scheduler.response_compactor import ...`
- `from automation_scheduler.collector_scheduled_runner import validate_cron_token`
- `from automation_scheduler.owner_approval_gate import evaluate_owner_approval`
- `from automation_scheduler.provider_allowlist import classify_provider`
- `from automation_scheduler.risk_limit_guard import evaluate_risk_limits`
- `from automation_scheduler.secret_safety import redact_sensitive, secret_safety_fields`
- `from automation_scheduler.security_event_types import EXECUTION_ATTEMPT_BLOCKED`
- `from automation_scheduler.security_policy import locked_safety_flags`
- `from automation_scheduler.balance_sheet_risk import evaluate_balance_sheet`
- `from automation_scheduler.candlestick_pattern_detector import detect_candlestick_patterns`
- `from automation_scheduler.data_paths import get_storage_health, resolve_base_data_dir`
- `from automation_scheduler.liquidity_context_scoring import calculate_float_rotation, score_liquidity_context`
- `from automation_scheduler.scheduler_config import safe_run_id, sanitize_filename, utc_now_iso`
- `from automation_scheduler.session_risk_rules import evaluate_session_risk, score_time_of_day`
- `from automation_scheduler.institutional_cross_asset_adapters import compact_redact, read_existing_outputs`
- `from automation_scheduler.institutional_cross_asset_calibration import build_calibration_by_asset_class`
- `from automation_scheduler.institutional_risk_engine import assess_institutional_risk`
- `from automation_scheduler.strategy_context_buckets import build_context_bucket`
- `from automation_scheduler.pattern_review_queue import build_pattern_review_item`
- `from automation_scheduler.pattern_review_queue import persist_pattern_review_queue, summarize_pattern_review_queue`
- `from automation_scheduler.scheduler_config import SCHEMA_VERSION, hash_payload, safe_run_id, sanitize_filename, utc_now_iso`
- `from automation_scheduler.secret_safety import redact_sensitive, secret_safety_fields`
- `from automation_scheduler.security_event_types import normalize_event_type`
- `from automation_scheduler.security_policy import locked_safety_flags`
- `from automation_scheduler.data_paths import resolve_base_data_dir`
- `from automation_scheduler.institutional_cross_asset_adapters import compact_redact`
- `from automation_scheduler.scheduler_config import sanitize_filename, utc_now_iso`
- `from automation_scheduler.outcome_store import PERSISTABLE_SOURCES, validate_outcome_record`

## Zero-import proof target

The direct runtime imports above are removed from those eight files. The remaining `automation_scheduler` references are dependency-injection variables, facade aliases, or other non-import source text.

## Remaining blockers

- `automation_scheduler` still exists on disk.
- Internal scheduler self-imports remain.
- Test imports remain.

## Next step

Break internal scheduler self-imports and then redirect test imports in the next phase.
