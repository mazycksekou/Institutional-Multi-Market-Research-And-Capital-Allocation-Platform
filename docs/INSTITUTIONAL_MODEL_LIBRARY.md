# Institutional Model Library

`math_models.institutional` is a structured, research-backed library of institutional investment model families. It is metadata-first and evaluation-only.

## Classifications

Each model is classified as one of:

- `alpha_model`
- `risk_model`
- `allocation_model`
- `execution_model`
- `liability_model`
- `regime_model`
- `validation_model`
- `reporting_model`

## Activation Tiers

Default activation for every new institutional model is `research_only`.

- `research_only` -> `backtest_ready` only when required inputs and tests exist
- `backtest_ready` -> `paper_trade_ready` only after out-of-sample validation
- `paper_trade_ready` -> `review_queue_ready` only after performance monitoring
- `review_queue_ready` -> `active_scoring_ready` only after calibration, drawdown, and governance checks

## Routing Rules

`model_router.py` routes models by market type, horizon, purpose, and available inputs.

Key constraints:

- allocation and liability models are blocked for short-horizon trading contexts
- institutional models do not create sportsbook-style recommendations
- alpha-style outputs cannot override risk or liability constraints
- default `research_only` models do not populate review-queue institutional fields

## Review Queue Use

Institutional model fields are only relevant when:

- the model is routed as eligible
- evidence score is at least `70`
- input quality score is at least `75`
- model risk rating is acceptable
- the output is relevant to the candidate market and horizon

These models are intended to enrich long-horizon portfolio, risk, liability, execution, and governance review rather than drive short-term event decisions.
