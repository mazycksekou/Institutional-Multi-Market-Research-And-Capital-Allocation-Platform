# NCAAF Free vs Paid Source Ledger

1. source_ledger_row_count: 18
2. free_open_loader_needed_count: 5
3. free_open_manual_import_needed_count: 4
4. paid_data_subscription_required_count: 2

## Lanes
- team_identity_crosswalk category=free_open_loader_needed source=CollegeFootballData API/docs
- schedule_game_results category=free_open_loader_needed source=CollegeFootballData API/docs
- drive_summary_epa category=free_open_loader_needed source=CollegeFootballData API/docs
- play_by_play_epa category=free_open_loader_needed source=CollegeFootballData API/docs
- venue_stadium_metadata category=free_open_loader_needed source=CollegeFootballData API/docs
- team_metadata_entities category=free_open_partial source=Wikidata college football entities
- postseason_metadata category=free_open_partial source=Wikipedia bowl and CFP tables
- official_ncaa_stats_pages category=free_open_manual_import_needed source=NCAA football official pages
- conference_official_context category=free_open_manual_import_needed source=Conference official football pages
- school_roster_depth_chart category=free_open_manual_import_needed source=School athletic football pages
- bowl_cfp_official_context category=free_open_manual_import_needed source=Bowl and CFP official pages
- espn_scoreboard_context category=policy_blocked source=ESPN college football pages
- sports_reference_context category=policy_blocked source=Sports Reference college football pages
- cfbfastr_sportsdataverse_context category=license_terms_unclear source=cfbfastR GitHub repository
- public_weather_stadium_context category=unavailable_after_max_effort source=Public weather archive
- injury_availability_depth_chart_feed category=paid_data_subscription_required source=Licensed NCAAF data vendor
- advanced_team_player_stats_feed category=paid_data_subscription_required source=Licensed NCAAF data vendor
- kaggle_dataset_catalog_context category=login_paywall_captcha_blocked source=Kaggle college football dataset catalog
