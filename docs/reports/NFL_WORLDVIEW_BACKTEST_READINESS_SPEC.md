# NFL Worldview Backtest Readiness Spec

## Purpose

This spec defines how the future Worldview Intelligence Layer should ask about NFL backtest readiness.

It does not implement Worldview.

## Questions Worldview should be able to ask

- is NFL backtest-ready?
- which required fields are missing?
- which features are supported?
- which features are blocked by leakage?
- how many valid rows exist?
- what evidence package can be returned?
- why was a row excluded?
- why was a row marked no-trade?

## Evidence package

The repository should be able to return evidence containing:

- contract version
- profile family
- decision time
- snapshot IDs
- lineage IDs
- validation status
- exclusion reason
- sample floor status
- coverage window

## Compatibility rule

Worldview should only request experiments against rows or markets that have passed enough of the contract to support objective testing.

## Safety rule

Worldview must not treat result-only fields as pregame features.

## Usefulness rule

The best Worldview query is one that can be answered without guessing:

- the row is backtest-ready or it is not
- if it is not, the repo can say exactly why
