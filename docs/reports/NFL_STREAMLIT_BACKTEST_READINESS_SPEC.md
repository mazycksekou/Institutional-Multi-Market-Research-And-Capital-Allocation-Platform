# NFL Streamlit Backtest Readiness Spec

## Purpose

This spec defines what the future dashboard should show for NFL backtest readiness.

It does not implement dashboard code.

## Required views

| View | What it should show |
| --- | --- |
| Required fields complete | Whether the 13 / 13 required P0 field families are present |
| Usable rows | How many rows are backtest-eligible |
| Excluded rows | How many rows were excluded |
| Exclusion reasons | Why rows were skipped or excluded |
| Seasons covered | Which seasons are represented |
| Market types covered | Spread, moneyline, totals, or other supported markets |
| Leakage warnings | Which rows or features were unsafe |
| Validation status | Whether the row batch passed validation |
| Readiness percentage | How close the dataset is to the readiness bar |
| Backtest-ready yes / no | The final readiness decision |

## Recommended widgets

- readiness summary cards
- completeness table
- exclusion reason table
- seasons / market coverage table
- leakage warning panel
- validation status banner
- sample floor progress bar

## Display rule

Do not show a dataset as backtest-ready unless the row contract is satisfied.

## Evidence rule

Every dashboard value should trace back to the stored row-level evidence:

- decision time
- snapshot IDs
- lineage IDs
- validation status
- exclusion reason
