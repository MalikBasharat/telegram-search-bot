"""
Search Telegram Global Directory for Subscription-sharing Channels
------------------------------------------------------------------
Uses Telethon user session to search Telegram's global public channel directory
for channels sharing free/discounted subscriptions (OTT, streaming, tools, etc.).
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, functions, types

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
RESULTS_DIR = BASE_DIR / "searches" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = CONFIG_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
load_dotenv(BASE_DIR / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

SEARCH_KEYWORDS = [
    "subscriptions",
    "free subscriptions",
    "premium accounts",
    "shared subscriptions",
    "ott subscriptions",
    "subscription giveaways",
    "netflix accounts",
    "spotify premium",
    "canva pro team",
    "chatgpt premium",
    "vpn accounts",
    "free accounts",
    "premium cookies",
]

async def search_channels():
    if not API_ID or not API_HASH:
        print("[!] Error: TELEGRAM_API_ID and TELEGRAM_API_HASH missing.")
        return

    session_path = str(CONFIG_DIR / "user_session")
    client = TelegramClient(session_path, int(API_ID), API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("[!] User session not authorized. Please run login_user.py first.")
            return

        print("[+] User session connected successfully.")
        all_channels = {}

        for kw in SEARCH_KEYWORDS:
            try:
                res = await client(functions.contacts.SearchRequest(q=kw, limit=20))
                chats = getattr(res, "chats", [])
                for chat in chats:
                    username = getattr(chat, "username", None)
                    title = getattr(chat, "title", "Unknown")
                    chat_id = getattr(chat, "id", None)
                    participants_count = getattr(chat, "participants_count", None)

                    if username:
                        key = username.lower()
                        if key not in all_channels:
                            all_channels[key] = {
                                "title": title,
                                "username": username,
                                "id": chat_id,
                                "participants_count": participants_count,
                                "link": f"https://t.me/{username}",
                                "matched_keywords": [kw],
                            }
                        else:
                            if kw not in all_channels[key]["matched_keywords"]:
                                all_channels[key]["matched_keywords"].append(kw)
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"[!] Search failed for '{kw}': {e}")

        channel_list = list(all_channels.values())
        print(f"\n[+] Total unique channels found: {len(channel_list)}")

        output_file = RESULTS_DIR / "subscription_channels.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(channel_list, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved results to: {output_file}")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(search_channels())

