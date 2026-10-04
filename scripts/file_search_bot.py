"""
Telegram File Search Bot
-------------------------
A Telethon-powered Telegram bot and search engine that allows searching for files 
(documents, videos, audio, archives) across target channels or globally.

Prerequisites:
1. Fill config/.env with:
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_BOT_TOKEN=your_bot_token (from @BotFather)
   # Optional: if searching as user (can access private channels you joined):
   TELEGRAM_PHONE_NUMBER=+1234567890

Run with:
   py scripts/file_search_bot.py
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, events, types

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / ".env"
SEARCH_RESULTS_DIR = BASE_DIR / "searches" / "results"
DOWNLOADS_DIR = BASE_DIR / "files" / "downloads"
CHANNELS_LIST_PATH = BASE_DIR / "searches" / "queries" / "channels.txt"

SEARCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

if CONFIG_PATH.exists():
    load_dotenv(dotenv_path=CONFIG_PATH)
load_dotenv(dotenv_path=BASE_DIR / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_target_channels():
    """Load target channels from searches/queries/channels.txt"""
    if not CHANNELS_LIST_PATH.exists():
        return []
    with open(CHANNELS_LIST_PATH, "r", encoding="utf-8") as f:
        channels = [
            line.strip().replace("https://t.me/", "").replace("@", "")
            for line in f
            if line.strip() and not line.startswith("#")
        ]
    return channels

def format_size(size_bytes):
    """Format bytes into human-readable string"""
    if not size_bytes:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

async def search_files_in_channels(client, channels, query, limit=20, file_type=None):
    """
    Search for files matching query across given channels.
    file_type: 'document', 'video', 'audio', or None for all
    """
    all_results = []
    
    # Select filter
    filter_type = None
    if file_type == "document":
        filter_type = types.InputMessagesFilterDocument
    elif file_type == "video":
        filter_type = types.InputMessagesFilterVideo
    elif file_type == "audio":
        filter_type = types.InputMessagesFilterMusic

    for ch in channels:
        try:
            print(f"[*] Searching '{query}' in @{ch}...")
            count = 0
            async for msg in client.iter_messages(ch, search=query, filter=filter_type, limit=limit):
                if not msg.media:
                    continue

                # Extract file details
                file_name = "Unnamed File"
                file_size = 0
                media_type = "media"

                if msg.document:
                    file_size = msg.document.size
                    media_type = "document"
                    for attr in msg.document.attributes:
                        if isinstance(attr, types.DocumentAttributeFilename):
                            file_name = attr.file_name
                            break
                elif msg.video:
                    file_size = msg.video.size
                    media_type = "video"
                    file_name = f"video_{msg.id}.mp4"

                result_item = {
                    "channel": ch,
                    "message_id": msg.id,
                    "file_name": file_name,
                    "size": file_size,
                    "size_str": format_size(file_size),
                    "media_type": media_type,
                    "date": msg.date.isoformat() if msg.date else None,
                    "link": f"https://t.me/{ch}/{msg.id}",
                    "caption": (msg.text or "")[:150]
                }
                all_results.append(result_item)
                count += 1
                if count >= limit:
                    break
        except Exception as e:
            print(f"[!] Error searching @{ch}: {e}")

    # Save search result dump
    if all_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '_', '-')).strip()
        out_file = SEARCH_RESULTS_DIR / f"search_{safe_query}_{timestamp}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"[+] Saved results to {out_file}")

    return all_results

async def main():
    if not API_ID or not API_HASH:
        print("[!] Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in config/.env")
        print("    Get your API credentials at: https://my.telegram.org/apps")
        return

    session_path = str(BASE_DIR / "config" / "search_bot_session")

    if BOT_TOKEN:
        print("[*] Starting Telegram Bot with BotFather token...")
        client = TelegramClient(session_path, int(API_ID), API_HASH)
        await client.start(bot_token=BOT_TOKEN)

        @client.on(events.NewMessage(pattern=r"^/start"))
        async def start_handler(event):
            channels = get_target_channels()
            ch_list = "\n".join([f"• @{c}" for c in channels]) if channels else "None (add to searches/queries/channels.txt)"
            msg = (
                "🔍 **Telegram File Search Bot**\n\n"
                "**Commands:**\n"
                "• `/search <keyword>` - Search for files in configured channels\n"
                "• `/doc <keyword>` - Search documents (PDFs, ZIP, etc.)\n"
                "• `/video <keyword>` - Search videos\n"
                "• `/channels` - Show configured target channels\n\n"
                f"**Current Channels:**\n{ch_list}"
            )
            await event.reply(msg)

        @client.on(events.NewMessage(pattern=r"^/channels"))
        async def channels_handler(event):
            channels = get_target_channels()
            ch_list = "\n".join([f"• @{c}" for c in channels]) if channels else "None"
            await event.reply(f"📁 **Monitored Channels:**\n\n{ch_list}")

        @client.on(events.NewMessage(pattern=r"^/(search|doc|video)\s+(.+)"))
        async def search_handler(event):
            cmd = event.pattern_match.group(1)
            query = event.pattern_match.group(2).strip()

            file_type = None
            if cmd == "doc":
                file_type = "document"
            elif cmd == "video":
                file_type = "video"

            channels = get_target_channels()
            if not channels:
                await event.reply("⚠️ No target channels configured in `searches/queries/channels.txt`!")
                return

            status_msg = await event.reply(f"🔎 Searching for `{query}` across {len(channels)} channels...")

            results = await search_files_in_channels(client, channels, query, limit=15, file_type=file_type)

            if not results:
                await status_msg.edit(f"❌ No files found matching `{query}`.")
                return

            text_response = f"📁 **Found {len(results)} file(s) for `{query}`:**\n\n"
            for idx, r in enumerate(results[:10], 1):
                text_response += (
                    f"**{idx}. [{r['file_name']}]({r['link']})**\n"
                    f"   📦 Size: `{r['size_str']}` | Channel: @{r['channel']}\n"
                )

            if len(results) > 10:
                text_response += f"\n_...and {len(results) - 10} more results saved to server._"

            await status_msg.edit(text_response, link_preview=False)

        print("[+] Bot is active and listening for messages. Press Ctrl+C to stop.")
        await client.run_until_disconnected()

    else:
        # CLI Mode (Interactive Terminal Search)
        print("[*] BOT_TOKEN not found in config/.env; running in Interactive CLI Mode...")
        client = TelegramClient(session_path, int(API_ID), API_HASH)
        await client.start()

        channels = get_target_channels()
        print(f"[*] Configured channels ({len(channels)}): {channels}")
        query = input("Enter keyword or filename to search: ").strip()
        if query:
            results = await search_files_in_channels(client, channels, query, limit=20)
            print(f"\n[+] Total Results: {len(results)}")
            for idx, r in enumerate(results, 1):
                print(f"{idx}. {r['file_name']} ({r['size_str']}) -> {r['link']}")

if __name__ == "__main__":
    asyncio.run(main())
