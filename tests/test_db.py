"""
Unit Tests for Database & FTS5 Index Engine
"""

import unittest
import tempfile
from pathlib import Path
from db.database import (
    init_db, upsert_file, search_files, get_recent_files,
    get_stats, add_channel, get_channels, update_channel_cursor,
    is_whitelisted, add_whitelist
)

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_index.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upsert_and_deduplication(self):
        file_item = {
            "channel_username": "test_channel",
            "message_id": 101,
            "file_name": "python_guide.pdf",
            "file_size": 2048576,
            "media_type": "document",
            "date": "2026-10-04T00:00:00",
            "caption": "Comprehensive Python reference manual",
            "message_link": "https://t.me/test_channel/101"
        }
        # First insert -> True
        self.assertTrue(upsert_file(file_item, self.db_path))

        # Duplicate insert -> False
        self.assertFalse(upsert_file(file_item, self.db_path))

        # Total files in stats should be 1
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_files"], 1)
        self.assertEqual(stats["total_bytes"], 2048576)

    def test_fts5_search_and_pagination(self):
        files = [
            {
                "channel_username": "dev_channel",
                "message_id": 1,
                "file_name": "Learn_FastAPI_Framework.pdf",
                "file_size": 1024,
                "media_type": "document",
                "date": "2026-10-01",
                "caption": "Python Web API tutorial",
                "message_link": "https://t.me/dev_channel/1"
            },
            {
                "channel_username": "dev_channel",
                "message_id": 2,
                "file_name": "React_Components_Guide.zip",
                "file_size": 512,
                "media_type": "document",
                "date": "2026-10-02",
                "caption": "Frontend modern javascript",
                "message_link": "https://t.me/dev_channel/2"
            },
            {
                "channel_username": "video_channel",
                "message_id": 3,
                "file_name": "FastAPI_Video_Course.mp4",
                "file_size": 5000000,
                "media_type": "video",
                "date": "2026-10-03",
                "caption": "Building asynchronous APIs in Python",
                "message_link": "https://t.me/video_channel/3"
            }
        ]
        for f in files:
            upsert_file(f, self.db_path)

        # Search for "FastAPI"
        results, total = search_files("FastAPI", limit=10, offset=0, db_path=self.db_path)
        self.assertEqual(total, 2)
        self.assertEqual(len(results), 2)

        # Filter by media_type="video"
        results, total = search_files("FastAPI", media_type="video", limit=10, offset=0, db_path=self.db_path)
        self.assertEqual(total, 1)
        self.assertEqual(results[0]["file_name"], "FastAPI_Video_Course.mp4")

        # Search for "python" across filename and caption
        results, total = search_files("python", limit=10, offset=0, db_path=self.db_path)
        self.assertEqual(total, 2)

    def test_whitelist_access(self):
        admin_id = 999999
        normal_user_id = 111111

        # Admin is always whitelisted
        self.assertTrue(is_whitelisted(admin_id, admin_ids=[admin_id], db_path=self.db_path))

        # Normal user is not whitelisted initially
        self.assertFalse(is_whitelisted(normal_user_id, admin_ids=[admin_id], db_path=self.db_path))

        # Add user to whitelist
        self.assertTrue(add_whitelist(normal_user_id, username="alice", added_by=admin_id, db_path=self.db_path))

        # Now normal user is whitelisted
        self.assertTrue(is_whitelisted(normal_user_id, admin_ids=[admin_id], db_path=self.db_path))

    def test_channel_cursor(self):
        add_channel("chinawenhua", "Chinese Animation Channel", self.db_path)
        channels = get_channels(self.db_path)
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]["username"], "chinawenhua")
        self.assertEqual(channels[0]["last_message_id"], 0)

        # Update cursor
        update_channel_cursor("chinawenhua", 500, self.db_path)
        channels = get_channels(self.db_path)
        self.assertEqual(channels[0]["last_message_id"], 500)

        # Out of order smaller ID does not decrease cursor
        update_channel_cursor("chinawenhua", 300, self.db_path)
        channels = get_channels(self.db_path)
        self.assertEqual(channels[0]["last_message_id"], 500)

if __name__ == "__main__":
    unittest.main()
