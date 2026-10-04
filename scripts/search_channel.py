"""
Telegram Channel Search & Download Utility (Template)
Requires: telethon, python-dotenv
Install: pip install telethon python-dotenv
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / ".env"
SEARCH_RESULTS_DIR = BASE_DIR / "searches" / "results"
DOWNLOADS_DIR = BASE_DIR / "files" / "downloads"

load_dotenv(dotenv_path=CONFIG_PATH)

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = str(BASE_DIR / "config" / "telegram_user")

async def search_channel(channel_username: str, query: str, limit: int = 50, download_media: bool = False):
    """
    Search messages in a channel and optionally download media files.
    """
    if not API_ID or not API_HASH:
        print("[!] Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in config/.env")
        return

    try:
        from telethon import TelegramClient
    except ImportError:
        print("[!] telethon not installed. Run: pip install telethon python-dotenv")
        return

    async with TelegramClient(SESSION_NAME, int(API_ID), API_HASH) as client:
        print(f"[*] Searching '{query}' in {channel_username} (max {limit} messages)...")
        results = []
        async for message in client.iter_messages(channel_username, search=query, limit=limit):
            msg_data = {
                "id": message.id,
                "date": message.date.isoformat() if message.date else None,
                "text": message.text,
                "sender_id": message.sender_id,
                "has_media": bool(message.media),
            }
            results.append(msg_data)

            if download_media and message.media:
                file_path = await message.download_media(file=DOWNLOADS_DIR)
                print(f"[+] Downloaded: {file_path}")
                msg_data["downloaded_file"] = str(file_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_channel = channel_username.replace("@", "").replace("/", "_")
        output_file = SEARCH_RESULTS_DIR / f"{sanitized_channel}_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"[+] Search complete. Found {len(results)} matches.")
        print(f"[+] Results saved to: {output_file}")

if __name__ == "__main__":
    # Example usage:
    # asyncio.run(search_channel("@example_channel", query="python", limit=20, download_media=False))
    print("Telegram Channel Search Template")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Config file expected at: {CONFIG_PATH}")
