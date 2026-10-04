"""
Unit Tests for Crawler Parser & Media Categorization
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock
from telethon.tl import types
from crawler.parser import format_size, categorize_media, extract_file_metadata

class TestParser(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1048576 * 15), "15.0 MB")
        self.assertEqual(format_size(1073741824 * 2.5), "2.5 GB")

    def test_categorize_media(self):
        self.assertEqual(categorize_media("app-release.apk"), "apk")
        self.assertEqual(categorize_media("setup.exe"), "apk")
        self.assertEqual(categorize_media("movie.mkv"), "video")
        self.assertEqual(categorize_media("clip.mp4", has_video=True), "video")
        self.assertEqual(categorize_media("song.flac", has_audio=True), "audio")
        self.assertEqual(categorize_media("wallpaper.png", has_photo=True), "image")
        self.assertEqual(categorize_media("report.pdf"), "document")
        self.assertEqual(categorize_media("archive.zip"), "document")

    def test_extract_file_metadata_document(self):
        msg = MagicMock()
        msg.id = 42
        msg.media = True
        msg.video = None
        msg.audio = None
        msg.photo = None
        msg.text = "Here is the new Python cheat sheet"
        msg.date = datetime(2026, 10, 4, 12, 0, 0)

        doc = MagicMock()
        doc.size = 2048000
        attr = types.DocumentAttributeFilename(file_name="Python_Cheatsheet.pdf")
        doc.attributes = [attr]
        msg.document = doc

        meta = extract_file_metadata(msg, "python_resources")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["file_name"], "Python_Cheatsheet.pdf")
        self.assertEqual(meta["file_size"], 2048000)
        self.assertEqual(meta["media_type"], "document")
        self.assertEqual(meta["channel_username"], "python_resources")
        self.assertEqual(meta["message_link"], "https://t.me/python_resources/42")

    def test_extract_file_metadata_no_media(self):
        msg = MagicMock()
        msg.media = None
        self.assertIsNone(extract_file_metadata(msg, "some_channel"))

if __name__ == "__main__":
    unittest.main()
