"""
Telegram Bot Command Handlers & Interactive UI
----------------------------------------------
Implements commands (/search, /doc, /video, /apk, /stats, /channels, /syncmychannels,
/findchannels, /addchannel, /allow, /download) with inline keyboard pagination
and native Telegram bot command menu popup.
"""

import os
import math
import logging
from pathlib import Path
from typing import List, Optional
from telethon import TelegramClient, events, Button, functions, types
from db.database import (
    search_files, get_recent_files, get_file_by_id, get_stats,
    add_channel, get_channels, is_whitelisted, add_whitelist, upsert_file
)
from crawler.parser import format_size, categorize_media
from leech.downloader import download_file, format_eta, is_iranian_target

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

PAGE_SIZE = 8

async def setup_commands_menu(bot_client: TelegramClient):
    """Registers native '/' command suggestions popup with Telegram."""
    commands = [
        types.BotCommand(command="leech", description="Download direct URL & send file (up to 2GB)"),
        types.BotCommand(command="search", description="Search all files (keyword)"),
        types.BotCommand(command="doc", description="Search documents & PDFs"),
        types.BotCommand(command="video", description="Search videos & course files"),
        types.BotCommand(command="apk", description="Search software & APKs"),
        types.BotCommand(command="recent", description="Show newest files"),
        types.BotCommand(command="stats", description="View index statistics"),
        types.BotCommand(command="crawl", description="Run immediate crawler across all channels"),
        types.BotCommand(command="channels", description="List monitored channels"),
        types.BotCommand(command="syncmychannels", description="Import channels from your account"),
        types.BotCommand(command="findchannels", description="Find new channels by keyword"),
        types.BotCommand(command="addchannel", description="Add a channel to monitor"),
        types.BotCommand(command="help", description="Show usage instructions"),
    ]
    try:
        await bot_client(functions.bots.SetBotCommandsRequest(
            scope=types.BotCommandScopeDefault(),
            lang_code="",
            commands=commands
        ))
        logger.info("[+] Telegram '/' popup command menu registered successfully.")
    except Exception as e:
        logger.warning(f"[!] Could not set bot commands menu: {e}")

def build_search_page_text(query: str, results: list, total: int, page: int, total_pages: int, media_type: Optional[str] = None) -> str:
    type_label = f" [{media_type.upper()}]" if media_type else ""
    text = (
        f"🔍 **Search Results for:** `{query}`{type_label}\n"
        f"📊 **Found:** {total} file(s) | **Page:** {page}/{total_pages}\n"
        f"────────────────────────\n\n"
    )
    for idx, r in enumerate(results, 1):
        num = (page - 1) * PAGE_SIZE + idx
        name = r["file_name"]
        size_str = format_size(r["file_size"])
        ch = r["channel_username"]
        fid = r["id"]
        link = r.get("message_link") or f"https://t.me/{ch}/{r['message_id']}"
        text += (
            f"**{num}. [{name}]({link})**\n"
            f"   📦 `{size_str}` | 📢 @{ch} | ⚡ /get_{fid}\n\n"
        )
    return text

def build_pagination_buttons(query: str, page: int, total_pages: int, media_type: Optional[str] = None) -> list:
    buttons = []
    nav_row = []
    safe_mtype = media_type or "all"

    # Previous page button
    if page > 1:
        prev_offset = (page - 2) * PAGE_SIZE
        nav_row.append(Button.inline("⬅️ Prev", data=f"p:{safe_mtype}:{prev_offset}:{query[:20]}"))
    else:
        nav_row.append(Button.inline("⬅️ Prev", data="noop"))

    # Page indicator
    nav_row.append(Button.inline(f"{page}/{total_pages}", data="noop"))

    # Next page button
    if page < total_pages:
        next_offset = page * PAGE_SIZE
        nav_row.append(Button.inline("Next ➡️", data=f"p:{safe_mtype}:{next_offset}:{query[:20]}"))
    else:
        nav_row.append(Button.inline("Next ➡️", data="noop"))

    buttons.append(nav_row)
    return buttons

def register_bot_handlers(
    bot_client: TelegramClient,
    crawler_instance=None,
    user_client: Optional[TelegramClient] = None,
    admin_ids: Optional[List[int]] = None
):
    admins = admin_ids or []

    async def check_access(event) -> bool:
        user_id = event.sender_id
        if is_whitelisted(user_id, admin_ids=admins):
            return True
        await event.reply(
            "⛔ **Access Restricted**\n\n"
            "This bot is restricted to authorized users. Please contact the administrator to grant access."
        )
        return False

    @bot_client.on(events.NewMessage(pattern=r"^/start$|^/help$"))
    async def help_handler(event):
        if not await check_access(event):
            return
        channels = get_channels()
        stats = get_stats()
        text = (
            "🤖 **Telegram File Search Bot**\n\n"
            "Search across indexed channels for files, documents, videos, and APKs.\n\n"
            "**Search Commands:**\n"
            "• `/search <keyword>` — Search all indexed files\n"
            "• `/doc <keyword>` — Filter to documents & archives\n"
            "• `/video <keyword>` — Filter to video files\n"
            "• `/apk <keyword>` — Filter to Android/software packages\n"
            "• `/recent` — Show 10 most recently indexed files\n"
            "• `/get_<id>` — Instantly receive/forward a file\n\n"
            "**Channel Discovery & Management:**\n"
            "• `/syncmychannels` — Import all channels joined by your Telegram account\n"
            "• `/findchannels <keyword>` — Search Telegram directory for public channels\n"
            "• `/addchannel @username` — Add a channel to monitor\n"
            "• `/channels` — List currently monitored channels\n"
            "• `/stats` — Show database & indexed metrics\n"
        )
        if event.sender_id in admins:
            text += "• `/allow <user_id>` — Whitelist a new user\n"

        text += (
            f"\n📊 **Current Index:** {stats['total_files']} files across {len(channels)} channels."
        )
        await event.reply(text)

    @bot_client.on(events.NewMessage(pattern=r"^/channels$"))
    async def list_channels_handler(event):
        if not await check_access(event):
            return
        channels = get_channels()
        if not channels:
            await event.reply("📁 No channels configured yet. Use `/addchannel @username` to add one.")
            return
        ch_list = "\n".join([f"• @{c['username']} (Last ID: `{c['last_message_id']}`)" for c in channels])
        await event.reply(f"📁 **Monitored Channels ({len(channels)}):**\n\n{ch_list}")

    @bot_client.on(events.NewMessage(pattern=r"^/stats$"))
    async def stats_handler(event):
        if not await check_access(event):
            return
        stats = get_stats()
        total_size = format_size(stats["total_bytes"])
        db_size = format_size(stats["db_size_bytes"])
        text = (
            "📈 **Search Engine Index Stats**\n\n"
            f"• **Indexed Files:** `{stats['total_files']}`\n"
            f"• **Total Indexed Media Volume:** `{total_size}`\n"
            f"• **Monitored Channels:** `{stats['total_channels']}`\n"
            f"• **Database Size:** `{db_size}` (SQLite FTS5)\n"
        )
        await event.reply(text)

    @bot_client.on(events.NewMessage(pattern=r"^/recent$"))
    async def recent_handler(event):
        if not await check_access(event):
            return
        recent = get_recent_files(limit=10)
        if not recent:
            await event.reply("ℹ️ No files indexed yet. Run crawler to populate.")
            return
        text = "🕒 **Recently Indexed Files:**\n\n"
        for idx, r in enumerate(recent, 1):
            size_str = format_size(r["file_size"])
            link = r.get("message_link") or f"https://t.me/{r['channel_username']}/{r['message_id']}"
            text += f"**{idx}. [{r['file_name']}]({link})**\n   📦 `{size_str}` | @{r['channel_username']} | /get_{r['id']}\n\n"
        await event.reply(text, link_preview=False)

    @bot_client.on(events.NewMessage(pattern=r"^/(search|doc|video|apk)(\s+.*)?$"))
    async def search_handler(event):
        if not await check_access(event):
            return
        cmd = event.pattern_match.group(1)
        raw_query = event.pattern_match.group(2)
        if not raw_query or not raw_query.strip():
            await event.reply(f"💡 Usage: `/{cmd} <keyword>`\nExample: `/{cmd} python`")
            return

        query = raw_query.strip()
        media_type = None
        if cmd == "doc":
            media_type = "document"
        elif cmd == "video":
            media_type = "video"
        elif cmd == "apk":
            media_type = "apk"

        results, total = search_files(query, media_type=media_type, limit=PAGE_SIZE, offset=0)
        if total == 0:
            stats = get_stats()
            if stats["total_files"] == 0:
                await event.reply(
                    f"❌ No files found matching `{query}`.\n\n"
                    "⚠️ **Notice: Database index is currently empty (0 files).**\n\n"
                    "**To start indexing files:**\n"
                    "• `/syncmychannels` — Import & index channels joined by your Telegram account\n"
                    "• `/crawl` — Force-crawl all monitored channels right now\n"
                    "• `/addchannel @username` — Add a specific channel to monitor"
                )
            else:
                await event.reply(f"❌ No files found matching `{query}`.\n\n💡 Try broader keywords or check `/recent`.")
            return

        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        text = build_search_page_text(query, results, total, 1, total_pages, media_type=media_type)
        buttons = build_pagination_buttons(query, 1, total_pages, media_type=media_type) if total_pages > 1 else None

        await event.reply(text, buttons=buttons, link_preview=False)

    @bot_client.on(events.CallbackQuery(pattern=r"^p:(all|document|video|apk):(\d+):(.*)$"))
    async def pagination_callback(event):
        raw_mtype = event.pattern_match.group(1).decode("utf-8")
        offset = int(event.pattern_match.group(2).decode("utf-8"))
        query = event.pattern_match.group(3).decode("utf-8")

        media_type = None if raw_mtype == "all" else raw_mtype
        page = (offset // PAGE_SIZE) + 1

        results, total = search_files(query, media_type=media_type, limit=PAGE_SIZE, offset=offset)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        text = build_search_page_text(query, results, total, page, total_pages, media_type=media_type)
        buttons = build_pagination_buttons(query, page, total_pages, media_type=media_type)

        await event.edit(text, buttons=buttons, link_preview=False)
        await event.answer()

    @bot_client.on(events.CallbackQuery(pattern=r"^noop$"))
    async def noop_callback(event):
        await event.answer()

    @bot_client.on(events.NewMessage(pattern=r"^/crawl$"))
    async def crawl_now_handler(event):
        if not await check_access(event):
            return
        if not crawler_instance:
            await event.reply("❌ Crawler instance not initialized.")
            return

        status_msg = await event.reply("🚀 **Triggering manual crawl across all monitored channels...**")
        channels = get_channels()
        if not channels:
            await status_msg.edit("📁 No channels configured. Add one with `/addchannel @username` or `/syncmychannels`.")
            return

        total_new = 0
        for idx, ch in enumerate(channels, 1):
            ch_name = ch["username"]
            await status_msg.edit(f"⏳ [{idx}/{len(channels)}] Crawling **@{ch_name}**...")
            try:
                count = await crawler_instance.backfill_channel(ch_name, limit=60)
                total_new += (count or 0)
            except Exception as e:
                logger.error(f"Error crawling @{ch_name}: {e}")
            await asyncio.sleep(1)

        stats = get_stats()
        await status_msg.edit(
            f"✅ **Crawl Complete!**\n\n"
            f"• **New Files Indexed:** `{total_new}`\n"
            f"• **Total Library:** `{stats['total_files']}` files across {len(channels)} channels.\n\n"
            f"👉 Search your files with `/search <keyword>` or view `/recent`."
        )

    @bot_client.on(events.NewMessage(pattern=r"^/syncmychannels$"))
    async def sync_my_channels_handler(event):
        """Scans user account dialogs and adds joined channels to the crawler."""
        if not await check_access(event):
            return
        if not user_client:
            await event.reply("⚠️ User client is not connected in the backend.")
            return

        status_msg = await event.reply("⏳ Scanning your Telegram account for joined channels and groups...")
        imported = []
        try:
            import asyncio
            async for dialog in user_client.iter_dialogs():
                if dialog.is_channel or dialog.is_group:
                    username = getattr(dialog.entity, 'username', None)
                    if username:
                        clean = username.strip().replace("@", "")
                        add_channel(clean, title=dialog.title)
                        imported.append(f"• **{dialog.title}** (@{clean})")
                        if crawler_instance:
                            asyncio.create_task(crawler_instance.backfill_channel(clean, limit=40))

            if imported:
                text = f"✅ **Imported {len(imported)} Channels from your Account:**\n\n" + "\n".join(imported[:12])
                if len(imported) > 12:
                    text += f"\n\n_...and {len(imported) - 12} more channels queued for crawling!_"
                await status_msg.edit(text)
            else:
                await status_msg.edit("ℹ️ No public channels with usernames found in your joined chats.")
        except Exception as e:
            await status_msg.edit(f"❌ Error scanning your channels: {e}")

    @bot_client.on(events.NewMessage(pattern=r"^/findchannels(\s+.*)?$"))
    async def find_channels_handler(event):
        """Discovers public channels using global Telegram search."""
        if not await check_access(event):
            return
        raw_query = event.pattern_match.group(1)
        if not raw_query or not raw_query.strip():
            await event.reply("💡 Usage: `/findchannels <keyword>`\nExample: `/findchannels python courses`")
            return

        query = raw_query.strip()
        if not user_client:
            await event.reply("⚠️ User client is required to search the global Telegram directory.")
            return

        status_msg = await event.reply(f"🔎 Searching Telegram directory for `{query}`...")
        try:
            search_res = await user_client(functions.contacts.SearchRequest(q=query, limit=10))
            chats = getattr(search_res, 'chats', [])
            if not chats:
                await status_msg.edit(f"❌ No public channels found matching `{query}`.")
                return

            text = f"🌐 **Telegram Channels Matching `{query}`:**\n\n"
            found_count = 0
            for c in chats:
                username = getattr(c, 'username', None)
                title = getattr(c, 'title', 'Channel')
                if username:
                    found_count += 1
                    text += f"**{found_count}. {title}** (@{username})\n   👉 Add to bot: `/addchannel @{username}`\n\n"

            if found_count == 0:
                await status_msg.edit(f"❌ No public channels with usernames found for `{query}`.")
            else:
                await status_msg.edit(text)
        except Exception as e:
            await status_msg.edit(f"❌ Search error: {e}")

    @bot_client.on(events.NewMessage(pattern=r"^/addchannel\s+(@?[\w\d_\-\/]+)$"))
    async def add_channel_handler(event):
        if not await check_access(event):
            return
        target = event.pattern_match.group(1).strip()
        clean = target.replace("@", "").replace("https://t.me/", "")
        add_channel(clean)
        
        status_msg = await event.reply(f"✅ Added **@{clean}** to monitored channels.")
        
        if crawler_instance:
            import asyncio
            asyncio.create_task(crawler_instance.backfill_channel(clean))
            await status_msg.edit(f"✅ Added **@{clean}**. Background crawling and indexing started!")

    @bot_client.on(events.NewMessage(pattern=r"^/allow\s+(\d+)$"))
    async def allow_user_handler(event):
        if event.sender_id not in admins:
            await event.reply("⛔ Admin only command.")
            return
        target_uid = int(event.pattern_match.group(1).strip())
        add_whitelist(target_uid, added_by=event.sender_id)
        await event.reply(f"✅ User ID `{target_uid}` is now authorized to use this bot.")

    @bot_client.on(events.NewMessage(pattern=r"^/(?:download|get)_?(\d+)$"))
    async def download_handler(event):
        if not await check_access(event):
            return
        file_id = int(event.pattern_match.group(1))
        file_info = get_file_by_id(file_id)
        if not file_info:
            await event.reply("❌ File not found in database index.")
            return

        ch = file_info["channel_username"]
        msg_id = file_info["message_id"]
        fname = file_info["file_name"]

        try:
            # Deliver via instant zero-bandwidth message forward
            await bot_client.forward_messages(event.chat_id, msg_id, ch)
            logger.info(f"[+] Forwarded file {fname} from @{ch}:{msg_id} to user {event.sender_id}")
        except Exception as e:
            logger.warning(f"[!] Forward failed for {fname}: {e}")
            link = file_info.get("message_link") or f"https://t.me/{ch}/{msg_id}"
            await event.reply(
                f"⚠️ Cloud forward failed (channel may have restricted forwarding).\n\n"
                f"🔗 Direct Link: [{fname}]({link})\n"
                f"Error details: `{e}`"
            )

    @bot_client.on(events.NewMessage(pattern=r"^/(?:leech|mirror)(\s+.*)?$"))
    async def leech_handler(event):
        if not await check_access(event):
            return
        raw_url = (event.pattern_match.group(1) or "").strip()
        if not raw_url:
            await event.reply(
                "💡 **Usage:** `/leech <direct_url>`\n\n"
                "**Examples:**\n"
                "• `/leech https://example.com/Python_Course.zip`\n"
                "• `/leech https://edge17.111.ir.cdn.ir/dl/.../Revit.part1.rar`\n\n"
                "*(Downloads file, uploads directly to chat up to 2GB, and indexes into `/search`)*"
            )
            return

        if not raw_url.startswith(("http://", "https://")):
            await event.reply("❌ Invalid URL. Please provide a link starting with `http://` or `https://`.")
            return

        status_msg = await event.reply("⏳ **Connecting to target server...**")
        downloads_dir = Path(__file__).resolve().parent.parent / "files" / "downloads"

        async def progress_cb(p):
            text = (
                f"📥 **Downloading:** `{p['file_name']}`\n"
                f"{p['bar']}\n"
                f"📊 `{format_size(p['downloaded'])}` / `{format_size(p['total'])}`\n"
                f"⚡ **Speed:** `{format_size(int(p['speed']))}/s` | ⏱️ **ETA:** `{format_eta(p['eta'])}`\n"
            )
            if p.get("is_iranian"):
                text += "🇮🇷 _(Iranian CDN detected — bypass headers applied)_\n"
            try:
                await status_msg.edit(text)
            except Exception:
                pass

        iran_proxy = os.getenv("IRAN_PROXY")

        try:
            result = await download_file(
                raw_url,
                dest_dir=downloads_dir,
                progress_callback=progress_cb,
                iran_proxy=iran_proxy
            )
            file_path = result["file_path"]
            file_name = result["file_name"]
            file_size = result["file_size"]
            size_str = format_size(file_size)

            await status_msg.edit(
                f"📦 **Downloaded:** `{file_name}` ({size_str})\n"
                f"📤 **Uploading to Telegram now...**\n"
                f"_Please wait, sending file directly to your chat..._"
            )

            # Upload via user_client (supports up to 2GB) or bot_client
            sender_client = user_client if (user_client and await user_client.is_user_authorized()) else bot_client

            caption = f"📁 **{file_name}**\n📊 `{size_str}`\n🔗 Source: `{raw_url[:60]}...`"
            uploaded_msg = await sender_client.send_file(
                event.chat_id,
                file=str(file_path),
                caption=caption,
                force_document=True
            )

            # Auto-index into SQLite FTS5 database
            metadata = {
                "channel_username": "leeched_files",
                "message_id": uploaded_msg.id,
                "file_name": file_name,
                "file_size": file_size,
                "media_type": categorize_media(file_name),
                "date": uploaded_msg.date.isoformat() if uploaded_msg.date else None,
                "caption": caption,
                "message_link": None
            }
            upsert_file(metadata)

            # Cleanup local file to prevent disk exhaustion
            keep_local = os.getenv("KEEP_LOCAL_COPY", "false").lower() in ("true", "1")
            if not keep_local:
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass

            await status_msg.edit(
                f"✅ **Leech Complete!**\n"
                f"📁 `{file_name}` ({size_str}) delivered and indexed into `/search`."
            )

        except Exception as e:
            logger.error(f"Leech error for {raw_url}: {e}")
            error_text = f"❌ **Leech Failed:** `{e}`"
            if is_iranian_target(raw_url) and not iran_proxy:
                error_text += (
                    "\n\n🇮🇷 **Iranian CDN Geoblock Detected:**\n"
                    "This URL is on an Iranian CDN (`111.ir.cdn.ir`). To bypass foreign IP blocks, "
                    "add an Iranian proxy in `config/.env` (`IRAN_PROXY=socks5://...`), or paste the link into Seedr/Real-Debrid."
                )
            await status_msg.edit(error_text)

