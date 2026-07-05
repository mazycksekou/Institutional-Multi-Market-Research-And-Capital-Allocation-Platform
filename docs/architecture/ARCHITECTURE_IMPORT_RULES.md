# Architecture Import Rules

Checked by `scripts/check_architecture.py` and integrated into `scripts/ops_check.py`.

Rules enforced in the active gate:

- No direct executable imports of `automation_scheduler`
- No direct executable imports of `automation_scheduler_legacy`
- No direct executable imports of `src.automation_scheduler_legacy`
- No direct executable imports of `src.services.automation_scheduler_facade`
- No ignored `src/**/*.py` files
- No root Markdown files outside the allowlist

Archived migration-proof tests are excluded from active import enforcement when they match the archived-test policy in `tests/conftest.py`.
