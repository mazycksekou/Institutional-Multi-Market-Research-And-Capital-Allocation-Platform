# Basketball Free vs Paid Source Ledger

- source_count: 72

| sport | lane_name | free_or_paid_category | current_record_count | candidate_source_name | sample_attempted | loader_exists | manual_template_exists | policy_status | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| basketball_nba | schedule_results | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_nba | team_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_nba | player_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_nba | play_by_play | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_nba | advanced_team_player_stats | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_nba | pace_possessions | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_nba | shot_location | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_nba | referee_official_assignments | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_nba | rest_travel_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_nba | arena_venue_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_nba | roster_continuity | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_nba | injuries_availability | free_open_manual_import_needed | 0 | SportsDataverse release assets | False | True | True | approved_release_asset_with_terms_caution | create_manual_import_template |
| basketball_nba | transaction_availability_volatility | paid_data_subscription_required | 0 | Stats Perform basketball data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_nba | optical_tracking_player_location | paid_data_subscription_required | 0 | Second Spectrum tracking data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_nba | restricted_reference_tables | blocked_reference_or_restricted_source | 0 | Basketball Reference / Sports Reference | False | True | False | blocked_reference_or_restricted_source | mark_policy_blocked |
| basketball_nba | duplicate_box_score_mirror_sources | obsolete_or_duplicate | 0 | SportsDataverse release assets | False | True | False | approved_release_asset_with_terms_caution | mark_obsolete_or_duplicate |
| basketball_nba | lineup_on_off | license_terms_unclear | 0 | nba_api | False | True | True | license_terms_unclear | escalate_manual_review |
| basketball_wnba | schedule_results | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_wnba | team_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_wnba | player_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_wnba | play_by_play | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_wnba | advanced_team_player_stats | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_wnba | pace_possessions | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_wnba | shot_location | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_wnba | referee_official_assignments | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_wnba | rest_travel_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_wnba | arena_venue_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_wnba | roster_continuity | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_wnba | injuries_availability | free_open_manual_import_needed | 0 | SportsDataverse release assets | False | True | True | approved_release_asset_with_terms_caution | create_manual_import_template |
| basketball_wnba | transaction_availability_volatility | paid_data_subscription_required | 0 | Stats Perform basketball data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_wnba | optical_tracking_player_location | paid_data_subscription_required | 0 | Second Spectrum tracking data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_wnba | restricted_reference_tables | blocked_reference_or_restricted_source | 0 | Basketball Reference / Sports Reference | False | True | False | blocked_reference_or_restricted_source | mark_policy_blocked |
| basketball_wnba | duplicate_box_score_mirror_sources | obsolete_or_duplicate | 0 | SportsDataverse release assets | False | True | False | approved_release_asset_with_terms_caution | mark_obsolete_or_duplicate |
| basketball_wnba | lineup_on_off | free_open_partial | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaab | schedule_results | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaab | team_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaab | player_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaab | play_by_play | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaab | advanced_team_player_stats | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaab | pace_possessions | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaab | shot_location | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaab | referee_official_assignments | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaab | rest_travel_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaab | arena_venue_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaab | roster_continuity | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaab | injuries_availability | paid_data_subscription_required | 0 | Sportradar Basketball APIs | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaab | transaction_availability_volatility | paid_data_subscription_required | 0 | Stats Perform basketball data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaab | optical_tracking_player_location | paid_data_subscription_required | 0 | Second Spectrum tracking data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaab | restricted_reference_tables | blocked_reference_or_restricted_source | 0 | Basketball Reference / Sports Reference | False | True | False | blocked_reference_or_restricted_source | mark_policy_blocked |
| basketball_ncaab | duplicate_box_score_mirror_sources | obsolete_or_duplicate | 0 | SportsDataverse release assets | False | True | False | approved_release_asset_with_terms_caution | mark_obsolete_or_duplicate |
| basketball_ncaab | lineup_on_off | paid_data_subscription_required | 0 | Genius Sports official data APIs | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaab | strength_of_schedule_context | free_open_manual_import_needed | 0 | NCAA NET ranking tables | False | True | True | manual_import_only | create_manual_import_template |
| basketball_ncaab | conference_tournament_context | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | schedule_results | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaaw | team_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaaw | player_box_scores | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaaw | play_by_play | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaaw | advanced_team_player_stats | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | backfill_approved_seasons |
| basketball_ncaaw | pace_possessions | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | shot_location | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | referee_official_assignments | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | rest_travel_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | arena_venue_features | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | roster_continuity | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
| basketball_ncaaw | injuries_availability | paid_data_subscription_required | 0 | Sportradar Basketball APIs | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaaw | transaction_availability_volatility | paid_data_subscription_required | 0 | Stats Perform basketball data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaaw | optical_tracking_player_location | paid_data_subscription_required | 0 | Second Spectrum tracking data | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaaw | restricted_reference_tables | blocked_reference_or_restricted_source | 0 | Basketball Reference / Sports Reference | False | True | False | blocked_reference_or_restricted_source | mark_policy_blocked |
| basketball_ncaaw | duplicate_box_score_mirror_sources | obsolete_or_duplicate | 0 | SportsDataverse release assets | False | True | False | approved_release_asset_with_terms_caution | mark_obsolete_or_duplicate |
| basketball_ncaaw | lineup_on_off | paid_data_subscription_required | 0 | Genius Sports official data APIs | False | True | True | paid_subscription_required | mark_paid_subscription_required |
| basketball_ncaaw | strength_of_schedule_context | free_open_manual_import_needed | 0 | NCAA NET ranking tables | False | True | True | manual_import_only | create_manual_import_template |
| basketball_ncaaw | conference_tournament_context | free_open_populated | 3 | SportsDataverse release assets | True | True | False | approved_release_asset_with_terms_caution | add_schema_field |
