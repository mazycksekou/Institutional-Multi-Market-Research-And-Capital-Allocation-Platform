# NFL Worldview Readiness

This document defines how the future Worldview Intelligence Layer should interact with NFL once the baseline research slice exists.

## Intent

The Worldview layer is a research scientist.
It proposes hypotheses and experiments.
It does not invent results and it does not bypass the repository's lifecycle gates.

## Allowed Hypothesis Request Shape

| Field | Meaning |
| --- | --- |
| hypothesis_id | Unique experiment identifier |
| market | NFL spread, moneyline, or totals for the baseline slice |
| question | The hypothesis to test |
| candidate_features | Allowed point-in-time safe features |
| blocked_features | Features excluded due to leakage or timing risk |
| data_window | Exact seasons / weeks / folds to evaluate |
| success_metrics | ROI, CLV, calibration, log loss, drawdown |
| required_evidence | The artifact package the repo must return |
| human_review_required | Whether approval is needed before promotion |

## Allowed Experiment Types

- feature ablation
- model comparison
- walk-forward comparison
- leakage audit
- calibration comparison
- baseline vs candidate evaluation

## Evidence Package Returned by the Repository

The repository should return a reproducible evidence bundle containing:

- dataset version identifiers
- snapshot identifiers
- feature pack version
- model version
- backtest row set
- fold summaries
- CLV / ROI summary
- calibration results
- leakage report
- no-trade reasons, if any

## Human Review View

The reviewer should be able to see:

- what hypothesis was tested
- what data was allowed
- what data was blocked
- what evidence was produced
- whether the experiment passed the gate
- why the decision was made

## Readiness Rule

Worldview requests are only appropriate once the market has:

- a reproducible data contract,
- point-in-time-safe features,
- a validated baseline backtest path,
- and an evidence package that can be reviewed without tribal knowledge.

