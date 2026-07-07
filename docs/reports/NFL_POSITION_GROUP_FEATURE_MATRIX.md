# NFL Position Group Feature Matrix

This matrix maps the registry to NFL position groups.

| Position Group | Available Features | Missing Features | Future Desirable Features | Atomic Metrics | Composite Metrics | Status |
| --- | --- | --- | --- | --- | --- | --- |
| QB | NFL_F035 NFL_F028 | stable pressure and passing efficiency by QB | CPOE pressure-to-sack air yards time-to-throw | player_id snaps starter_status | pass rush pressure allowed | PARTIAL |
| RB | NFL_F035 NFL_F036 | route share and rush context | explosive rush rate receiving usage goal-line share | player_id snaps position | route participation target share | CONTRACT_ONLY |
| WR | NFL_F035 NFL_F036 | route participation and target depth | air yard share separation proxy red-zone usage | player_id snaps position | route participation target share | CONTRACT_ONLY |
| TE | NFL_F035 NFL_F036 | blocking and route role split | route share red-zone role blocking proxy | player_id snaps position | route participation target share | CONTRACT_ONLY |
| OL | NFL_F018 NFL_F026 NFL_F028 | stable line-level source | continuity pressure allowed run block index | team_id player_id snaps | offensive line score pass rush pressure allowed | PARTIAL |
| DL | NFL_F020 NFL_F027 NFL_F028 | reliable disruption fields | pressure rate run-stop rate sack conversion | team_id player_id snaps | defensive line pressure score | PARTIAL |
| LB | NFL_F020 | player-level LB source | tackle rate blitz rate coverage proxy | player_id position team | defensive matchup score | FUTURE_EXTENSION |
| CB | NFL_F020 | player-level coverage source | yards allowed per target explosive allowed | player_id position team | coverage matchup score | FUTURE_EXTENSION |
| S | NFL_F020 | player-level safety source | explosive prevention tackle role | player_id position team | secondary matchup score | FUTURE_EXTENSION |
| K | NFL_F013 NFL_F029 | kicker-specific history | kicking efficiency weather adjustment | player_id team weather | weather-adjusted kicking context | CONTRACT_ONLY |
| P | NFL_F029 | punter and coverage history | punt efficiency field position | player_id team | special teams efficiency | CONTRACT_ONLY |
| Special Teams | NFL_F029 | complete return and coverage source | hidden yards special teams EPA | team_id game_id | special teams efficiency | CONTRACT_ONLY |
| Coaches | NFL_F032 NFL_F033 | deeper scheme and coordinator tendencies | staff turnover scheme tendency fourth-down posture | coach_id team_id season | coaching continuity | PARTIAL |
| Officials | NFL_F030 NFL_F031 | stable assignment history | penalty tendency total tendency home bias | official_id game_id | official crew tendency | PARTIAL |
| Weather | NFL_F013 NFL_F014 | forecast source proof | wind impact precipitation surface impact | temp wind roof surface | weather impact score | PARTIAL |
| Medical | NFL_F015 NFL_F016 NFL_F017 | complete timestamped availability source | severity return estimate role impact | injury_status starter_status | injury adjusted availability | CONTRACT_ONLY |
| Market Context | NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F009 NFL_F010 NFL_F039 NFL_F040 | complete odds history | liquidity book consensus limits | spread total moneyline odds | movement relevance CLV calibration | PARTIAL |

## Position Group Takeaway

The first implementation should stay team/game first.
Player-position expansion becomes safer after roster, snap, depth chart, and availability lanes are validated.
