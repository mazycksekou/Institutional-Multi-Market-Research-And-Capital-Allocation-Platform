# NFL Feature Priority Matrix

This matrix classifies the canonical NFL feature families discovered in Phase 4.1.
It focuses on the first reusable model slice, not on every possible future player prop or tracking feature.

Legend:

- **P0** = required for the first baseline model
- **P1** = required for a strong baseline
- **P2** = useful after the baseline works
- **P3** = future extension
- **DEFER** = do not implement yet

| Canonical feature | Priority | Type | Primary source type | Point-in-time safe? | Leakage risk | Expected value | Backtest use | Streamlit use | Worldview use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| game_id / season / week / kickoff / home-away | P0 | ATOMIC_FEATURE | LOCAL_CSV / OPEN_DATA | Yes | Low | Foundation only | Join key | Readiness panel | Evidence anchor |
| market open spread | P0 | ATOMIC_FEATURE | FREE_API / LOCAL_CSV / OPEN_DATA | Yes | Medium if snapshot timing is missing | High | Baseline spread model | Odds panel | Experiment control |
| market open total | P0 | ATOMIC_FEATURE | FREE_API / LOCAL_CSV / OPEN_DATA | Yes | Medium if snapshot timing is missing | High | Baseline totals model | Odds panel | Experiment control |
| market open moneyline | P0 | ATOMIC_FEATURE | FREE_API / LOCAL_CSV / OPEN_DATA | Yes | Medium if snapshot timing is missing | Medium | Baseline comparison | Odds panel | Experiment control |
| rest days | P0 | COMPOSITE_FEATURE | Schedule + kickoff timestamps | Yes | Low | High | Core context | Feature readiness | Hypothesis input |
| travel distance | P0 | COMPOSITE_FEATURE | Venue + team geography | Yes | Low | Medium | Context feature | Feature readiness | Hypothesis input |
| offensive efficiency recent | P0 | COMPOSITE_FEATURE | Open play-by-play / results | Yes if cutoff before decision time | Medium | High | Core signal | Feature panel | Hypothesis input |
| defensive efficiency recent | P0 | COMPOSITE_FEATURE | Open play-by-play / results | Yes if cutoff before decision time | Medium | High | Core signal | Feature panel | Hypothesis input |
| pace / play volume recent | P0 | COMPOSITE_FEATURE | Open play-by-play | Yes if cutoff before decision time | Medium | High | Core signal | Feature panel | Hypothesis input |
| roster continuity | P0 | COMPOSITE_FEATURE | Roster / schedule / results | Yes if snapshot is frozen | Medium | Medium | Stabilizer | Feature readiness | Hypothesis input |
| coaching continuity | P0 | COMPOSITE_FEATURE | Coaching sources + roster history | Yes if timestamped | Medium | Medium | Stabilizer | Feature readiness | Hypothesis input |
| injury-adjusted availability | P0 | COMPOSITE_FEATURE | Injury / availability snapshots | Yes if timestamped | High if late injury changes leak in | High | Core signal | Leakage warning panel | Hypothesis input |
| weather forecast impact | P0 | COMPOSITE_FEATURE | Forecast snapshots | Yes if forecast is pregame | Medium | Medium | Core signal | Weather panel | Hypothesis input |
| depth chart rank / starter status | P1 | ATOMIC_FEATURE | Depth chart snapshots | Yes if timestamped | High if post-release updates leak in | High | Strengthens player context | Feature readiness | Hypothesis input |
| official crew tendency | P1 | COMPOSITE_FEATURE | Officials assignment + historical tendencies | Usually yes | Low to medium | Medium | Context / calibration | Feature panel | Hypothesis input |
| pregame market movement snapshot | P1 | COMPOSITE_FEATURE | Odds snapshots across decision-time checkpoints | Yes if frozen before decision | High if closing data leaks in | High | Market intelligence | Odds movement view | Hypothesis input |
| offensive line score | P1 | COMPOSITE_FEATURE | Open data + roster / results | Yes if built from prior games | Medium | High | Unit strength | Feature panel | Hypothesis input |
| defensive line pressure score | P1 | COMPOSITE_FEATURE | Open data + roster / results | Yes if built from prior games | Medium | High | Unit strength | Feature panel | Hypothesis input |
| red zone efficiency | P1 | COMPOSITE_FEATURE | Play-by-play / drive data | Yes if cutoff before game | Medium | High | Efficiency feature | Feature panel | Hypothesis input |
| third down efficiency | P1 | COMPOSITE_FEATURE | Play-by-play / drive data | Yes if cutoff before game | Medium | Medium | Efficiency feature | Feature panel | Hypothesis input |
| special teams efficiency | P1 | COMPOSITE_FEATURE | Play-by-play / results | Yes if cutoff before game | Medium | Medium | Context feature | Feature panel | Hypothesis input |
| pass rush pressure allowed | P1 | COMPOSITE_FEATURE | Play-by-play / charting proxy | Usually yes if historical only | Medium | Medium | Unit matchup | Feature panel | Hypothesis input |
| draft capital / combine context | P2 | COMPOSITE_FEATURE | Draft / combine tables | Yes historically | Low | Low to medium | Optional context | Advanced panel | Future experiment |
| explosive play rate | P2 | COMPOSITE_FEATURE | Play-by-play / results | Yes if cutoff before game | Medium | Medium | Optional context | Advanced panel | Future experiment |
| turnover luck / turnover rate trend | P2 | COMPOSITE_FEATURE | Play-by-play / results | Yes if cutoff before game | Medium | Medium | Optional context | Advanced panel | Future experiment |
| route participation / target share | DEFER | COMPOSITE_FEATURE | Player tracking / participation | Often not safely available yet | High | High later | Deferred | Deferred | Future experiment |
| tracking data | DEFER | COMPOSITE_FEATURE | Tracking / paid charting | Usually not available in the current slice | High | High later | Deferred | Deferred | Future experiment |

## Notes

- Atomic features should remain cheap to add later.
- Composite features should be computed from versioned, point-in-time-safe inputs.
- Anything that depends on postgame outcomes stays out of the pregame feature set.
- The first baseline model should prefer stable team/game features over player-level complexity.

