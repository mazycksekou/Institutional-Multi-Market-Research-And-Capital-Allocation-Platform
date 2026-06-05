import unittest

from automation_scheduler.source_discovery_query_builder import build_query_variant_bundle, build_search_term_bundle


class TestSourceDiscoveryQueryBuilder(unittest.TestCase):
    def test_build_query_variant_bundle_expands_synonyms(self):
        bundle = build_query_variant_bundle(
            sport="nfl",
            field_name="coaching_staff_role_history",
            source_family="official_team_staff_pages",
            official_domain="nfl.com",
            extra_synonyms=["coach lineage"],
        )

        self.assertEqual(bundle["sport"], "nfl")
        self.assertEqual(bundle["league"], "NFL")
        self.assertIn("coaching staff role history", bundle["exact_terms"])
        self.assertIn("coaching staff history", bundle["synonym_terms"])
        self.assertIn("coach lineage", bundle["synonym_terms"])
        self.assertIn("NFL coaching staff role history dataset", bundle["query_variants"])
        self.assertIn("NFL coaching staff history dataset", bundle["query_variants"])
        self.assertIn("coaching staff history site:nfl.com", bundle["query_variants"])
        self.assertEqual(bundle["query_variants"].count("NFL coaching staff role history dataset"), 1)

    def test_build_search_term_bundle_matches_query_bundle(self):
        query_bundle = build_query_variant_bundle(
            sport="mlb",
            field_name="team_game_run_profile",
            source_family="retrosheet_open_dataset",
            official_domain="mlb.com",
        )
        search_bundle = build_search_term_bundle(
            sport="mlb",
            field_name="team_game_run_profile",
            source_family="retrosheet_open_dataset",
            official_domain="mlb.com",
        )

        self.assertEqual(search_bundle["exact_search_terms"], query_bundle["exact_terms"])
        self.assertEqual(search_bundle["synonym_search_terms"], query_bundle["synonym_terms"])
        self.assertEqual(search_bundle["query_variants"], query_bundle["query_variants"])


if __name__ == "__main__":
    unittest.main()
