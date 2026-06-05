# Basketball Free vs Paid Gap Action Plan

- gap_rows_total: 72
- generic actions: 0

| sport | lane_name | free_or_paid_category | action | allowed_action | reason |
| --- | --- | --- | --- | --- | --- |
| basketball_nba | schedule_results | free_open_populated | backfill_approved_seasons | True | One-season SportsDataverse schedule CSV sample is available with stable game/date/team/result fields. |
| basketball_nba | team_box_scores | free_open_populated | backfill_approved_seasons | True | One-season team box score CSV sample validates team-game statistics. |
| basketball_nba | player_box_scores | free_open_populated | backfill_approved_seasons | True | One-season player box score CSV sample validates player-game statistics. |
| basketball_nba | play_by_play | free_open_populated | backfill_approved_seasons | True | One-season play-by-play CSV sample validates event-level basketball data. |
| basketball_nba | advanced_team_player_stats | free_open_populated | backfill_approved_seasons | True | Team season-stat release validates structured stat labels and values. |
| basketball_nba | pace_possessions | free_open_populated | add_schema_field | True | Possessions are derivable from verified team box score fields with provenance to the sampled source. |
| basketball_nba | shot_location | free_open_populated | add_schema_field | True | One-season shot CSV sample validates shot coordinate fields. |
| basketball_nba | referee_official_assignments | free_open_populated | add_schema_field | True | One-season officials CSV sample validates official names/positions by game. |
| basketball_nba | rest_travel_features | free_open_populated | add_schema_field | True | Rest/back-to-back features are derivable from verified dated schedule rows; travel distance remains estimate-only without venue coordinates. |
| basketball_nba | arena_venue_features | free_open_populated | add_schema_field | True | Schedule samples expose venue and neutral-site fields. |
| basketball_nba | roster_continuity | free_open_populated | add_schema_field | True | Game roster samples are available for one-season verification. |
| basketball_nba | injuries_availability | free_open_manual_import_needed | create_manual_import_template | True | No policy-safe complete historical automated injury feed was verified; manual NBA/WNBA reports can be imported, college coverage needs a licensed vendor. |
| basketball_nba | transaction_availability_volatility | paid_data_subscription_required | mark_paid_subscription_required | True | Free releases validate rosters but not complete timestamped transaction volatility. |
| basketball_nba | optical_tracking_player_location | paid_data_subscription_required | mark_paid_subscription_required | True | True player/ball tracking is not available in the verified free release lanes. |
| basketball_nba | restricted_reference_tables | blocked_reference_or_restricted_source | mark_policy_blocked | True | User explicitly prohibited Basketball Reference, Sports Reference, and College Basketball Reference scraping. |
| basketball_nba | duplicate_box_score_mirror_sources | obsolete_or_duplicate | mark_obsolete_or_duplicate | True | Verified SportsDataverse release lanes already cover the same box-score surface with provenance. |
| basketball_nba | lineup_on_off | license_terms_unclear | escalate_manual_review | True | nba_api documents lineup/on-off endpoints, but direct NBA Stats API path needs exact policy review before retrieval. |
| basketball_wnba | schedule_results | free_open_populated | backfill_approved_seasons | True | One-season SportsDataverse schedule CSV sample is available with stable game/date/team/result fields. |
| basketball_wnba | team_box_scores | free_open_populated | backfill_approved_seasons | True | One-season team box score CSV sample validates team-game statistics. |
| basketball_wnba | player_box_scores | free_open_populated | backfill_approved_seasons | True | One-season player box score CSV sample validates player-game statistics. |
| basketball_wnba | play_by_play | free_open_populated | backfill_approved_seasons | True | One-season play-by-play CSV sample validates event-level basketball data. |
| basketball_wnba | advanced_team_player_stats | free_open_populated | backfill_approved_seasons | True | Team season-stat release validates structured stat labels and values. |
| basketball_wnba | pace_possessions | free_open_populated | add_schema_field | True | Possessions are derivable from verified team box score fields with provenance to the sampled source. |
| basketball_wnba | shot_location | free_open_populated | add_schema_field | True | One-season shot CSV sample validates shot coordinate fields. |
| basketball_wnba | referee_official_assignments | free_open_populated | add_schema_field | True | One-season officials CSV sample validates official names/positions by game. |
| basketball_wnba | rest_travel_features | free_open_populated | add_schema_field | True | Rest/back-to-back features are derivable from verified dated schedule rows; travel distance remains estimate-only without venue coordinates. |
| basketball_wnba | arena_venue_features | free_open_populated | add_schema_field | True | Schedule samples expose venue and neutral-site fields. |
| basketball_wnba | roster_continuity | free_open_populated | add_schema_field | True | Game roster samples are available for one-season verification. |
| basketball_wnba | injuries_availability | free_open_manual_import_needed | create_manual_import_template | True | No policy-safe complete historical automated injury feed was verified; manual NBA/WNBA reports can be imported, college coverage needs a licensed vendor. |
| basketball_wnba | transaction_availability_volatility | paid_data_subscription_required | mark_paid_subscription_required | True | Free releases validate rosters but not complete timestamped transaction volatility. |
| basketball_wnba | optical_tracking_player_location | paid_data_subscription_required | mark_paid_subscription_required | True | True player/ball tracking is not available in the verified free release lanes. |
| basketball_wnba | restricted_reference_tables | blocked_reference_or_restricted_source | mark_policy_blocked | True | User explicitly prohibited Basketball Reference, Sports Reference, and College Basketball Reference scraping. |
| basketball_wnba | duplicate_box_score_mirror_sources | obsolete_or_duplicate | mark_obsolete_or_duplicate | True | Verified SportsDataverse release lanes already cover the same box-score surface with provenance. |
| basketball_wnba | lineup_on_off | free_open_partial | backfill_approved_seasons | True | WNBA Stats lineup release has a current-season CSV sample; completed-season historical coverage still needs validation. |
| basketball_ncaab | schedule_results | free_open_populated | backfill_approved_seasons | True | One-season SportsDataverse schedule CSV sample is available with stable game/date/team/result fields. |
| basketball_ncaab | team_box_scores | free_open_populated | backfill_approved_seasons | True | One-season team box score CSV sample validates team-game statistics. |
| basketball_ncaab | player_box_scores | free_open_populated | backfill_approved_seasons | True | One-season player box score CSV sample validates player-game statistics. |
| basketball_ncaab | play_by_play | free_open_populated | backfill_approved_seasons | True | One-season play-by-play CSV sample validates event-level basketball data. |
| basketball_ncaab | advanced_team_player_stats | free_open_populated | backfill_approved_seasons | True | Team season-stat release validates structured stat labels and values. |
| basketball_ncaab | pace_possessions | free_open_populated | add_schema_field | True | Possessions are derivable from verified team box score fields with provenance to the sampled source. |
| basketball_ncaab | shot_location | free_open_populated | add_schema_field | True | One-season shot CSV sample validates shot coordinate fields. |
| basketball_ncaab | referee_official_assignments | free_open_populated | add_schema_field | True | One-season officials CSV sample validates official names/positions by game. |
| basketball_ncaab | rest_travel_features | free_open_populated | add_schema_field | True | Rest/back-to-back features are derivable from verified dated schedule rows; travel distance remains estimate-only without venue coordinates. |
| basketball_ncaab | arena_venue_features | free_open_populated | add_schema_field | True | Schedule samples expose venue and neutral-site fields. |
| basketball_ncaab | roster_continuity | free_open_populated | add_schema_field | True | Game roster samples are available for one-season verification. |
| basketball_ncaab | injuries_availability | paid_data_subscription_required | mark_paid_subscription_required | True | No policy-safe complete historical automated injury feed was verified; manual NBA/WNBA reports can be imported, college coverage needs a licensed vendor. |
| basketball_ncaab | transaction_availability_volatility | paid_data_subscription_required | mark_paid_subscription_required | True | Free releases validate rosters but not complete timestamped transaction volatility. |
| basketball_ncaab | optical_tracking_player_location | paid_data_subscription_required | mark_paid_subscription_required | True | True player/ball tracking is not available in the verified free release lanes. |
| basketball_ncaab | restricted_reference_tables | blocked_reference_or_restricted_source | mark_policy_blocked | True | User explicitly prohibited Basketball Reference, Sports Reference, and College Basketball Reference scraping. |
| basketball_ncaab | duplicate_box_score_mirror_sources | obsolete_or_duplicate | mark_obsolete_or_duplicate | True | Verified SportsDataverse release lanes already cover the same box-score surface with provenance. |
| basketball_ncaab | lineup_on_off | paid_data_subscription_required | mark_paid_subscription_required | True | No policy-safe free college lineup/on-off release was verified; licensed data is needed for reliable lineup continuity. |
| basketball_ncaab | strength_of_schedule_context | free_open_manual_import_needed | create_manual_import_template | True | Official NET tables are public but automated scraping is not enabled; manual snapshots can fill the lane. |
| basketball_ncaab | conference_tournament_context | free_open_populated | add_schema_field | True | Schedule samples expose conference/season-type/neutral-site fields usable for tournament context. |
| basketball_ncaaw | schedule_results | free_open_populated | backfill_approved_seasons | True | One-season SportsDataverse schedule CSV sample is available with stable game/date/team/result fields. |
| basketball_ncaaw | team_box_scores | free_open_populated | backfill_approved_seasons | True | One-season team box score CSV sample validates team-game statistics. |
| basketball_ncaaw | player_box_scores | free_open_populated | backfill_approved_seasons | True | One-season player box score CSV sample validates player-game statistics. |
| basketball_ncaaw | play_by_play | free_open_populated | backfill_approved_seasons | True | One-season play-by-play CSV sample validates event-level basketball data. |
| basketball_ncaaw | advanced_team_player_stats | free_open_populated | backfill_approved_seasons | True | Team season-stat release validates structured stat labels and values. |
| basketball_ncaaw | pace_possessions | free_open_populated | add_schema_field | True | Possessions are derivable from verified team box score fields with provenance to the sampled source. |
| basketball_ncaaw | shot_location | free_open_populated | add_schema_field | True | One-season shot CSV sample validates shot coordinate fields. |
| basketball_ncaaw | referee_official_assignments | free_open_populated | add_schema_field | True | One-season officials CSV sample validates official names/positions by game. |
| basketball_ncaaw | rest_travel_features | free_open_populated | add_schema_field | True | Rest/back-to-back features are derivable from verified dated schedule rows; travel distance remains estimate-only without venue coordinates. |
| basketball_ncaaw | arena_venue_features | free_open_populated | add_schema_field | True | Schedule samples expose venue and neutral-site fields. |
| basketball_ncaaw | roster_continuity | free_open_populated | add_schema_field | True | Game roster samples are available for one-season verification. |
| basketball_ncaaw | injuries_availability | paid_data_subscription_required | mark_paid_subscription_required | True | No policy-safe complete historical automated injury feed was verified; manual NBA/WNBA reports can be imported, college coverage needs a licensed vendor. |
| basketball_ncaaw | transaction_availability_volatility | paid_data_subscription_required | mark_paid_subscription_required | True | Free releases validate rosters but not complete timestamped transaction volatility. |
| basketball_ncaaw | optical_tracking_player_location | paid_data_subscription_required | mark_paid_subscription_required | True | True player/ball tracking is not available in the verified free release lanes. |
| basketball_ncaaw | restricted_reference_tables | blocked_reference_or_restricted_source | mark_policy_blocked | True | User explicitly prohibited Basketball Reference, Sports Reference, and College Basketball Reference scraping. |
| basketball_ncaaw | duplicate_box_score_mirror_sources | obsolete_or_duplicate | mark_obsolete_or_duplicate | True | Verified SportsDataverse release lanes already cover the same box-score surface with provenance. |
| basketball_ncaaw | lineup_on_off | paid_data_subscription_required | mark_paid_subscription_required | True | No policy-safe free college lineup/on-off release was verified; licensed data is needed for reliable lineup continuity. |
| basketball_ncaaw | strength_of_schedule_context | free_open_manual_import_needed | create_manual_import_template | True | Official NET tables are public but automated scraping is not enabled; manual snapshots can fill the lane. |
| basketball_ncaaw | conference_tournament_context | free_open_populated | add_schema_field | True | Schedule samples expose conference/season-type/neutral-site fields usable for tournament context. |
