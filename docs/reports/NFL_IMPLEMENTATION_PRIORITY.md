# NFL Implementation Priority

This priority plan converts the feature registry into a future build order.
It is not an implementation.

## P0 Foundation

Build first:

- NFL_F001 game_id season week kickoff home_away
- NFL_F002 team identity
- NFL_F003 kickoff timing
- NFL_F004 final score result
- NFL_F005 market open spread
- NFL_F006 market open total
- NFL_F007 market open moneyline
- NFL_F008 odds at decision time
- NFL_F011 rest days
- NFL_F012 travel distance
- NFL_F013 weather forecast inputs
- NFL_F014 weather impact score
- NFL_F015 injury status
- NFL_F016 injury adjusted availability
- NFL_F018 roster continuity
- NFL_F019 offensive efficiency recent
- NFL_F020 defensive efficiency recent
- NFL_F021 pace play volume recent
- NFL_F032 coaching staff identity
- NFL_F033 coaching continuity
- NFL_F035 player usage snaps

## P1 Strong Baseline

Build after the foundation validates:

- NFL_F009 pregame market movement
- NFL_F010 closing line value
- NFL_F017 depth chart rank starter status
- NFL_F022 red zone efficiency
- NFL_F023 third down efficiency
- NFL_F026 offensive line score
- NFL_F027 defensive line pressure score
- NFL_F028 pass rush pressure allowed
- NFL_F029 special teams efficiency
- NFL_F030 official crew identity
- NFL_F031 official crew tendency
- NFL_F039 market relevance score
- NFL_F040 calibration confidence

## P2 Research Expansion

Build only after the baseline backtest is reproducible:

- NFL_F024 explosive play rate
- NFL_F025 turnover rate trend
- NFL_F034 draft capital combine context
- NFL_F041 pattern similarity score

## Deferred

Do not build until player-level source quality and timing are proven:

- NFL_F036 route participation target share
- NFL_F037 tracking data bundle
- NFL_F038 player props input bundle

## Recommended Phase 4.3 Slice

The smallest useful implementation slice is:

1. schedule and results storage
2. odds snapshot storage
3. weather and injury snapshot contracts
4. baseline feature snapshot schema
5. no-leakage validation for decision-time snapshots

This sequence keeps the platform reusable and avoids jumping into player props before the team/game foundation is reproducible.
