# NCAAF Oxylabs Reclassification Report

1. reclassification_row_count: 10
2. paid_still_required_count: 2
3. manual_import_still_required_count: 4
4. policy_blocker_still_applies_count: 2

## Lanes
- official_ncaa_stats_pages final=manual_import_required reason=NCAA public pages remain manual-only unless exact automated terms approve extraction.
- conference_official_context final=manual_import_required reason=Conference pages remain manual-only in this pass.
- school_roster_depth_chart final=manual_import_required reason=School roster/depth-chart pages remain manual-only unless exact site policy approves automation.
- bowl_cfp_official_context final=manual_import_required reason=Bowl and CFP official pages remain manual-only for timestamped review.
- espn_scoreboard_context final=policy_blocked reason=ESPN scraping is blocked unless an exact path passes policy review; no automated extraction is approved here.
- sports_reference_context final=policy_blocked reason=Sports Reference / College Football Reference scraping is explicitly prohibited.
- cfbfastr_sportsdataverse_context final=license_terms_unclear reason=cfbfastR/SportsDataverse requires exact license and upstream-source legal review before broad automated reuse.
- injury_availability_depth_chart_feed final=paid_subscription_required reason=Production NCAAF injury, depth chart, advanced stat, and odds feeds remain paid/licensed.
- advanced_team_player_stats_feed final=paid_subscription_required reason=Production NCAAF injury, depth chart, advanced stat, and odds feeds remain paid/licensed.
- kaggle_dataset_catalog_context final=login_paywall_captcha_blocked reason=Kaggle catalog access remains account-gated and is not used for automated backfill.
