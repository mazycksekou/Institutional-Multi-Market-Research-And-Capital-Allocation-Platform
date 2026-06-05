# Maximum Effort Schema Expansion V2 Report

- new_fields_created_count: 8
- new_tables_created_count: 4
- model_eligible_features_added: coaching_staff_role_history, staff_turnover_severity, official_assignment_tendency, stadium_surface_roof_state, manager_coach_role_history, draft_pick_origin, umpire_assignment_tendency

| field_name | sport | source_id | retrieval_method | cutoff_safe | model_eligible | confidence |
| --- | --- | --- | --- | --- | --- | ---: |
| coaching_staff_role_history | nfl | official_team_staff_pages | oxylabs_web_scraper_api | true | true | 0.88 |
| staff_turnover_severity | nfl | official_team_press_releases | oxylabs_web_scraper_api | true | true | 0.76 |
| official_assignment_tendency | nfl | official_nfl_staff_or_news_pages | oxylabs_residential_proxy | true | true | 0.8 |
| stadium_surface_roof_state | nfl | nflverse_schedules_results | open_github_release | true | true | 0.84 |
| manager_coach_role_history | mlb | mlb_stats_api | approved_structured_api | true | true | 0.86 |
| draft_pick_origin | mlb | draft_lahman | open_dataset | true | true | 0.83 |
| umpire_assignment_tendency | mlb | retrosheet_open_dataset | direct_http_get | true | true | 0.77 |
| probable_pitcher_confirmation_history | mlb | mlb_stats_api | approved_structured_api | true | false | 0.81 |
