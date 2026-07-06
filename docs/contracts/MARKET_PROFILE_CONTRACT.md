# Market Profile Contract

The Market Profile Contract defines the canonical shape for a market family or market instance in this repository.

It is the reusable contract that market-specific logic builds on.

## Required fields

| Field | Meaning |
| --- | --- |
| `profile_id` | Stable identifier for the profile or profile instance |
| `profile_family` | Reusable family name such as `sports`, `prediction_markets`, or `options_0dte` |
| `canonical_identifiers` | Fields that uniquely identify the profile records |
| `required_timestamps` | Timestamps required for point-in-time safety |
| `canonical_fields` | Canonical field names that define the profile payload |
| `atomic_feature_groups` | Direct fields that do not require aggregation |
| `composite_feature_groups` | Derived feature families requiring multiple inputs |
| `validation_rules` | Validation expectations that must hold before use |
| `leakage_rules` | Rules that keep future information out of pre-event features |
| `storage_requirements` | Required storage families for the profile |
| `feature_store_requirements` | Required feature-store behavior for the profile |
| `backtest_requirements` | Required replay and validation behavior |
| `streamlit_requirements` | Required dashboard visibility for the profile |
| `research_requirements` | Required research-support behavior |
| `worldview_permissions` | What the future Worldview layer may request |
| `paper_trading_requirements` | What must exist before paper trading is allowed |
| `live_execution_gates` | What must exist before live execution is allowed |

## Contract principles

- Profiles are contracts, not implementations.
- Profiles should describe what the repository needs to know, not how every calculation is performed.
- Profiles must remain point-in-time aware.
- Profiles must expose leakage rules explicitly.
- Profiles must not encode provider credentials or private model logic.

## NFL relationship

NFL is the first Sports profile instance.

That means:

- the contract stays generic
- NFL is a configuration of the Sports profile family
- NFL-specific extensions belong under sports scope, not as a separate top-level market architecture

## Validation expectation

The framework validates:

- required identifiers
- required timestamps
- canonical field uniqueness
- family-specific field expectations
- duplicate profile IDs in the catalog or registry

The validation layer is intentionally lightweight so the contract can remain reusable without pulling in runtime providers or ingestion code.
