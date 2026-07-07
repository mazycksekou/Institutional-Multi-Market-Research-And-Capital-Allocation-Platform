# NFL Feature Quality Matrix

Scores use `1` to `5`.
For cost, noise, leakage, and difficulty, higher scores mean more burden or risk.

| Feature family | Feature IDs | Predictive Value | Research Value | Backtest Value | Data Availability | Historical Depth | Maintenance Cost | Expected Stability | Noise Level | Leakage Risk | Implementation Difficulty | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| schedule_results | NFL_F001 NFL_F003 NFL_F004 | 2 | 4 | 5 | 5 | 5 | 1 | 5 | 1 | 1 | 1 | P0 |
| team_identity | NFL_F002 | 1 | 3 | 5 | 5 | 5 | 1 | 5 | 1 | 1 | 1 | P0 |
| market_odds | NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F009 NFL_F010 | 5 | 5 | 5 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | P0-P1 |
| rest_travel | NFL_F011 NFL_F012 | 3 | 4 | 4 | 4 | 4 | 2 | 4 | 2 | 1 | 2 | P0 |
| stadium_weather | NFL_F013 NFL_F014 | 3 | 4 | 4 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | P0 |
| injury_lineup | NFL_F015 NFL_F016 NFL_F017 | 5 | 5 | 4 | 2 | 2 | 4 | 2 | 4 | 5 | 4 | P0-P1 |
| roster_continuity | NFL_F018 NFL_F035 | 3 | 4 | 4 | 3 | 4 | 3 | 3 | 3 | 3 | 3 | P0 |
| team_efficiency | NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F024 NFL_F025 | 5 | 5 | 5 | 4 | 4 | 3 | 3 | 3 | 3 | 3 | P0-P2 |
| position_unit | NFL_F026 NFL_F027 NFL_F028 | 4 | 5 | 4 | 2 | 3 | 4 | 2 | 4 | 4 | 4 | P1 |
| special_teams | NFL_F029 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 3 | P1 |
| officials | NFL_F030 NFL_F031 | 2 | 4 | 3 | 2 | 3 | 3 | 3 | 4 | 3 | 3 | P1 |
| coaching_staff | NFL_F032 NFL_F033 | 3 | 4 | 4 | 3 | 3 | 3 | 4 | 2 | 2 | 3 | P0 |
| player_profile | NFL_F034 | 2 | 4 | 2 | 4 | 5 | 2 | 5 | 3 | 1 | 2 | P2 |
| deferred_player_tracking | NFL_F036 NFL_F037 NFL_F038 | 5 | 5 | 2 | 1 | 1 | 5 | 2 | 5 | 5 | 5 | DEFER |
| governance_research | NFL_F039 NFL_F040 NFL_F041 | 3 | 5 | 5 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | P1-P2 |

## Quality Takeaway

The strongest first slice remains schedule, odds snapshots, team efficiency, rest/travel, weather, coaching continuity, and leakage-safe backtest evidence.
Player tracking and player props remain high-value but deferred because the source and timing risks are not yet controlled.
