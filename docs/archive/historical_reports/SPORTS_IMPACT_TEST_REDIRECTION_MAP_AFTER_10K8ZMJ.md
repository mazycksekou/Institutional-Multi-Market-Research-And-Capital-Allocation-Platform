# Sports Impact Test Redirection Map After 10K8ZMJ

Canonical targets used in this batch:

- Sport impact and context helpers -> `src.market_intelligence.sports`
- Diagnostics compaction helpers -> `src.market_intelligence.response_compactor`

Representative redirections:

- Baseball availability, batter, bullpen, defense, pitcher, and run-value helpers -> `src.market_intelligence.sports`
- Golf approach, course-fit, strokes-gained, weather, and readiness helpers -> `src.market_intelligence.sports`
- Hockey goalie, skater, line, special-teams, transition, and readiness helpers -> `src.market_intelligence.sports`
- Soccer tactical, pressing, possession-value, lineup, referee, and readiness helpers -> `src.market_intelligence.sports`
- Combat striking, grappling, phase, durability, pace, and readiness helpers -> `src.market_intelligence.sports`
- Tennis serve, return, surface, matchup, pressure, and readiness helpers -> `src.market_intelligence.sports`
- `compact_*_impact_diagnostics_response` helpers -> `src.market_intelligence.response_compactor`
- `redact_and_limit_payload` -> `src.market_intelligence.response_compactor`

Behavioral note:
- The canonical shims resolve the legacy implementations at call time, so the tests keep their existing coverage without introducing live-trading behavior.
