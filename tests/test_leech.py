"""
Unit Tests for Leech Downloader and Progress Bar Calculations
"""

import unittest
from leech.downloader import (
    is_iranian_target, parse_filename, make_progress_bar, format_eta
)

class TestLeech(unittest.TestCase):
    def test_is_iranian_target(self):
        self.assertTrue(is_iranian_target("https://edge17.111.ir.cdn.ir/dl/file.rar"))
        self.assertTrue(is_iranian_target("https://downloadly.ir/software/utility.zip"))
        self.assertTrue(is_iranian_target("https://soft98.ir/os/windows.iso"))
        self.assertFalse(is_iranian_target("https://github.com/user/repo/archive.zip"))
        self.assertFalse(is_iranian_target("https://google.com/test.bin"))

    def test_parse_filename(self):
        url = "https://speed.hetzner.de/100MB.bin"
        self.assertEqual(parse_filename(url), "100MB.bin")

        disposition = 'attachment; filename="Python_Course_2026.zip"'
        self.assertEqual(parse_filename("https://site.com/get?id=123", disposition), "Python_Course_2026.zip")

        disposition_utf8 = "attachment; filename*=UTF-8''Revit_2025_Setup.exe"
        self.assertEqual(parse_filename("https://site.com/dl", disposition_utf8), "Revit_2025_Setup.exe")

    def test_make_progress_bar(self):
        bar_0 = make_progress_bar(0.0)
        self.assertIn("[░░░░░░░░░░]", bar_0)
        self.assertIn("0.0%", bar_0)

        bar_50 = make_progress_bar(50.0)
        self.assertIn("[█████░░░░░]", bar_50)
        self.assertIn("50.0%", bar_50)

        bar_100 = make_progress_bar(100.0)
        self.assertIn("[██████████]", bar_100)
        self.assertIn("100.0%", bar_100)

    def test_format_eta(self):
        self.assertEqual(format_eta(25), "25s")
        self.assertEqual(format_eta(90), "1m 30s")
        self.assertEqual(format_eta(3665), "1h 1m")

if __name__ == "__main__":
    unittest.main()
