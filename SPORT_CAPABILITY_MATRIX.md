# Sport Capability Matrix

Feature-pack depth is the current implementation signal.

| Sport pack | Display name | Family | Depth | Required | Recommended | Optional | Maturity |
|---|---|---|---|---:|---:|---:|---|
| `basketball_nba` | NBA Basketball | basketball | full | 8 | 10 | 7 | COMPLETE |
| `basketball_ncaab` | NCAAB Basketball | basketball | full | 8 | 10 | 7 | COMPLETE |
| `basketball_ncaaw` | NCAAW Basketball | basketball | full | 8 | 10 | 7 | COMPLETE |
| `basketball_wnba` | WNBA Basketball | basketball | full | 8 | 10 | 7 | COMPLETE |
| `americanfootball_nfl` | NFL Football | americanfootball | full | 8 | 10 | 7 | COMPLETE |
| `americanfootball_ncaaf` | NCAAF Football | americanfootball | full | 8 | 10 | 7 | COMPLETE |
| `baseball_mlb` | MLB Baseball | baseball | full | 8 | 10 | 7 | COMPLETE |
| `boxing` | Boxing | combat | full | 7 | 8 | 6 | COMPLETE |
| `combat_sports` | Combat Sports | combat | full | 7 | 8 | 6 | COMPLETE |
| `cricket` | Cricket | cricket | full | 7 | 8 | 6 | COMPLETE |
| `cs2` / `dota2` / `league_of_legends` / `overwatch` / `valorant` / `call_of_duty` / `esports` | Esports families | esports | full | 7 | 8 | 6 | COMPLETE |
| `formula_1` / `formula_e` / `nascar` / `indycar` / `motogp` | Motorsports | motorsport | full | 7 | 8 | 6 | COMPLETE |
| `golf` / `pga` / `lpga` | Golf | golf | full | 7 | 8 | 6 | COMPLETE |
| `icehockey_nhl` | NHL Hockey | hockey | full | 8 | 10 | 7 | COMPLETE |
| `mma` / `ufc` / `ufc_mma` | MMA / UFC | combat | full | 7 | 8 | 6 | COMPLETE |
| `soccer` | Soccer | soccer | full | 8 | 10 | 7 | COMPLETE |
| `tennis` | Tennis | tennis | full | 7 | 8 | 6 | COMPLETE |
| `afl` / `badminton` / `darts` / `handball` / `lacrosse` / `pickleball` / `rugby` / `snooker` / `table_tennis` / `volleyball` / `water_polo` | Long-tail sports | mixed | thin | 5-7 | 6-8 | 4-6 | PARTIAL |
| `general` | Fallback | general | fallback | 0 | 0 | 0 | SCAFFOLD |

## Interpretation

- `full` depth means the repo has a rich, usable contract for the sport family.
- `thin` depth means the repo has a usable but narrow contract.
- `fallback` depth means the repo has a scaffold / catch-all contract only.
