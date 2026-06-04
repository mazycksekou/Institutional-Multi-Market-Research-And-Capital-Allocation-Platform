# MLB Open Data Expansion

This repo now has a disabled-by-default MLB open-data stack that mirrors the existing NFL workflow:

- `automation_scheduler/mlb_open_data_sources.py` for the registry and source posture
- `automation_scheduler/mlb_open_data_source_exhaustion.py` for source-family and field novelty auditing
- `automation_scheduler/mlb_open_data_field_catalog.py` for source-to-field cataloging
- `automation_scheduler/mlb_open_data_backfill.py` for metadata checks, tiny samples, and coverage matrices
- `automation_scheduler/mlb_open_data_feature_builders.py` for provenance-only feature readiness
- `automation_scheduler/mlb_open_data_feature_readiness.py` for catalog, exhaustion, cutoff, and readiness summaries
- `automation_scheduler/mlb_cutoff_date_features.py` for point-in-time snapshots with future-data guards
- `automation_scheduler/mlb_structured_seed_sources.py` and `automation_scheduler/mlb_structured_seed_adapters.py` for CC0 structured seed handling

Safety posture stays fixed:

- no provider writes
- no execution or betting/trading actions
- no raw HTML persistence
- no raw provider payload persistence
- no secret capture
- no paid source enablement
- no browser automation or spoofing

Approved open lanes are represented as metadata-only or local validated-row workflows. Blocked lanes remain blocked until terms, access, or budget constraints are explicitly cleared.

## Entry Points

- `scripts/check_mlb_open_data_sources.ps1`
- `scripts/run_mlb_open_data_field_catalog.ps1`
- `scripts/run_mlb_open_data_backfill.ps1`
- `scripts/run_mlb_open_data_feature_readiness.ps1`
- `scripts/run_mlb_source_exhaustion.ps1`
- `scripts/run_mlb_cutoff_features.ps1`
- `scripts/run_mlb_structured_seed_import.ps1`

## Notes

- Retrosheet and Lahman are used as the open historical backbone.
- MLB Stats API lanes are represented only when they are open/public and the adapter posture stays no-call or explicit safe local ingestion.
- Statcast/Baseball Savant and market-odds lanes remain blocked unless a safe, terms-clear, no-scrape path is verified.
- The derived feature backfill report now carries MLB readiness signals alongside the existing NFL ones.
