# Phase 10K8ZH5 - Core Probability Extraction

## Executive Summary
Probability ownership is canonical in `src/core/probability.py`.
The legacy `model_probability.py` file remains importable as a compatibility wrapper.
All logic stays local, deterministic, and calibration-safe.

## Current HEAD
`11c1432442d070500cc4853bc3acab79845cf908`

## Scope
- Probability clamping and normalization
- Independent input container
- Probability blending
- Adjustment capping
- Confidence scoring
- Probability-to-edge helpers

## Ownership Map
- Canonical target: `src/core/probability.py`
- Compatibility wrapper: `model_probability.py`
- Out of scope: connectors, providers, live calls, broker execution

## Compatibility Report
Legacy imports stay available while canonical ownership moves to `src/core/probability.py`.
No network, credential, or live model behavior is introduced.

