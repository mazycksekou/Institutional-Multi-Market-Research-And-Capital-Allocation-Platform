# NFL Completion Final Report

1. sport: americanfootball_nfl
2. run_mode: open_free_mode
3. started_at: 2026-06-04T23:16:55.705509+00:00
4. completed_at: 2026-06-04T23:16:56.778774+00:00
5. record_count_total: 6461599
6. rejected_count_total: 0
7. feature_groups_built: depth_chart_stability, injury_availability, nextgen_efficiency_candidates, player_usage_participation, player_usage_snaps, roster_continuity, team_game_efficiency_candidates, team_game_play_volume
8. feature_groups_model_eligible: average_margin, average_points_against, average_points_for, average_rest_days, away_win_rate, close_game_win_rate, defensive_volatility, depth_chart_stability, home_win_rate, injury_availability, late_season_win_rate, nextgen_efficiency_candidates, player_usage_participation, player_usage_snaps, point_differential, roster_continuity, schedule_strength_proxy, scoring_volatility, simple_team_rating, team_game_efficiency_candidates, team_game_play_volume, win_rate
9. feature_groups_blocked: coaching_continuity_candidates, coaching_staff_by_team_season, coordinator_by_team_season, coordinator_continuity_candidates, depth_chart_stability, head_coach_by_team_season, injury_availability, nextgen_efficiency_candidates, player_usage_participation, player_usage_snaps, roster_continuity, staff_turnover_candidates, team_game_efficiency_candidates, team_game_play_volume
10. cutoff_safe_feature_count: 6
11. future_leakage_checks_passed: true
12. tests_run: 11
13. tests_passed: 11
14. blockers: download_not_allowed, ftn_terms_not_proven_open, html_scraping_terms_unclear, license_unverified, no_coaching_records_available, one_season_required, robots_disallows_automation, sports_reference_scraping_blocked
15. fallbacks_used: blocked_policy, blocked_terms_review, manual_csv_import, nflverse_release_download, open_release_download, structured_open_source_unverified, wikidata_entity_api, wikidata_local_dump, wikipedia_structured_tables, wikipedia_supplemental_only
16. commit_hash: 7fdf533d0b685dd2d312c489f2aa8b0db94eb4a6

## Source Families
| sport | source_id | source_family | policy_status | retrieval_method | license_or_terms_note | season_coverage | date_coverage | record_count | rejected_count | blocker | fallback | model_eligible | cutoff_safe |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| americanfootball_nfl | nflverse_schedules_results | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 7548 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_play_by_play | nflverse | populated | open_github_release | reviewed_open_metadata | 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 1184000 | 0 | none | nflverse_release_download | true | true |
| americanfootball_nfl | nflverse_team_stats | nflverse | populated | open_github_release | reviewed_open_metadata | 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 13444 | 0 | download_not_allowed | open_release_download | true | true |
| americanfootball_nfl | nflverse_weekly_player_stats | nflverse | populated | open_github_release | reviewed_open_metadata | 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 440336 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_rosters | nflverse | populated | open_github_release | reviewed_open_metadata | 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927, 1928, 1929, 1930, 1931, 1932, 1933, 1934, 1935, 1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026 | {} | 135870 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_weekly_rosters | nflverse | populated | open_github_release | reviewed_open_metadata | 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 828713 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_snap_counts | nflverse | populated | open_github_release | reviewed_open_metadata | 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 271384 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_participation | nflverse | populated | open_github_release | reviewed_open_metadata | 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 384636 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_depth_charts | nflverse | populated | open_github_release | reviewed_open_metadata | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026 | {} | 1003228 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_injuries | nflverse | populated | open_github_release | reviewed_open_metadata | 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 79716 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_transactions | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 4975 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_draft | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 12927 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_combine | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 8968 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_players | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 25040 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_teams | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 36 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_officials | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 21900 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_stadiums | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 7548 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_weather | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 7548 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_betting_lines_or_market_odds | nflverse | populated | open_github_release | reviewed_open_metadata | all | {} | 7548 | 0 | none | open_release_download | true | false |
| americanfootball_nfl | nflverse_pace_or_play_volume | nflverse | populated | open_github_release | reviewed_open_metadata | 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 1184000 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_roster_continuity | nflverse | populated | open_github_release | reviewed_open_metadata | 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 | {} | 828713 | 0 | none | open_release_download | true | true |
| americanfootball_nfl | nflverse_nextgen_stats | nflverse | populated | open_github_release | reviewed_open_metadata | 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 | {} | 3521 | 0 | none | open_release_download | true | false |
| americanfootball_nfl | nflverse_coaching_research | research | blocked | research_required | research_required | none | {} | 0 | 0 | download_not_allowed | structured_open_source_unverified | false | false |
| americanfootball_nfl | nflverse_pfr_advstats_blocked | nflverse | blocked | open_release_terms_review_required | sports_reference_derivative_terms_review_required | none | {} | 0 | 0 | one_season_required | blocked_terms_review | false | false |
| americanfootball_nfl | nflverse_ftn_charting_blocked | nflverse | blocked | open_release_terms_review_required | third_party_terms_review_required | none | {} | 0 | 0 | one_season_required | blocked_terms_review | false | false |
| americanfootball_nfl | official_team_staff_pages | official_team_staff_pages | blocked | public_web | not_applicable | none | {} | 0 | 0 | robots_disallows_automation | blocked_terms_review | false | false |
| americanfootball_nfl | official_team_press_releases | official_team_press_releases | blocked | public_web | not_applicable | none | {} | 0 | 0 | html_scraping_terms_unclear | blocked_terms_review | false | false |
| americanfootball_nfl | official_nfl_staff_or_news_pages | official_nfl_staff_or_news_pages | blocked | public_web | not_applicable | none | {} | 0 | 0 | html_scraping_terms_unclear | blocked_terms_review | false | false |
| americanfootball_nfl | team_sitemaps | team_sitemaps | blocked | public_web | not_applicable | none | {} | 0 | 0 | html_scraping_terms_unclear | blocked_terms_review | false | false |
| americanfootball_nfl | wikidata_coaching_seed | wikidata_coaching_seed | approved_empty | structured_open_api | cc0 | none | {} | 0 | 0 | none | wikidata_entity_api | false | false |
| americanfootball_nfl | wikidata_entity_api | wikidata_entity_api | approved_empty | structured_open_api | cc0 | none | {} | 0 | 0 | none | wikidata_entity_api | false | false |
| americanfootball_nfl | wikidata_local_dump | wikidata_local_dump | approved_empty | local_dump_file | cc0 | none | {} | 0 | 0 | none | wikidata_local_dump | false | false |
| americanfootball_nfl | wikipedia_coaching_tables | wikipedia_coaching_tables | approved_empty | structured_open_api | cc_by_sa | none | {} | 0 | 0 | none | wikipedia_structured_tables | false | false |
| americanfootball_nfl | wikipedia_coaching_seed | wikipedia_coaching_seed | approved_empty | structured_open_api | cc_by_sa | none | {} | 0 | 0 | none | wikipedia_supplemental_only | false | false |
| americanfootball_nfl | open_github_coaching_dataset | open_github_coaching_dataset | blocked | open_github_file | license_unverified | none | {} | 0 | 0 | license_unverified | blocked_policy | false | false |
| americanfootball_nfl | manual_csv_import | manual_csv_import | approved_empty | manual_local_file | user_declared | none | {} | 0 | 0 | none | manual_csv_import | false | false |
| americanfootball_nfl | blocked_pfr_reference | blocked_pfr_reference | blocked | public_web | not_applicable | none | {} | 0 | 0 | sports_reference_scraping_blocked | blocked_policy | false | false |
| americanfootball_nfl | blocked_ftn_charting | blocked_ftn_charting | blocked | third_party_release | not_applicable | none | {} | 0 | 0 | ftn_terms_not_proven_open | blocked_policy | false | false |
