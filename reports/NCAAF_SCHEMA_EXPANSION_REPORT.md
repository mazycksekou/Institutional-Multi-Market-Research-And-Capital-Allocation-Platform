# NCAAF Schema Expansion Report

1. new_fields_created_count: 14
2. new_tables_created_count: 7

## Fields
- team_slug table=ncaaf_teams validation=sample_verified
- conference_slug table=ncaaf_teams validation=sample_verified
- final_margin_bucket table=ncaaf_games validation=sample_verified
- total_points_bucket table=ncaaf_games validation=sample_verified
- postgame_training_join_key table=ncaaf_games validation=sample_verified
- drive_success_rate_proxy table=ncaaf_drives validation=sample_verified
- drive_points_per_opportunity table=ncaaf_drives validation=sample_verified
- play_success_flag table=ncaaf_plays validation=sample_verified
- explosive_play_flag table=ncaaf_plays validation=sample_verified
- epa_bucket table=ncaaf_plays validation=sample_verified
- venue_slug table=ncaaf_venues validation=sample_verified
- altitude_bucket table=ncaaf_venues validation=sample_verified
- team_wikidata_slug table=ncaaf_team_metadata validation=sample_verified
- postseason_context_slug table=ncaaf_postseason_metadata validation=sample_verified
