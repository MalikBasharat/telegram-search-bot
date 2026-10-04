"""
Background Telegram Channel Crawler
-----------------------------------
Crawls historical messages, catches FloodWait errors,
and indexes real-time uploads from monitored channels into SQLite.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChannelPrivateError, ChatAdminRequiredError

from db.database import (
    upsert_file, add_channel, get_channels, update_channel_cursor
)
from crawler.parser import extract_file_metadata

logger = logging.getLogger("crawler")
logger.setLevel(logging.INFO)

class ChannelCrawler:
    def __init__(self, client: TelegramClient, channels_file: Optional[Path] = None):
        self.client = client
        self.channels_file = channels_file
        self.is_running = False

    def load_channels_from_file(self) -> List[str]:
        if not self.channels_file or not self.channels_file.exists():
            return []
        with open(self.channels_file, "r", encoding="utf-8") as f:
            return [
                line.strip().replace("https://t.me/", "").replace("@", "")
                for line in f
                if line.strip() and not line.startswith("#")
            ]

    async def sync_channel_list(self):
        """Populates channels table with entries from channels.txt."""
        file_channels = self.load_channels_from_file()
        for ch in file_channels:
            add_channel(ch)

    async def backfill_channel(self, channel_username: str, limit: int = 150):
        """
        Crawls channel messages since last_message_id up to limit.
        """
        clean_ch = channel_username.strip().replace("@", "").replace("https://t.me/", "")
        logger.info(f"[*] Starting crawl for @{clean_ch} (limit: {limit})...")
        
        # Check current cursor
        channels_in_db = {c["username"]: c["last_message_id"] for c in get_channels()}
        min_id = channels_in_db.get(clean_ch, 0)
        
        new_files_count = 0
        highest_id = min_id

        try:
            async for msg in self.client.iter_messages(clean_ch, limit=limit, min_id=min_id):
                if msg.id > highest_id:
                    highest_id = msg.id

                metadata = extract_file_metadata(msg, clean_ch)
                if metadata:
                    if upsert_file(metadata):
                        new_files_count += 1
                        logger.debug(f"[+] Indexed: {metadata['file_name']} from @{clean_ch}")

                # Gentle pacing to prevent flood-wait
                await asyncio.sleep(0.05)

        except FloodWaitError as e:
            logger.warning(f"[!] FloodWait on @{clean_ch}: sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
        except (ChannelPrivateError, ChatAdminRequiredError) as e:
            logger.warning(f"[!] Cannot access @{clean_ch}: {e}")
            return 0
        except Exception as e:
            logger.error(f"[!] Error crawling @{clean_ch}: {e}")
            return 0

        if highest_id > min_id:
            update_channel_cursor(clean_ch, highest_id)

        logger.info(f"[+] Finished crawl for @{clean_ch}. Indexed {new_files_count} new file(s).")
        return new_files_count

    def register_realtime_listener(self):
        """Registers listener to index files uploaded in real-time."""
        @self.client.on(events.NewMessage)
        async def new_message_handler(event):
            try:
                chat = await event.get_chat()
                username = getattr(chat, 'username', None)
                if not username:
                    return

                # Check if chat is monitored
                monitored = {c["username"].lower() for c in get_channels()}
                if username.lower() not in monitored:
                    return

                metadata = extract_file_metadata(event.message, username)
                if metadata:
                    if upsert_file(metadata):
                        logger.info(f"[+] Real-time file indexed: {metadata['file_name']} from @{username}")
                    update_channel_cursor(username, event.message.id)
            except Exception as e:
                logger.error(f"[!] Error in real-time message handler: {e}")

    async def run_crawler_loop(self, poll_interval: int = 300):
        """Runs initial sync and continuous periodic polling."""
        self.is_running = True
        await self.sync_channel_list()
        self.register_realtime_listener()

        while self.is_running:
            channels = get_channels()
            for ch_entry in channels:
                if not self.is_running:
                    break
                await self.backfill_channel(ch_entry["username"])
                await asyncio.sleep(2)  # pause between channels

            logger.info(f"[*] Crawl cycle complete. Next cycle in {poll_interval}s.")
            try:
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                self.is_running = False
                break
