# Sport Specific Field Contracts

## Layer 1: Universal market fields

- `sport`
- `league`
- `event_date`
- `home_team`
- `away_team`
- `market`
- `selection`
- `odds_at_decision_time`
- `market_implied_probability`
- `bookmaker`
- `line_value`

## Layer 2: Shared sports fields

- `opening_odds`
- `closing_odds`
- `opening_line`
- `closing_line`
- `current_odds`
- `current_line`
- `snapshot_time`
- `clv`
- `player_name`
- `player_team`
- `player_prop_type`
- `player_line`
- `player_minutes`
- `player_usage`
- `recent_player_average`
- `opponent_allowed_stat`

## Layer 3: Sport-specific fields

- Full-depth sports packs: NBA, NFL, MLB, NCAAB, NCAAW, WNBA, boxing, combat sports, cricket, CS2, Dota2, esports, Formula 1, Formula E, golf, NHL, League of Legends, LPGA, MMA/UFC, NASCAR, Overwatch, PGA, soccer, tennis, Valorant.
- Thin-depth sports packs: AFL, badminton, darts, handball, IndyCar, lacrosse, MotoGP, pickleball, rugby, snooker, table tennis, volleyball, water polo.
- Fallback sports pack: `general`.

## Field contract rules

- Required fields are driven by the pack depth and by the universal market layer.
- Optional fields expand only when the source can safely support them.
- Forbidden fields are settlement / closing / leakage fields whenever a model is still in decision-time mode.
- Model and backtest compatibility must stay aligned with the canonical field catalog.
