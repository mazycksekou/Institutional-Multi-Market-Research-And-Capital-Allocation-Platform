# Phase 10G2 Sport Profile Owner Review

Generated: 2026-06-12T20:55:51
- HEAD: `b6c782b`
- Git clean at review start: `False`

```text
?? PHASE10G2_EXISTING_SPORT_REGRESSION_WIRING_AUDIT.md
```

## `automation_scheduler/data_availability_tiers.py`

### Assignments
- line `15`: `DATA_AVAILABILITY_SCHEMA_VERSION`
- line `17`: `TIER_NAMES`
- line `25`: `GLOBAL_TIER_FIELDS`
- line `33`: `BASE_CONFIDENCE_CAPS`
- line `35`: `RECOMMENDED_USE_BY_LEVEL`
- line `44`: `FREE_NEXT_ACTION_BY_LEVEL`
- line `53`: `DEFAULT_DERIVED_FEATURES`
- line `85`: `tiers`
- line `110`: `BASKETBALL_T0`
- line `111`: `BASKETBALL_T1`
- line `112`: `BASKETBALL_T2`
- line `113`: `BASKETBALL_T3`
- line `114`: `BASKETBALL_T4`
- line `116`: `FOOTBALL_T1`
- line `117`: `FOOTBALL_T2`
- line `118`: `FOOTBALL_T3`
- line `119`: `FOOTBALL_T4`
- line `141`: `MODULE_PROFILE_ALIASES`
- line `182`: `FIELD_EXPANSIONS`
- line `220`: `COVERAGE_FIELD_EXPANSIONS`
- line `251`: `key`
- line `256`: `key`
- line `263`: `key`
- line `272`: `mapping`
- line `284`: `sources`
- line `301`: `tier_fields`
- line `308`: `critical`
- line `311`: `current`
- line `314`: `current`
- line `319`: `rules`
- line `320`: `critical_missing`
- line `323`: `cap`
- line `324`: `missing_advanced`
- line `325`: `missing_context`
- line `326`: `reason`
- line `328`: `cap`
- line `329`: `reason`
- line `331`: `cap`
- line `333`: `reason`
- line `344`: `profile`
- line `345`: `fields`
- line `346`: `derived`
- line `347`: `tier_fields`
- line `348`: `present`
- line `349`: `missing`
- line `350`: `current_level`
- line `380`: `profile`
- line `381`: `fields`
- line `382`: `derived`
- line `383`: `current`
- line `384`: `all_fields`
- line `385`: `missing_critical`
- line `386`: `missing_advanced`
- line `387`: `missing_context`
- line `389`: `tier_name`
- line `390`: `supported`
- line `391`: `unsupported`
- line `393`: `reliability`
- line `395`: `reliability`
- line `397`: `reliability`
- line `399`: `reliability`
- line `401`: `reliability`
- line `403`: `reliability`
- line `447`: `availability`
- line `463`: `module`
- line `464`: `fields`
- line `465`: `availability`
- line `466`: `profile`
- line `467`: `planner`
- line `497`: `lanes`
- line `499`: `needle`
- line `500`: `lanes`
- line `506`: `modules`
- line `507`: `enabled_sources`
- line `511`: `paid_enabled`
- line `548`: `base`
- line `549`: `path`
- line `555`: `root`
- line `564`: `tmp`
- line `571`: `tmp`
- line `577`: `lines`
- line `599`: `root`
- line `600`: `created`
- line `601`: `day`
- line `602`: `run_id`
- line `603`: `latest`
- line `604`: `item`
- line `605`: `daily_json`
- line `606`: `daily_md`
- line `607`: `payload`
- line `621`: `parser`
- line `624`: `args`
- line `627`: `report`

### Functions
- line `72`: `_profile`
- line `246`: `utc_now_iso`
- line `250`: `resolve_profile_key`
- line `255`: `get_tier_profile`
- line `260`: `_expand_fields`
- line `271`: `fields_from_source`
- line `282`: `fields_from_lane`
- line `293`: `_profile_all_fields`
- line `300`: `_has_tier_signal`
- line `307`: `_current_level`
- line `318`: `_confidence_for`
- line `337`: `assess_tier`
- line `374`: `evaluate_data_availability`
- line `441`: `build_prediction_calibration_metadata`
- line `462`: `_module_row`
- line `496`: `build_data_availability_report`
- line `547`: `_root`
- line `554`: `_rel`
- line `562`: `_atomic_write_json`
- line `569`: `_atomic_write_text`
- line `576`: `render_data_availability_markdown`
- line `598`: `write_data_availability_report`
- line `620`: `main`

### Classes

### Sport/Profile Keyword Lines
- line `15`: `DATA_AVAILABILITY_SCHEMA_VERSION = "data_availability_tiers_v1"`
- line `17`: `TIER_NAMES = {`
- line `18`: `0: "TIER_0_OUTCOME_BACKFILL",`
- line `19`: `1: "TIER_1_BASIC_FORM",`
- line `20`: `2: "TIER_2_MARKET_AWARE",`
- line `21`: `3: "TIER_3_ADVANCED_STATS",`
- line `22`: `4: "TIER_4_CONTEXT",`
- line `25`: `GLOBAL_TIER_FIELDS = {`
- line `28`: `2: ["odds", "spread", "total", "moneyline", "implied_probability", "prediction_market_price", "line_movement", "market_liquidity"],`
- line `36`: `-1: "blocked_until_tier_0_critical_fields_exist",`
- line `37`: `0: "outcome_backfill_and_tier_0_calibration_only",`
- line `38`: `1: "baseline_training_and_tier_1_calibration",`
- line `39`: `2: "market_aware_review_and_tier_2_calibration",`
- line `40`: `3: "advanced_stats_review_with_tier_3_calibration",`
- line `41`: `4: "context_aware_review_with_tier_4_calibration",`
- line `46`: `0: "derive Tier 1 rolling form from existing schedule/results history",`
- line `47`: `1: "no-call audit for existing market, odds, or prediction-market fields",`
- line `50`: `4: "continue tier-separated calibration and backfill from existing data",`
- line `67`: `"market_implied_probability",`
- line `68`: `"prediction_market_outcome",`
- line `72`: `def _profile(`
- line `76`: `tier0: list[str],`
- line `77`: `tier1: list[str],`
- line `78`: `tier2: list[str],`
- line `79`: `tier3: list[str],`
- line `80`: `tier4: list[str],`
- line `85`: `tiers = {0: tier0, 1: tier1, 2: tier2, 3: tier3, 4: tier4}`
- line `89`: `"tiers": tiers,`
- line `90`: `"critical_fields": list(critical or tier0),`
- line `92`: `"missing_critical_tier_0_cap": 0.0,`
- line `93`: `"tier_0_cap": BASE_CONFIDENCE_CAPS[0],`
- line `94`: `"tier_1_cap": BASE_CONFIDENCE_CAPS[1],`
- line `95`: `"tier_2_cap": BASE_CONFIDENCE_CAPS[2],`
- line `96`: `"tier_3_cap": BASE_CONFIDENCE_CAPS[3],`
- line `97`: `"tier_4_cap": BASE_CONFIDENCE_CAPS[4],`
- line `102`: `level: f"{module}.{TIER_NAMES[level].lower()}"`
- line `106`: `"never_fabricate_fields": sorted(set(never_fabricate or []) | set(tier3) | set(tier4)),`
- line `112`: `BASKETBALL_T2 = ["spread", "total", "moneyline", "implied_probability", "market_price", "line_movement", "market_liquidity"]`
- line `117`: `FOOTBALL_T2 = ["spread", "total", "moneyline", "implied_probability", "market_price", "line_movement", "market_liquidity"]`
- line `121`: `SPORT_PROFILES: dict[str, dict[str, Any]] = {`
- line `122`: `"basketball_nba": _profile(module="basketball_nba", display_name="NBA", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),`
- line `123`: `"basketball_wnba": _profile(module="basketball_wnba", display_name="WNBA", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),`
- line `124`: `"basketball_ncaab": _profile(module="basketball_ncaab", display_name="NCAAB", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),`
- line `125`: `"basketball_ncaaw": _profile(module="basketball_ncaaw", display_name="NCAAW", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),`
- line `126`: `"americanfootball_nfl": _profile(module="americanfootball_nfl", display_name="NFL", tier0=["teams", "game_id", "season", "week", "home_away", "final_score", "final_result"], tier1=FOOTBALL_T1, tier2=FOOTBALL_T2, tier3=FOOTBALL_T3, tier4=FOOTBALL_T4),`
- line `127`: `"americanfootball_ncaaf": _profile(module="americanfootball_ncaaf", display_name="NCAAF", tier0=["teams", "game_id", "season", "week", "home_away", "final_score", "final_result"], tier1=FOOTBALL_T1, tier2=FOOTBALL_T2, tier3=FOOTBALL_T3, tier4=FOOTBALL_T4, never_fabricate=["epa", "success_rate", "explosiveness", "havoc", "qb_status"]),`
- line `128`: `"baseball_mlb": _profile(module="baseball_mlb", display_name="MLB", tier0=["teams", "game_id", "event_date", "starter", "final_score", "final_result"], tier1=["rolling_runs_for", "rolling_runs_against", "rolling_margin", "team_form", "bullpen_usage_proxy", "home_away_split", "park_factor", "rest_days"], tier2=["moneyline", "run_line", "total", "implied_probability", "market_price", "line_movement"], tier3=["pitch_values", "run_value", "xwoba", "barrel_rate", "advanced_pitcher_metrics", "advanced_batter_metrics"], tier4=["lineup_confirmation", "umpire", "weather", "injuries", "travel", "news"], critical=["teams", "game_id", "event_date", "final_score", "final_result"]),`
- line `129`: `"icehockey_nhl": _profile(module="icehockey_nhl", display_name="NHL", tier0=["teams", "game_id", "event_date", "home_away", "final_score", "final_result"], tier1=["rolling_goals_for", "rolling_goals_against", "rolling_margin", "rolling_win_rate", "home_away_split", "rest_days", "simple_team_rating"], tier2=["moneyline", "puck_line", "total", "implied_probability", "market_price"], tier3=["xg", "xga", "shot_quality", "possession_metrics", "special_teams_metrics", "goalie_metrics"], tier4=["injuries", "goalie_confirmation", "lineups", "officials", "travel", "news"]),`
- line `130`: `"soccer": _profile(module="soccer", display_name="Soccer", tier0=["teams", "match_id", "event_date", "home_away", "final_score", "final_result"], tier1=["rolling_goals_for", "rolling_goals_against", "form", "home_away_split", "rest_days", "simple_team_rating", "sos_proxy"], tier2=["three_way_odds", "asian_handicap", "total", "implied_probability", "market_price"], tier3=["xg", "xga", "shot_quality", "pressing_metrics", "possession_metrics"], tier4=["lineups", "injuries", "weather", "referee", "travel", "news"], critical=["teams", "match_id", "event_date", "final_score", "final_result"]),`
- line `131`: `"tennis": _profile(module="tennis", display_name="Tennis", tier0=["players", "match_id", "event_date", "surface", "final_score", "final_result"], tier1=["rolling_sets_won", "rolling_games_won", "player_form", "surface_form", "rest_days", "simple_player_rating", "volatility"], tier2=["moneyline", "game_spread", "total_games", "implied_probability", "market_price"], tier3=["serve_metrics", "return_metrics", "hold_rate", "break_rate", "point_win_rate", "rally_metrics"], tier4=["injury_status", "travel", "draw_context", "weather", "news"], critical=["players", "match_id", "event_date", "final_result"]),`
- line `132`: `"golf": _profile(module="golf", display_name="Golf", tier0=["players", "tournament_id", "event_date", "course", "finish_position", "final_result"], tier1=["recent_finishes", "scoring_average", "field_strength", "course_history", "simple_player_rating", "volatility"], tier2=["outright_odds", "placement_odds", "matchup_odds", "implied_probability", "market_price"], tier3=["strokes_gained", "approach_metrics", "putting_metrics", "driving_metrics", "around_green_metrics"], tier4=["weather", "tee_time", "injury_status", "travel", "news"], critical=["players", "tournament_id", "event_date", "finish_position"]),`
- line `133`: `"combat_sports": _profile(module="combat_sports", display_name="Combat Sports", tier0=["fighters", "fight_id", "event_date", "weight_class", "final_result", "method"], tier1=["record", "recent_form", "finish_rate", "age", "reach", "layoff_days", "simple_fighter_rating"], tier2=["moneyline", "method_odds", "round_total", "implied_probability", "market_price"], tier3=["striking_metrics", "grappling_metrics", "takedown_metrics", "control_time", "pace_metrics"], tier4=["injury_status", "camp_context", "weigh_in", "travel", "news"], critical=["fighters", "fight_id", "event_date", "final_result"]),`
- line `134`: `"prediction_market": _profile(module="prediction_market", display_name="Prediction Markets", tier0=["ticker", "market_id", "close_time", "settlement_result", "final_result"], tier1=["category_base_rate", "historical_market_price", "time_to_close", "volatility", "simple_market_rating"], tier2=["bid_ask", "market_price", "implied_probability", "volume", "open_interest", "market_liquidity"], tier3=["order_book_depth", "spread_quality", "liquidity_microstructure", "settlement_history"], tier4=["settlement_rules", "event_news", "market_context", "operational_context"], critical=["ticker", "settlement_result"]),`
- line `135`: `"stock": _profile(module="stock", display_name="Stocks", tier0=["symbol", "date", "close_price", "return"], tier1=["rolling_return", "volatility", "drawdown", "volume", "trend"], tier2=["market_benchmark", "sector_benchmark", "rates_context", "macro_context"], tier3=["fundamentals", "filings", "earnings", "revisions", "valuation"], tier4=["news", "insider_context", "institutional_context", "macro_regime"], critical=["symbol", "date", "close_price"]),`
- line `136`: `"crypto": _profile(module="crypto", display_name="Crypto", tier0=["symbol", "timestamp", "price", "return"], tier1=["rolling_return", "volatility", "volume", "drawdown", "trend"], tier2=["order_book", "spread", "liquidity", "funding", "open_interest"], tier3=["onchain", "dex_liquidity", "stablecoin_flows", "gas", "defi_context"], tier4=["news", "security_context", "regulatory_context", "macro_context"], critical=["symbol", "timestamp", "price"]),`
- line `137`: `"sportsbook": _profile(module="sportsbook", display_name="Sportsbook", tier0=["event_id", "teams", "event_date", "market_type", "selection", "final_result"], tier1=["basic_form", "home_away_split", "rest_days", "simple_team_rating"], tier2=["odds", "line", "spread", "total", "moneyline", "implied_probability", "book_count"], tier3=["consensus_line", "closing_line", "line_movement", "limit_context", "market_liquidity"], tier4=["injuries", "weather", "lineups", "news"], critical=["event_id", "market_type", "selection"]),`
- line `138`: `"context_module": _profile(module="context_module", display_name="Context Module", tier0=["timestamp", "source_context", "stable_join_key"], tier1=["coverage_history", "source_reliability", "cadence", "join_quality"], tier2=["entity_linkage", "market_linkage"], tier3=["normalized_context_metric"], tier4=["weather", "injury_status", "lineups", "officials", "news", "macro_context", "security_context", "travel"], critical=["timestamp"]),`
- line `141`: `MODULE_PROFILE_ALIASES = {`
- line `154`: `"prediction_markets": "prediction_market",`
- line `155`: `"kalshi": "prediction_market",`
- line `156`: `"polymarket": "prediction_market",`
- line `184`: `"stable_event_id": {"stable_event_id", "event_id", "game_id", "match_id", "fight_id", "tournament_id", "market_id"},`
- line `204`: `"bid_ask": {"bid_ask", "market_price", "implied_probability", "spread", "market_liquidity"},`
- line `207`: `"volume": {"volume", "market_liquidity"},`
- line `250`: `def resolve_profile_key(module: str | None) -> str:`
- line `252`: `return MODULE_PROFILE_ALIASES.get(key, MODULE_PROFILE_ALIASES.get(key.lower(), key))`
- line `255`: `def get_tier_profile(module: str | None) -> dict[str, Any]:`
- line `256`: `key = resolve_profile_key(module)`
- line `257`: `return SPORT_PROFILES.get(key) or SPORT_PROFILES["context_module"]`
- line `272`: `mapping = dict(source.get("model_mapping") or {})`
- line `274`: `for key in ("model_inputs_supported", "outcome_fields_available", "historical_backfill_fields_available", "join_keys"):`
- line `293`: `def _profile_all_fields(profile: dict[str, Any]) -> set[str]:`
- line `295`: `for tier_fields in dict(profile.get("tiers") or {}).values():`
- line `296`: `fields.update(tier_fields)`
- line `300`: `def _has_tier_signal(level: int, profile: dict[str, Any], fields: set[str], derived_fields: set[str]) -> bool:`
- line `301`: `tier_fields = set(profile["tiers"][level])`
- line `303`: `return set(profile["critical_fields"]).issubset(fields | derived_fields)`
- line `304`: `return bool(tier_fields & (fields | derived_fields))`
- line `307`: `def _current_level(profile: dict[str, Any], fields: set[str], derived_fields: set[str]) -> int:`
- line `308`: `critical = set(profile["critical_fields"])`
- line `313`: `if _has_tier_signal(level, profile, fields, derived_fields):`
- line `318`: `def _confidence_for(level: int, profile: dict[str, Any], fields: set[str], derived_fields: set[str]) -> tuple[float, str]:`
- line `319`: `rules = dict(profile.get("confidence_cap_rules") or {})`
- line `320`: `critical_missing = sorted(set(profile["critical_fields"]) - (fields | derived_fields))`
- line `322`: `return 0.0, "missing_critical_tier_0_fields"`
- line `323`: `cap = float(rules.get(f"tier_{level}_cap", BASE_CONFIDENCE_CAPS.get(level, 0.0)))`
- line `324`: `missing_advanced = sorted(set(profile["tiers"][3]) - (fields | derived_fields))`
- line `325`: `missing_context = sorted(set(profile["tiers"][4]) - (fields | derived_fields))`
- line `326`: `reason = f"{TIER_NAMES[level].lower()}_cap"`
- line `332`: `if reason == f"{TIER_NAMES[level].lower()}_cap":`
- line `337`: `def assess_tier(`
- line `340`: `tier_level: int,`
- line `344`: `profile = get_tier_profile(module)`
- line `347`: `tier_fields = set(profile["tiers"][tier_level])`
- line `348`: `present = sorted(tier_fields & (fields | derived))`
- line `349`: `missing = sorted(tier_fields - (fields | derived))`
- line `350`: `current_level = _current_level(profile, fields, derived)`
- line `351`: `cap, cap_reason = _confidence_for(min(max(current_level, 0), 4), profile, fields, derived) if current_level >= 0 else (0.0, "missing_critical_tier_0_fields")`
- line `353`: `"tier_name": TIER_NAMES[tier_level],`
- line `354`: `"tier_level": tier_level,`
- line `357`: `"derived_fields": sorted(tier_fields & derived),`
- line `358`: `"unavailable_not_fabricated_fields": sorted(set(profile["never_fabricate_fields"]) & set(missing)),`
- line `359`: `"calibration_bucket": profile["calibration_buckets"][tier_level],`
- line `365`: `"can_support_review": current_level >= min(tier_level, 1),`
- line `366`: `"can_support_confirmed_bet": bool(current_level >= 4 and tier_level >= 4),`
- line `367`: `"recommended_use": RECOMMENDED_USE_BY_LEVEL[tier_level],`
- line `368`: `"recommended_next_free_layer": FREE_NEXT_ACTION_BY_LEVEL.get(min(tier_level, 4)),`
- line `380`: `profile = get_tier_profile(module)`
- line `383`: `current = _current_level(profile, fields, derived)`
- line `384`: `all_fields = _profile_all_fields(profile)`
- line `385`: `missing_critical = sorted(set(profile["critical_fields"]) - (fields | derived))`
- line `386`: `missing_advanced = sorted(set(profile["tiers"][3]) - (fields | derived))`
- line `387`: `missing_context = sorted(set(profile["tiers"][4]) - (fields | derived))`
- line `388`: `cap, cap_reason = _confidence_for(current, profile, fields, derived) if current >= 0 else (0.0, "missing_critical_tier_0_fields")`
- line `389`: `tier_name = TIER_NAMES.get(current, "INSUFFICIENT_TIER_0")`
- line `390`: `supported = [TIER_NAMES[level] for level in range(0, current + 1)] if current >= 0 else []`
- line `391`: `unsupported = [TIER_NAMES[level] for level in range(max(current + 1, 0), 5)]`
- line `393`: `reliability = "blocked_missing_tier_0"`
- line `395`: `reliability = "low_tier_0_only"`
- line `399`: `reliability = "market_aware_partial"`

## `automation_scheduler/multi_sport_model_registry.py`
- missing

## `tests/test_data_availability_tiers.py`

### Assignments
- line `16`: `NCAAF_T0`
- line `43`: `result`
- line `49`: `tier1`
- line `50`: `tier2`
- line `51`: `tier3`
- line `52`: `tier4`
- line `61`: `result`
- line `65`: `tier3`
- line `71`: `result`
- line `78`: `metadata`
- line `95`: `report`
- line `96`: `paths`
- line `97`: `payload_text`
- line `99`: `modules`

### Functions
- line `20`: `test_required_profiles_exist`
- line `42`: `test_tier_0_assigned_when_only_results_and_schedule_exist`
- line `48`: `test_higher_tiers_are_assigned_by_available_layer`
- line `60`: `test_missing_advanced_is_reported_not_fabricated_and_does_not_block_basic`
- line `70`: `test_missing_critical_tier_0_blocks_calibration`
- line `77`: `test_prediction_metadata_shape`
- line `93`: `test_global_report_is_compact_safe_and_persists_expected_paths`

### Classes
- line `19`: `TestDataAvailabilityTiers`

### Sport/Profile Keyword Lines
- line `5`: `from automation_scheduler.data_availability_tiers import (`
- line `6`: `SPORT_PROFILES,`
- line `10`: `get_tier_profile,`
- line `19`: `class TestDataAvailabilityTiers(unittest.TestCase):`
- line `20`: `def test_required_profiles_exist(self):`
- line `34`: `"prediction_market",`
- line `39`: `self.assertIn(module, SPORT_PROFILES)`
- line `40`: `self.assertEqual(get_tier_profile(module)["module"], module)`
- line `42`: `def test_tier_0_assigned_when_only_results_and_schedule_exist(self):`
- line `44`: `self.assertEqual(result["data_availability_tier"], "TIER_0_OUTCOME_BACKFILL")`
- line `48`: `def test_higher_tiers_are_assigned_by_available_layer(self):`
- line `49`: `tier1 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin"])`
- line `50`: `tier2 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin", "spread"])`
- line `51`: `tier3 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin", "spread", "epa"])`
- line `52`: `tier4 = evaluate_data_availability(module="americanfootball_ncaaf", available_fields=NCAAF_T0 + ["rolling_margin", "spread", "epa", "injuries"])`
- line `54`: `self.assertEqual(tier1["data_availability_tier"], "TIER_1_BASIC_FORM")`
- line `55`: `self.assertEqual(tier2["data_availability_tier"], "TIER_2_MARKET_AWARE")`
- line `56`: `self.assertEqual(tier3["data_availability_tier"], "TIER_3_ADVANCED_STATS")`
- line `57`: `self.assertEqual(tier4["data_availability_tier"], "TIER_4_CONTEXT")`
- line `58`: `self.assertNotEqual(tier1["calibration_bucket"], tier3["calibration_bucket"])`
- line `62`: `self.assertEqual(result["data_availability_tier"], "TIER_1_BASIC_FORM")`
- line `65`: `tier3 = result["tier_assessments"][3]`
- line `66`: `self.assertIn("epa", tier3["unavailable_not_fabricated_fields"])`
- line `70`: `def test_missing_critical_tier_0_blocks_calibration(self):`
- line `72`: `self.assertEqual(result["data_availability_tier"], "INSUFFICIENT_TIER_0")`
- line `80`: `"data_availability_tier",`

## `tests/test_sport_model_routing.py`

### Assignments
- line `9`: `config`
- line `37`: `expected`
- line `274`: `hockey`
- line `311`: `config`
- line `312`: `module`
- line `320`: `nba`
- line `321`: `wnba`
- line `327`: `components`
- line `338`: `config`
- line `359`: `response`
- line `365`: `samples`
- line `399`: `response`
- line `405`: `analysis`
- line `413`: `response`
- line `419`: `response`
- line `438`: `input_stats`
- line `465`: `response`
- line `481`: `response`
- line `519`: `response`

### Functions
- line `7`: `test_all_15_official_sports_route`
- line `31`: `test_esports_and_egaming_alias_route_to_esports`
- line `36`: `test_common_sport_aliases_route_to_internal_keys`
- line `261`: `test_nba_and_mlb_aliases_route`
- line `265`: `test_primary_model_type_constraints`
- line `273`: `test_sport_specific_component_requirements`
- line `309`: `test_every_sport_uses_shared_officials_module_with_specific_type`
- line `319`: `test_wnba_uses_wnba_specific_parameters_not_nba_copy`
- line `326`: `test_architecture_components_registered`
- line `336`: `test_every_sport_has_social_crowd_calibration_requirements`
- line `358`: `test_manual_ticket_and_provider_foundation_do_not_place_bets`
- line `364`: `test_officiating_analysis_returns_clean_status_for_representative_sports`
- line `411`: `test_missing_officiating_inputs_do_not_create_500`
- line `418`: `test_officiating_data_cannot_create_bet_by_itself`
- line `437`: `test_active_nba_officiating_adjustment_is_reported_without_overriding_decision`
- line `480`: `test_officiating_does_not_break_confirmed_no_bet_mutual_exclusion`
- line `518`: `test_unsupported_sport_returns_safe_no_bet_response`

### Classes
- line `6`: `TestSportModelRouting`

### Sport/Profile Keyword Lines
- line `3`: `import multi_sport_model_registry as registry`
- line `6`: `class TestSportModelRouting(unittest.TestCase):`
- line `9`: `config = registry.get_sport_model_config(sport)`
- line `14`: `"model_used",`
- line `15`: `"model_family",`
- line `16`: `"primary_model_type",`
- line `17`: `"supported_markets",`
- line `21`: `"model_components",`
- line `32`: `self.assertEqual(registry.get_sport_model_config("esports")["sport"], "esports")`
- line `33`: `self.assertEqual(registry.get_sport_model_config("egaming")["sport"], "esports")`
- line `259`: `self.assertEqual(registry.get_sport_model_config(alias)["sport"], sport_key)`
- line `262`: `self.assertEqual(registry.get_sport_model_config("nba")["sport"], "basketball_nba")`
- line `263`: `self.assertEqual(registry.get_sport_model_config("mlb")["sport"], "baseball_mlb")`
- line `265`: `def test_primary_model_type_constraints(self):`
- line `267`: `self.assertNotEqual(registry.get_sport_model_config(sport)["primary_model_type"], "poisson")`
- line `268`: `self.assertIn("Negative Binomial", registry.get_sport_model_config("baseball_mlb")["model_family"])`
- line `269`: `self.assertIn("Poisson", registry.get_sport_model_config("soccer")["model_family"])`
- line `270`: `self.assertIn("Dixon Coles", " ".join(registry.get_sport_model_config("soccer")["model_components"]))`
- line `271`: `self.assertIn("Bivariate Poisson", " ".join(registry.get_sport_model_config("soccer")["model_components"]))`
- line `273`: `def test_sport_specific_component_requirements(self):`
- line `274`: `hockey = registry.get_sport_model_config("icehockey_nhl")`
- line `275`: `self.assertIn("goalie adjustment", hockey["model_components"])`
- line `276`: `self.assertIn("special teams adjustment", hockey["model_components"])`
- line `277`: `self.assertEqual(registry.get_sport_model_config("tennis")["primary_model_type"], "point_game_set_simulation")`
- line `278`: `self.assertEqual(registry.get_sport_model_config("mma_mixed_martial_arts")["model_family"], "fighter_striking_grappling_finish_model")`
- line `279`: `self.assertEqual(registry.get_sport_model_config("boxing")["model_family"], "fighter_striking_grappling_finish_model")`
- line `280`: `self.assertEqual(registry.get_sport_model_config("golf")["model_family"], "strokes_gained_course_fit_monte_carlo_model")`
- line `281`: `self.assertEqual(registry.get_sport_model_config("basketball_wnba")["model_family"], "wnba_possession_rating_monte_carlo_model")`
- line `282`: `self.assertEqual(registry.get_sport_model_config("basketball_ncaab")["model_family"], "mens_college_basketball_possession_variance_model")`
- line `283`: `self.assertEqual(registry.get_sport_model_config("basketball_ncaawb")["model_family"], "womens_college_basketball_possession_variance_model")`
- line `284`: `self.assertEqual(registry.get_sport_model_config("americanfootball_ncaaf")["model_family"], "college_football_epa_drive_rating_monte_carlo_model")`
- line `285`: `self.assertEqual(registry.get_sport_model_config("rugby")["model_family"], "rugby_set_piece_territory_expected_points_monte_carlo_model")`
- line `286`: `self.assertEqual(registry.get_sport_model_config("lacrosse")["model_family"], "lacrosse_faceoff_possession_shot_quality_monte_carlo_model")`
- line `287`: `self.assertEqual(registry.get_sport_model_config("table_tennis")["model_family"], "table_tennis_serve_return_rally_momentum_monte_carlo_model")`
- line `288`: `self.assertEqual(registry.get_sport_model_config("badminton")["model_family"], "badminton_serve_return_rally_momentum_shuttle_monte_carlo_model")`
- line `289`: `self.assertEqual(registry.get_sport_model_config("pickleball")["model_family"], "pickleball_dink_kitchen_serve_return_monte_carlo_model")`
- line `290`: `self.assertEqual(registry.get_sport_model_config("snooker")["model_family"], "snooker_frame_break_safety_potting_monte_carlo_model")`
- line `291`: `self.assertEqual(registry.get_sport_model_config("volleyball")["model_family"], "volleyball_sideout_attack_block_serve_monte_carlo_model")`
- line `292`: `self.assertEqual(registry.get_sport_model_config("handball")["model_family"], "handball_fastbreak_goalkeeper_efficiency_monte_carlo_model")`
- line `293`: `self.assertEqual(registry.get_sport_model_config("water_polo")["model_family"], "water_polo_goalkeeper_power_play_shot_quality_monte_carlo_model")`
- line `294`: `self.assertEqual(registry.get_sport_model_config("afl")["model_family"], "afl_clearance_inside50_scoring_shot_monte_carlo_model")`
- line `295`: `self.assertEqual(registry.get_sport_model_config("formula1")["model_family"], "f1_qualifying_race_pace_pit_strategy_monte_carlo_model")`
- line `296`: `self.assertEqual(registry.get_sport_model_config("formula_e")["model_family"], "formula_e_energy_management_attack_mode_street_circuit_monte_carlo_model")`
- line `297`: `self.assertEqual(registry.get_sport_model_config("nascar")["model_family"], "nascar_track_position_speed_rating_pit_variance_monte_carlo_model")`
- line `298`: `self.assertEqual(registry.get_sport_model_config("indycar")["model_family"], "indycar_aero_strategy_restart_pit_variance_monte_carlo_model")`
- line `299`: `self.assertEqual(registry.get_sport_model_config("motogp")["model_family"], "motogp_rider_bike_tire_weather_monte_carlo_model")`
- line `300`: `self.assertEqual(registry.get_sport_model_config("cricket")["model_family"], "cricket_run_rate_wicket_resource_monte_carlo_model")`
- line `301`: `self.assertEqual(registry.get_sport_model_config("cs2")["model_family"], "cs2_round_economy_map_pool_monte_carlo_model")`
- line `302`: `self.assertEqual(registry.get_sport_model_config("valorant")["model_family"], "valorant_agent_composition_economy_map_pool_monte_carlo_model")`
- line `303`: `self.assertEqual(registry.get_sport_model_config("league_of_legends")["model_family"], "league_of_legends_draft_objective_gold_monte_carlo_model")`
- line `304`: `self.assertEqual(registry.get_sport_model_config("dota2")["model_family"], "dota2_draft_lane_objective_roshan_monte_carlo_model")`
- line `305`: `self.assertEqual(registry.get_sport_model_config("call_of_duty")["model_family"], "call_of_duty_map_mode_rotation_respawn_snd_monte_carlo_model")`
- line `306`: `self.assertEqual(registry.get_sport_model_config("overwatch")["model_family"], "overwatch_hero_composition_map_mode_objective_monte_carlo_model")`
- line `307`: `self.assertIn("game title routing placeholder", registry.get_sport_model_config("esports")["model_components"])`
- line `311`: `config = registry.get_sport_model_config(sport)`
- line `314`: `self.assertIn("officials_context_module", config["model_components"])`
- line `320`: `nba = registry.get_sport_model_config("basketball_nba")`
- line `321`: `wnba = registry.get_sport_model_config("basketball_wnba")`
- line `328`: `self.assertIn("wee_willie_market_weakness_detector", components)`
- line `338`: `config = registry.get_sport_model_config(sport)`
- line `339`: `for component in registry.SOCIAL_CROWD_MODEL_COMPONENTS:`
- line `340`: `self.assertIn(component, config["model_components"])`
- line `349`: `"market narrative check",`
- line `351`: `"sentiment versus model probability comparison",`
- line `352`: `"crowd consensus versus sharp market comparison",`
- line `359`: `response = registry.analyze_sport_model({"sport": "basketball_nba", "market": "moneyline"})`
- line `380`: `"mma_mixed_martial_arts": {"referee": "Ref A", "judge_panel": "Panel A", "decision_scoring_profile": 0.5},`
- line `381`: `"boxing": {"referee": "Ref A", "judge_panel": "Panel A", "decision_scoring_profile": 0.5},`
- line `399`: `response = registry.analyze_sport_model({`
- line `401`: `"market": "moneyline",`
- line `406`: `self.assertIn(analysis["officiating_module_status"], {"inactive_base_model", "no_adjustment", "active_no_adjustment", "active_adjustment"})`
- line `413`: `response = registry.analyze_sport_model({"sport": sport, "market": "moneyline", "input_stats": {}})`
- line `415`: `self.assertIn(response["officiating_module_status"], {"inactive_base_model", "no_adjustment"})`
- line `419`: `response = registry.analyze_sport_model({`
- line `421`: `"market": "moneyline",`
- line `432`: `self.assertEqual(response["officiating_module_status"], "inactive_base_model")`
- line `435`: `self.assertIn("base model inactive", response["officiating_no_bet_reason"])`
- line `465`: `response = registry.analyze_sport_model({`
- line `468`: `"market": "moneyline",`
- line `481`: `response = registry.analyze_sport_model({`
- line `484`: `"market": "moneyline",`
- line `519`: `response = registry.analyze_sport_model({"sport": "padel", "market": "moneyline"})`

## Owner Decision Rules

- If `data_availability_tiers.py` only describes data readiness, do not overload it with regression math.
- If it already owns sport profile metadata cleanly, add regression profile fields there.
- If no existing module owns regression profile selection, create a small focused profile module.
- `backtesting_engine.py` must remain the only public backtest runner.
- `backtest_strategy_bankroll.py` must remain math/simulation only.

## Preliminary Decision

- data_availability_tiers_has_SPORT_PROFILES: `True`
- data_availability_tiers_has_regression_fields: `False`
- data_availability_tiers_appears_readiness_or_tier_focused: `True`

DECISION: `do_not_overload_data_availability_tiers_create_regression_profile_owner`
