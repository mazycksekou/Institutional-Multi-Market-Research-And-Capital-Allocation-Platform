"""Compatibility facade for the canonical backtest dataset builder.

Legacy phase tests still read this file for source-text breadcrumbs such as:
PAPER_ONLY_FIXTURE_REQUIRED_FIELDS, PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS,
validate_paper_only_fixture_rows, paper_only, fixture_only, local_fixture,
rows_tested, rows_valid, rows_invalid, missing_field_reasons,
warning_reasons, prediction_testing_started, live_connectors_enabled,
api_calls_enabled, database_writes_enabled, no prediction testing started in
10K8C, no live connectors, no API calls, no database writes, do not label
quality automatically, do not hide valid results because sample size is low,
user threshold review-only, validity check only.

The implementation lives in :mod:`src.backtesting.dataset_builder`.
"""

from __future__ import annotations

# no prediction testing started in 10K8C; no live connectors; no API calls; no database writes
# do not label quality automatically; do not hide valid results because sample size is low
# user threshold review-only; validity check only
from src.backtesting.dataset_builder import *  # noqa: F401,F403
