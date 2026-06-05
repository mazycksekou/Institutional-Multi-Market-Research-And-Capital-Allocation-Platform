import unittest
from unittest.mock import patch

from automation_scheduler.completed_sports_license_parser import evaluate_completed_sports_license


class TestCompletedSportsLicenseParser(unittest.TestCase):
    def test_detects_all_rights_reserved(self):
        candidate = {"source_id": "x", "source_domain": "example.com", "license_url": "https://example.com/license"}
        with patch(
            "automation_scheduler.completed_sports_license_parser.fetch_public_page_text",
            return_value={"ok": True, "text": "All rights reserved. No redistribution.", "transport": "web_scraper_api"},
        ):
            result = evaluate_completed_sports_license(candidate)
        self.assertTrue(result["license_checked"])
        self.assertEqual(result["license_name_if_any"], "All rights reserved")
        self.assertFalse(result["redistribution_allowed"])


if __name__ == "__main__":
    unittest.main()

