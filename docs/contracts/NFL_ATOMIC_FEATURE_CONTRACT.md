# NFL Atomic Feature Contract

Atomic features are direct fields that do not require multiple source inputs to define their canonical meaning.

## Atomic Feature Contract Fields

Each atomic feature must define:

- `canonical_name`
- `raw_source_field`
- `datatype`
- `unit`
- `allowed_positions`
- `allowed_markets`
- `required_for_backtest`
- `optional_for_backtest`
- `streamlit_display_group`
- `model_usage`
- `leakage_risk`

## Canonical Atomic Feature Examples

| canonical_name | raw_source_field | datatype | unit | allowed_positions | allowed_markets | required_for_backtest | optional_for_backtest | streamlit_display_group | model_usage | leakage_risk |
|---|---|---|---|---|---|---|---|---|---|---|
| `player_id` | `player_id` | string | id | all | all | yes | yes | player identity | join key | low |
| `player_name` | `player_name` | string | text | all | all | yes | yes | player identity | display / join aid | low |
| `team` | `team` | string | text | all | all | yes | yes | team identity | grouping | low |
| `position` | `position` | string | enum | player positions | player markets | yes | yes | player profile | model conditioning | low |
| `game_id` | `game_id` | string | id | all | all | yes | yes | game identity | join key | low |
| `season` | `season` | integer | season | all | all | yes | yes | schedule context | partitioning | low |
| `week` | `week` | integer | week | all | all | yes | yes | schedule context | partitioning | low |
| `starter_status` | `starter_status` | string / bool | state | player roles | player markets | no | yes | availability | availability logic | medium |
| `snap_count` | `snap_count` | integer | snaps | player roles | player / team markets | yes | yes | participation | usage model input | medium |
| `injury_status` | `injury_status` | string | status | all players | player markets | no | yes | availability | risk modifier | high |
| `practice_status` | `practice_status` | string | status | all players | player markets | no | yes | availability | risk modifier | medium |
| `official_name` | `official_name` | string | text | officials | game markets | no | yes | officiating | context only | low |
| `temp` | `temp` | number | fahrenheit / celsius | all | totals / passing / kicking | no | yes | weather | weather modifier | medium |
| `wind` | `wind` | number | mph / kph | all | totals / passing / kicking | no | yes | weather | weather modifier | medium |
| `roof` | `roof` | string | enum | all | totals / passing / kicking | no | yes | weather | weather modifier | low |
| `spread_line` | `spread_line` | number | points | all | spread | yes | yes | market quotes | pricing input | low |
| `total_line` | `total_line` | number | points | all | total | yes | yes | market quotes | pricing input | low |
| `odds_at_decision_time` | `odds_at_decision_time` | number | price | all | all priced markets | yes | yes | market quotes | pricing input | low |

## Atomic Feature Policy

- atomic features should map directly to source or canonical normalized records
- atomic features should not hide a derived calculation
- atomic features should have stable naming across sports where possible
- atomic features should be cheap to add to the future NFL slice

