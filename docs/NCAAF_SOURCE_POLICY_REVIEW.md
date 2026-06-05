# NCAAF Source Policy Review

- CollegeFootballData API/docs: final_state=free_open_backfilled decision=accepted_for_automated_normalized_backfill reason=CFBD-style documented API surface is accepted for tiny deterministic normalized facts in this pass; live key/API extraction remains governed by API terms and adapter safeguards.
- Wikidata college football entities: final_state=free_open_metadata_only decision=accepted_for_metadata_only reason=Wikidata is accepted for attribution-preserving metadata-only NCAAF team enrichment.
- Wikipedia bowl and CFP tables: final_state=free_open_metadata_only decision=accepted_for_metadata_only reason=Wikipedia bowl/CFP tables are accepted as metadata-only supplemental context.
- NCAA football official pages: final_state=manual_import_required decision=accepted_for_manual_import_only reason=NCAA public pages remain manual-only unless exact automated terms approve extraction.
- Conference official football pages: final_state=manual_import_required decision=accepted_for_manual_import_only reason=Conference pages remain manual-only in this pass.
- School athletic football pages: final_state=manual_import_required decision=accepted_for_manual_import_only reason=School roster/depth-chart pages remain manual-only unless exact site policy approves automation.
- Bowl and CFP official pages: final_state=manual_import_required decision=accepted_for_manual_import_only reason=Bowl and CFP official pages remain manual-only for timestamped review.
- ESPN college football pages: final_state=policy_blocked decision=rejected_policy_blocked reason=ESPN scraping is blocked unless an exact path passes policy review; no automated extraction is approved here.
- Sports Reference college football pages: final_state=policy_blocked decision=rejected_policy_blocked reason=Sports Reference / College Football Reference scraping is explicitly prohibited.
- cfbfastR GitHub repository: final_state=license_terms_unclear decision=license_terms_unclear reason=cfbfastR/SportsDataverse requires exact license and upstream-source legal review before broad automated reuse.
- SportsDataverse CFB data: final_state=license_terms_unclear decision=license_terms_unclear reason=SportsDataverse CFB data requires exact data license and upstream rights review.
- Public weather archive: final_state=unavailable_after_exhaustive_free_search decision=unavailable_after_exhaustive_search reason=No policy-approved normalized NCAAF weather archive was accepted after exhaustive free/open search.
- Kaggle college football dataset catalog: final_state=login_paywall_captcha_blocked decision=rejected_login_paywall_captcha reason=Kaggle catalog access remains account-gated and is not used for automated backfill.
- Licensed NCAAF data vendor: final_state=paid_subscription_required decision=rejected_terms_blocked reason=Production NCAAF injury, depth chart, advanced stat, and odds feeds remain paid/licensed.
