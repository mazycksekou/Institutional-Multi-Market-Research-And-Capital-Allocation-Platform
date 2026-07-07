# NFL Feature Readiness Matrix

This matrix states what each feature needs before implementation.

| Readiness Status | Feature IDs | Reason | Next requirement |
| --- | --- | --- | --- |
| Ready | NFL_F001 NFL_F002 NFL_F003 NFL_F032 | Foundation contracts and source shapes already exist | preserve as canonical inputs |
| Needs Provider | NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F013 NFL_F015 NFL_F017 NFL_F030 | Requires timestamped source lane before use | validate free or local source and snapshot timing |
| Needs Calculation | NFL_F009 NFL_F011 NFL_F012 NFL_F014 NFL_F016 NFL_F018 NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F031 | Inputs are known but deterministic formulas and versions are not implemented | define formula version and dependency checks |
| Needs Validation | NFL_F004 NFL_F010 NFL_F033 NFL_F035 NFL_F040 | Logic or fields exist conceptually but require outcome, cutoff, or data-quality proof | validate against historical rows and point-in-time rules |
| Needs Research | NFL_F024 NFL_F025 NFL_F026 NFL_F027 NFL_F028 NFL_F029 NFL_F039 NFL_F041 | Useful but requires stronger definition or evidence | run research notebooks or controlled studies after data foundation |
| Deferred | NFL_F034 NFL_F036 NFL_F037 NFL_F038 | Useful later but outside the first team/game baseline | revisit after baseline backtest is stable |
| Blocked | none | No feature is blocked by policy; deferred items are intentionally not first-slice work | keep blocked status for future legal or source issues |

## Readiness Gate

A feature cannot move to implementation unless it has:

- source timing
- storage target
- formula version if composite
- leakage classification
- validation rule
- registry entry
