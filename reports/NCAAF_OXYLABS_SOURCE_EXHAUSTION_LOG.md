# NCAAF Oxylabs Source Exhaustion Log

1. source_candidate_count: 18
2. lanes_tested_count: 18
3. oxylabs_total_calls_attempted: 90
4. oxylabs_total_calls_successful: 17
5. oxylabs_total_calls_failed: 73

## Lanes
- team_identity_crosswalk final=free_open_backfilled transport=residential_proxy records=1
- schedule_game_results final=free_open_backfilled transport=residential_proxy records=1
- drive_summary_epa final=free_open_backfilled transport=residential_proxy records=1
- play_by_play_epa final=free_open_backfilled transport=residential_proxy records=1
- venue_stadium_metadata final=free_open_backfilled transport=residential_proxy records=1
- team_metadata_entities final=free_open_metadata_only transport=web_scraper_api records=1
- postseason_metadata final=free_open_metadata_only transport=web_scraper_api records=1
- official_ncaa_stats_pages final=manual_import_required transport=web_scraper_api records=0
- conference_official_context final=manual_import_required transport=web_scraper_api records=0
- school_roster_depth_chart final=manual_import_required transport=web_scraper_api records=0
- bowl_cfp_official_context final=manual_import_required transport=web_scraper_api records=0
- espn_scoreboard_context final=policy_blocked transport=web_scraper_api records=0
- sports_reference_context final=policy_blocked transport=web_scraper_api records=0
- cfbfastr_sportsdataverse_context final=license_terms_unclear transport=web_scraper_api records=0
- public_weather_stadium_context final=unavailable_after_exhaustive_free_search transport=web_scraper_api records=0
- injury_availability_depth_chart_feed final=paid_subscription_required transport=web_scraper_api records=0
- advanced_team_player_stats_feed final=paid_subscription_required transport=web_scraper_api records=0
- kaggle_dataset_catalog_context final=login_paywall_captcha_blocked transport=web_scraper_api records=0
