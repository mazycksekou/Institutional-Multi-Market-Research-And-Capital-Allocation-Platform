# NFL Point-in-Time Leakage Review

This review classifies the key NFL fields and feature families by timing risk.
The rule is simple: if a field is not safe at the decision time, it cannot be treated as a pregame feature.

## Timing Classes

- **POINT_IN_TIME_SAFE** - known before the decision point and frozen by snapshot
- **LEAKAGE_RISK** - can leak future information if not time bounded
- **RESULT_ONLY** - only valid after the game is settled
- **POST_EVENT_ONLY** - only valid after the event and not usable as a pregame input
- **UNKNOWN_TIMING** - not yet proven safe

| Field / family | Timing class | Why | Allowed use |
| --- | --- | --- | --- |
| game_id / season / week / kickoff | POINT_IN_TIME_SAFE | Scheduled before the game | Join key, not a predictive feature by itself |
| home / away team identifiers | POINT_IN_TIME_SAFE | Known before kickoff | Predictive context |
| open odds snapshot | POINT_IN_TIME_SAFE | Safe only when timestamped before decision time | Pregame feature |
| market movement before decision time | POINT_IN_TIME_SAFE | Safe if cutoff is frozen | Pregame feature |
| closing line | LEAKAGE_RISK for pregame features | Closing data can reflect information after the decision point | Evaluation only, not pregame input |
| final score | RESULT_ONLY | Outcome field | Backtest labels, not feature input |
| yards / EPA / efficiency from the game | RESULT_ONLY | Outcome-dependent | Evaluation and training labels only |
| weather forecast snapshot | POINT_IN_TIME_SAFE | Forecast is known before kickoff if time-stamped | Pregame feature |
| actual game weather | POST_EVENT_ONLY | The realized condition can only be known later | Evaluation / analysis only |
| injury report snapshot | POINT_IN_TIME_SAFE | Safe only when captured before decision time | Pregame feature |
| late injury news after model cutoff | LEAKAGE_RISK | Can reveal unavailable future information | Excluded |
| depth chart snapshot | POINT_IN_TIME_SAFE | Safe only when timestamped | Pregame feature |
| depth chart changes after cutoff | LEAKAGE_RISK | Can leak roster updates | Excluded |
| official assignment | POINT_IN_TIME_SAFE | Safe when posted before kickoff | Pregame context |
| player participation / snap counts from the game | POST_EVENT_ONLY | Only known after the game begins or ends | Evaluation / research only |
| roster continuity trend from prior weeks | POINT_IN_TIME_SAFE | Safe if built from prior-game history only | Pregame feature |
| coaching continuity | POINT_IN_TIME_SAFE | Safe when derived from pregame staff history | Pregame feature |
| betting market close / consensus after decision time | LEAKAGE_RISK | May encode the answer too directly | Evaluation only |
| player tracking or route share from the game | POST_EVENT_ONLY | Not a pregame input | Research / future work |

## Leakage Guard Plan

1. Define a single decision timestamp for every model row.
2. Freeze all pregame inputs at or before that timestamp.
3. Store snapshot timestamps alongside every feature row.
4. Separate pregame features from result labels.
5. Reject rows that mix pre- and post-event data.
6. Record the source and version for every field.
7. Never allow closing data to masquerade as pregame truth.
8. Require a documented no-trade reason whenever timing is incomplete.

## Practical Rule

If a reviewer cannot tell when a field became known, the field is not ready to be a pregame feature.

