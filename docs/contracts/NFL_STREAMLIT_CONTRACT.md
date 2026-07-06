# NFL Streamlit Contract

This contract defines the NFL-related dashboard surfaces currently supported through the shared Streamlit facade.

## Contract Principle

The Streamlit layer should display canonical data and diagnostics, not own duplicate business logic or storage.

## Discovered NFL Display Surfaces

| Page / view | Primary widget type | Data source / helper | Notes |
|---|---|---|---|
| NFL Impact Readiness | summary cards, status tables, badges | `build_football_impact_readiness` via the facade | Readiness-first view for NFL capability. |
| NFL Impact Diagnostics | diagnostic cards, score panels, risk tables | `build_football_impact_diagnostics` via the facade | Main football diagnostics view. |
| NFL Open Data Sources | source tables, coverage tables | `nfl_open_data_sources` | Discovery and coverage view. |
| NFL Field Catalog | field tables, join-key tables | `build_nfl_open_data_field_catalog` | Field discovery / catalog surface. |
| NFL Feature Readiness | readiness cards, blocker lists | `build_nfl_open_data_feature_readiness_report` | Feature readiness state. |
| NFL Feature Builders | builder table, blocked reasons | `build_nfl_feature_builder_report` | Builder-level readiness. |
| NFL Backfill / Coverage | coverage matrix, session report | `build_nfl_open_data_backfill_report`, `build_nfl_open_data_coverage_matrix` | Backfill / coverage proof. |
| NFL Coaching Sources | source table, blocked-source table | `build_nfl_coaching_source_report` | Coaching source inventory. |
| NFL Coaching Features | feature report table | `build_nfl_coaching_feature_report` | Coaching feature readiness. |
| NFL Coaching Acquisition | acquisition report, templates | `build_nfl_coaching_acquisition_report` | Acquisition planning view. |
| NFL Cutoff Week Features | cutoff summary, leakage guards | `build_cutoff_feature_report` | Point-in-time safety view. |
| NFL Historical Pattern Lab | similarity catalog, validation scorecard | `build_nfl_historical_pattern_lab_report` | Pattern similarity discovery. |
| NFL Source Exhaustion | candidate-source table, blocked-reason table | `build_nfl_source_exhaustion_report` | Safe-source discovery. |
| Experiment History | ablation and calibration history cards | `get_feature_ablation_lab_snapshot_for_dashboard` and Streamlit history flow | Reusable experiment UI, not NFL-specific only. |

## Streamlit Contract Rules

- the dashboard should render reports and summaries, not invent data
- the dashboard should call canonical helpers through the facade
- the dashboard should not create duplicate NFL storage or duplicate feature logic
- any dashboard widget that exposes NFL data should preserve the same cutoff and provenance discipline as the back-end contract

## Current State

The dashboard layer already has meaningful NFL-facing readouts.
It still depends on discovery and readiness data rather than a fully validated NFL feature store.

