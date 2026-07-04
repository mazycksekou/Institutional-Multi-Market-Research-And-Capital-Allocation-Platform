# Sport Backtest Compatibility Matrix

| Sport pack | Depth | Backtest compatibility | Notes |
|---|---|---|---|
| `basketball_nba` | full | READY | Concrete model artifact exists. |
| `basketball_ncaab` | full | READY | Full-depth sports pack. |
| `basketball_ncaaw` | full | READY | Full-depth sports pack. |
| `basketball_wnba` | full | READY | Full-depth sports pack. |
| `americanfootball_nfl` | full | READY | Full-depth sports pack. |
| `americanfootball_ncaaf` | full | READY | Full-depth sports pack. |
| `baseball_mlb` | full | READY | Full-depth sports pack. |
| `boxing` / `combat_sports` / `mma` / `ufc` / `ufc_mma` | full | READY | Combat family. |
| `cricket` / `esports` / `formula_1` / `formula_e` / `golf` / `icehockey_nhl` / `soccer` / `tennis` | full | READY | Full-depth packs exist. |
| Long-tail sports | thin | PARTIAL | Useful but narrower contracts. |
| `general` | fallback | SCAFFOLD | Catch-all only. |

## Compatibility rule

- `READY` means the field contract is rich enough to support leakage-safe backtest snapshots.
- `PARTIAL` means the lane is usable but may lack some context fields.
- `SCAFFOLD` means the lane remains a placeholder until source support improves.
