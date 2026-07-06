# NFL Streamlit Reporting Blueprint

This blueprint defines what the first NFL dashboard slice must show.
The goal is not flashy presentation; the goal is trust, readiness, and evidence.

## Required Views

| View | Required content |
| --- | --- |
| Dataset readiness | Which datasets exist, which are missing, version status, freshness status |
| Provider readiness | Which source families are usable, blocked, deferred, or manual |
| Feature readiness | Which P0 / P1 features are available and point-in-time safe |
| Leakage warnings | Which fields are unsafe, stale, or missing timestamps |
| Backtest summary | ROI, CLV, calibration, log loss, drawdown, sample size |
| CLV summary | Closing line value by bucket, by market, by fold |
| ROI summary | Gross / net ROI, stake assumptions, and confidence intervals |
| Calibration chart | Probability calibration vs outcomes |
| Model comparison | Baseline model vs candidate model vs no-skill benchmark |
| No-trade reasons | Why the system declined to place a trade |
| Worldview readiness | Whether the experiment evidence package is strong enough |

## Required Widgets

- readiness tables
- status badges
- feature availability counts
- snapshot freshness indicators
- fold-by-fold performance charts
- leakage warning callouts
- evidence links to the relevant docs

## Dashboard Rules

- Do not display postgame fields as if they are pregame evidence.
- Do not hide timing gaps.
- Do not collapse source quality into a single green badge.
- Do not imply model readiness when the backtest gate has not passed.

## Value of the First Dashboard

The first dashboard should answer:

1. Can we trust the dataset?
2. Can we trust the feature timing?
3. Can we trust the backtest?
4. Can we explain the result to a reviewer?

