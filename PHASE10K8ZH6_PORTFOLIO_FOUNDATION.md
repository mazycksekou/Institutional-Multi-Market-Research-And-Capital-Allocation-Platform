# Phase 10K8ZH6 - Portfolio Foundation

## Executive Summary
Portfolio ownership is canonical in `src/core/portfolio.py`.
The module stays pure Python and only reasons about exposure, concentration, and correlation.

## Scope
- position_exposure
- total_exposure
- exposure_weights
- concentration_score
- correlated_exposure
- portfolio_summary

## Ownership Map
- Canonical target: `src/core/portfolio.py`
- Compatibility: none required yet
- Out of scope: providers, connectors, live execution, dashboard rewrite

