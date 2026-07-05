# Sport Streamlit Display Contract

## Sports display groups

| Field group | Label | Description | Field count |
|---|---|---|---:|
| `core_event` | Core Event Fields | Sport, league, date, home/away team | 5 |
| `line_core` | Line Core Fields | Market, selection, odds, implied probability, bookmaker, line value | 6 |
| `line_movement` | Line Movement Fields | Opening/closing odds, CLV, snapshot time | 8 |
| `settlement` | Settlement Fields | Final result, winner, scores, profit/loss | 5 |
| `team_stats` | Team Stats Fields | Home/away team statistics, pace, ratings, injuries | 7 |
| `player_stats` | Player Stats Fields | Player name, prop type, line, minutes, usage | 8 |
| `projection_control` | Projection Control Fields | Model probability, features known at decision time | 2 |

## Display contract

- `core_event` and `line_core` are the minimum display groups for every sport.
- `line_movement` and `settlement` are shown only when the data is known safely.
- `team_stats` and `player_stats` are the sports-specific display groups.
- `projection_control` is the leakage guard group and must stay decision-time only.

## Display warnings

- Never show settlement fields as model features.
- Never show closing fields as decision-time inputs.
- Do not mask missing data as if it were present.
- Use feature-control profiles to explain exclusions.
