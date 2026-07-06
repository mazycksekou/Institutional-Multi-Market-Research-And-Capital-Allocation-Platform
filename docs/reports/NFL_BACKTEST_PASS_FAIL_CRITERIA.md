# NFL Backtest Pass / Fail Criteria

This document defines the first gate for a baseline NFL backtest.
It is intentionally conservative so the first reusable slice does not confuse noise with signal.

## Gate 1: Data Sufficiency

Pass only if:

- the dataset covers at least **2 full regular seasons**, or
- the dataset contains at least **400 resolved game rows**, whichever is greater
- every row is point-in-time safe
- all required snapshot timestamps are present
- no row mixes pregame inputs with postgame truth

## Gate 2: Validation Structure

Pass only if:

- the evaluation uses chronological splits
- at least **3 walk-forward folds** are present
- no random shuffle split is used
- the holdout period is strictly later than the training period

## Gate 3: Market Performance

Pass only if the candidate model shows:

- positive out-of-sample ROI after cost / vig assumptions
- positive average CLV on evaluated wagers
- calibration that beats a no-skill baseline
- log loss that beats a market-implied baseline

## Gate 4: Risk Control

Pass only if:

- maximum drawdown stays within the approved bankroll threshold
- edge buckets behave monotonically or at least do not collapse in the highest-confidence bucket
- no single-fold result drives the entire conclusion

## Gate 5: Overfitting Protection

Pass only if:

- the train/test gap stays within the approved tolerance
- feature importance does not swing wildly fold to fold
- simple sanity checks beat or match random/no-skill baselines
- leakage warnings are empty or explicitly explained

## Minimum Confidence Rules

Do not place a trade if:

- the snapshot timing is incomplete
- the odds are stale beyond the configured cutoff
- the injury / weather / depth chart snapshot is missing a timestamp
- the model edge does not clear the vig / cost threshold
- the backtest row is not fully reproducible

## No-Trade Rules

The system should record a no-trade reason when:

- data is incomplete
- timing is unsafe
- the model is under threshold
- the feature pack version is not valid
- the evaluation window is too small
- the fold is not chronologically valid

## Recommended First Promotion Bar

The first model should not be promoted just because it is "better than random."
It should be promoted only if it is reproducible, point-in-time safe, and clearly better than the baseline across multiple forward folds.

