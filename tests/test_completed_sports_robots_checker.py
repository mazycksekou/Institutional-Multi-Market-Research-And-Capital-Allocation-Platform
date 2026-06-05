import unittest
from unittest.mock import patch

from automation_scheduler.completed_sports_robots_checker import evaluate_completed_sports_robots


class TestCompletedSportsRobotsChecker(unittest.TestCase):
    def test_disallow_rule_blocks_target_path(self):
        candidate = {"source_id": "x", "source_domain": "example.com", "robots_url": "https://example.com/robots.txt", "source_path_or_path_pattern": "/private"}
        with patch(
            "automation_scheduler.completed_sports_robots_checker.fetch_public_page_text",
            return_value={"ok": True, "text": "User-agent: *\nDisallow: /private\n", "transport": "residential_proxy"},
        ):
            result = evaluate_completed_sports_robots(candidate)
        self.assertTrue(result["robots_checked"])
        self.assertTrue(result["robots_disallows_target_path"])
        self.assertEqual(result["robots_decision"], "block")


if __name__ == "__main__":
    unittest.main()

