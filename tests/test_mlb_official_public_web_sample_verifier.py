import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import build_mlb_official_public_web_sample_verification_report


class TestMlbOfficialPublicWebSampleVerifier(unittest.TestCase):
    def test_report_confirms_page_and_pdf_headers(self):
        report = build_mlb_official_public_web_sample_verification_report(
            fetch_text_fn=lambda url: "<html><body>Media Guide</body></html>",
            fetch_bytes_fn=lambda url: b"%PDF-1.7 sample pdf bytes",
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["report_name"], "MLB_OFFICIAL_PUBLIC_WEB_SAMPLE_VERIFICATION_REPORT")
        self.assertTrue(report["page_contains_media_guide"])
        self.assertTrue(report["pdf_header_is_pdf"])


if __name__ == "__main__":
    unittest.main()
