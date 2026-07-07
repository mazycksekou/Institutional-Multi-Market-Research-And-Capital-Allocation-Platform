# Minimum Backtest Row Contract

## Purpose

This contract defines the minimum historical row shape that can be used in a backtest.
It is reusable across sports, prediction markets, and options / 0DTE.

The contract answers one question:

> When is one historical event / contract row complete enough, time-safe enough, and traceable enough to use in a backtest?

## Canonical Backtest-Ready Definition

A row is backtest-ready when it has:

- one event or contract
- one market
- one decision time
- one aligned odds / price snapshot
- one aligned feature snapshot
- one eventual outcome
- one lineage chain
- one validation status
- no leakage violations
- a valid historical window

## Required Contract Areas

### 1. Required Identifiers

| Field | Why it is required |
| --- | --- |
| `market_profile` | Binds the row to the canonical market family. |
| `profile_family` | Identifies the reusable profile group, such as `sports`, `prediction_markets`, or `options_0dte`. |
| `season` or comparable historical partition | Makes the row reproducible within its historical window. |
| `event_or_contract_id` | Identifies the single event or contract represented by the row. |
| `market_type` | Distinguishes spread, moneyline, totals, contract price, or other supported market types. |
| `selection` | Identifies the side, contract leg, or price target being evaluated. |
| `provider_id` / `source_id` | Identifies the source that supplied the data. |
| `lineage_id` | Connects the row to the full source-to-result evidence chain. |

### 2. Required Timestamps

| Field | Why it is required |
| --- | --- |
| `decision_time` | Freezes the row at the model decision point. |
| `snapshot_time` / `odds_snapshot_time` | Proves the exact market snapshot used. |
| `feature_snapshot_time` | Proves the exact feature snapshot used. |
| `weather_snapshot_time` if used | Proves weather was known at decision time. |
| `injury_snapshot_time` if used | Proves injury data was frozen before the decision. |
| `team_stats_cutoff_time` if used | Proves historical stats were not future-looking. |
| `event_start_time` | Anchors the event start boundary. |
| `result_recorded_time` | Proves the outcome was attached only after the event finished. |

### 3. Required Market Fields

| Field | Why it is required |
| --- | --- |
| `market_type` | Defines the market being evaluated. |
| `line` | Captures the price or spread at the decision point. |
| `odds` | Captures the price or payout relationship at the decision point. |
| `book` / `provider` / `exchange` | Identifies the market source. |
| `snapshot_time` | Freezes the market state. |
| `price_type` | Distinguishes opening, live, decision-time, or closing context. |
| `opening_or_closing_classification` | Prevents closing data from being treated as pregame input. |

### 4. Required Feature Snapshot Fields

| Field | Why it is required |
| --- | --- |
| `feature_pack_version` | Identifies the exact feature bundle used. |
| `dataset_version` | Identifies the exact dataset state used. |
| `schema_version` | Proves the row shape is versioned. |
| `features_known_at_decision_time` | Documents only the inputs known at the cutoff. |
| `missing_feature_flags` | Explains incomplete rows explicitly. |
| `leakage_flags` | Marks any feature that would violate point-in-time safety. |

### 5. Required Outcome Fields

| Field | Why it is required |
| --- | --- |
| `final_result` | Provides the settled outcome. |
| `settlement_status` | Shows whether the row is final, pending, or void. |
| `win_loss_push` | Normalizes the outcome for evaluation. |
| `profit_loss` | Supports ROI and bankroll evaluation. |
| `closing_line` | Supports CLV analysis, not pregame input. |
| `clv` | Measures line movement after the decision. |
| `result_timestamp` | Proves the result was attached after the event. |

### 6. Required Validation Fields

| Field | Why it is required |
| --- | --- |
| `row_completeness_status` | States whether the row has every required field. |
| `point_in_time_status` | States whether the row is time-safe. |
| `leakage_status` | States whether any future information is present. |
| `source_quality_score` | Captures source trust and completeness. |
| `validation_errors` | Captures concrete failure reasons. |
| `no_trade_reason` | Explains why a row was skipped instead of used. |

### 7. Required Lineage Fields

| Field | Why it is required |
| --- | --- |
| `source_dataset_ids` | Identifies the upstream datasets used. |
| `provider_ids` | Identifies the source providers used. |
| `snapshot_ids` | Identifies the exact frozen snapshots used. |
| `transformation_ids` | Identifies the derivation path. |
| `feature_lineage_ids` | Connects the row to feature derivation. |
| `model_version` if applicable later | Lets future backtests map rows to model revisions. |

## Completeness Levels

The repository evaluates backtest readiness at three levels:

1. **Field completeness**
   - Do all required fields exist at all?
2. **Historical-window completeness**
   - Do enough complete rows exist across a valid historical window?
3. **Event-row completeness**
   - Do all required fields align to the same event / contract and the same decision time?

A field being present somewhere in the repository is not enough.
It must be present for the row being tested.

## Minimum Readiness Rule

A market is backtest-ready only when all of the following are true:

- every required field family is present for the same event or contract
- every required field family aligns to the same decision time
- every feature used in the row was known at or before decision time
- every outcome field is attached only after event completion
- no unresolved leakage violation exists
- the historical sample floor for the market family has been met
- every excluded row has a clear exclusion reason

## Readiness Levels

| Level | Meaning |
| --- | --- |
| Minimum Ready | The row shape is complete enough to run the first baseline backtest gate. |
| Research Ready | The row shape is complete enough for analysis and hypothesis testing, even if the sample is still small. |
| Strong Ready | The row shape is complete, leakage-safe, and supported by enough history for stable analysis. |
| Production Candidate Ready | The row shape is complete, stable, reproducible, and strong enough for a release candidate. |

## Exclusion and No-Trade States

| State | Meaning |
| --- | --- |
| `BACKTEST_ELIGIBLE` | The row is complete, time-safe, and usable in a backtest. |
| `NO_TRADE` | The row is complete enough to evaluate but the strategy should skip it. |
| `EXCLUDED` | The row is not usable because a required field, timestamp, or lineage step is missing or unsafe. |
| `NEEDS_REVIEW` | The row is ambiguous and needs a human or rule-based decision before use. |

Common exclusion reasons include:

- missing odds snapshot
- missing result
- missing decision time
- feature timestamp after decision time
- weather actual used instead of forecast
- injury update after decision time
- closing line used as a pregame feature
- missing lineage
- invalid market profile
- unsupported market type
- low source quality

## Streamlit Readiness Specification

Future dashboards should show:

- required fields complete
- usable rows
- excluded rows
- exclusion reasons
- seasons covered
- market types covered
- leakage warnings
- validation status
- readiness percentage
- backtest-ready yes / no

## Worldview Compatibility

The future Worldview Intelligence Layer should be able to ask:

- is this market backtest-ready?
- which fields are missing?
- which features are allowed?
- which features are blocked by leakage?
- how many valid rows exist?
- what evidence package can be returned?

The contract does not implement Worldview.
It only makes the evidence answerable.

## Reuse Across Market Families

This contract is designed to work for:

- Sports
- Prediction Markets
- Options / 0DTE

Each family can add its own field names and sample floor, but the minimum logic stays the same:

one event or contract, one market, one decision time, one frozen snapshot set, one outcome, one lineage chain, one validation status.
