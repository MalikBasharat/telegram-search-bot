"""
Telegram File Search & Indexing Engine - Application Entrypoint
--------------------------------------------------------------
Coordinates background crawler worker, SQLite WAL database, and interactive Telegram bot.

Run:
   py -3.12 main.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

from db.database import init_db
from crawler.crawler import ChannelCrawler
from bot.handlers import register_bot_handlers, setup_commands_menu
from server.health import start_health_server

# Configure logging
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("main")

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
ENV_FILE = CONFIG_DIR / ".env"
CHANNELS_FILE = BASE_DIR / "searches" / "queries" / "channels.txt"

def load_admin_ids() -> list:
    raw = os.getenv("ADMIN_USER_IDS", "")
    admins = []
    for item in raw.split(","):
        cleaned = item.strip()
        if cleaned.isdigit():
            admins.append(int(cleaned))
    return admins

async def run_app():
    # Checks config/.env first, then root .env as fallback
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE)
    load_dotenv(dotenv_path=BASE_DIR / ".env")

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    phone_number = os.getenv("TELEGRAM_PHONE_NUMBER")

    if not api_id or not api_hash:
        logger.error("[!] Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in config/.env")
        logger.error("    Obtain your credentials from https://my.telegram.org/apps")
        sys.exit(1)

    # 1. Initialize SQLite database & FTS5 tables
    logger.info("[*] Initializing SQLite WAL database and FTS5 indexes...")
    init_db()

    admin_ids = load_admin_ids()
    logger.info(f"[*] Configured {len(admin_ids)} admin user ID(s): {admin_ids}")

    bot_session = str(CONFIG_DIR / "bot_session")
    user_session = str(CONFIG_DIR / "user_session")

    # 2. Determine architecture mode (Bot vs User Client)
    if bot_token:
        logger.info("[*] Launching in Telegram Bot Mode (BotFather token)...")
        bot_client = TelegramClient(bot_session, int(api_id), api_hash)
        await bot_client.start(bot_token=bot_token)

        crawler_client = bot_client
        user_client = None

        # Check for Cloud StringSession or local session file
        session_string = os.getenv("TELEGRAM_USER_SESSION_STRING", "").strip()
        user_session_file = Path(f"{user_session}.session")

        from server.health import HEALTH_STATUS
        HEALTH_STATUS["has_session_string"] = bool(session_string)

        if session_string:
            try:
                logger.info("[*] Connecting User Client via Cloud StringSession...")
                user_client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
                await user_client.connect()
                if await user_client.is_user_authorized():
                    crawler_client = user_client
                    me_user = await user_client.get_me()
                    HEALTH_STATUS["user_client_authorized"] = True
                    HEALTH_STATUS["user_name"] = getattr(me_user, 'username', me_user.first_name)
                    logger.info(f"[+] User Client connected as {me_user.first_name} (@{me_user.username})!")
                    logger.info("    Cloud crawler has full access to index all public channels.")
                else:
                    logger.warning("[!] StringSession provided but not authorized.")
            except Exception as e:
                logger.warning(f"[!] Could not connect via StringSession: {e}")

        elif user_session_file.exists():
            try:
                logger.info("[*] Connecting authorized User Client for unrestricted channel crawling...")
                user_client = TelegramClient(user_session, int(api_id), api_hash)
                await user_client.connect()
                if await user_client.is_user_authorized():
                    crawler_client = user_client
                    me_user = await user_client.get_me()
                    logger.info(f"[+] User Client connected as {me_user.first_name} (@{me_user.username})!")
                    logger.info("    Crawler now has full access to index all public channels.")
                else:
                    logger.warning("[!] User session file exists but is not authorized.")
            except Exception as e:
                logger.warning(f"[!] Could not connect user client: {e}. Falling back to bot client.")
        elif phone_number:
            try:
                logger.info("[*] Connecting User Client with phone number...")
                user_client = TelegramClient(user_session, int(api_id), api_hash)
                await user_client.start(phone=phone_number)
                crawler_client = user_client
                logger.info("[+] User Client connected successfully!")
            except Exception as e:
                logger.warning(f"[!] Could not start user client: {e}. Falling back to bot client.")
        else:
            logger.warning("[!] NOTICE: No user session found (config/user_session.session or StringSession).")
            logger.warning("    👉 Run 'py -3.12 login_user.py' once to unlock full channel crawling!")

        # Initialize crawler
        crawler = ChannelCrawler(crawler_client, channels_file=CHANNELS_FILE)

        # Register native '/' command menu with Telegram
        await setup_commands_menu(bot_client)

        # Register bot handlers with user_client attached
        register_bot_handlers(bot_client, crawler_instance=crawler, user_client=user_client, admin_ids=admin_ids)

        # Start Cloud Keep-Alive & Healthcheck HTTP server (defaults to 7860 for Hugging Face)
        http_port = int(os.getenv("PORT", 7860))
        await start_health_server(http_port)


        logger.info("==================================================")
        logger.info(f"🚀 Telegram File Search Bot is running 24/7 on port {http_port}!")
        logger.info("   Message your bot on Telegram to start searching.")
        logger.info("==================================================")

        # Run crawler periodic loop and bot listener concurrently
        await asyncio.gather(
            crawler.run_crawler_loop(poll_interval=300),
            bot_client.run_until_disconnected()
        )


    else:
        # CLI / Interactive User Mode
        logger.info("[*] No BOT_TOKEN found. Launching in interactive User Client mode...")
        client = TelegramClient(user_session, int(api_id), api_hash)
        await client.start(phone=phone_number if phone_number else None)

        crawler = ChannelCrawler(client, channels_file=CHANNELS_FILE)
        logger.info("[*] Syncing channels and executing historical crawl...")
        await crawler.sync_channel_list()

        from db.database import get_channels, search_files, get_stats
        channels = get_channels()
        logger.info(f"[*] Found {len(channels)} channel(s). Starting backfill...")
        for ch in channels:
            await crawler.backfill_channel(ch["username"], limit=50)

        stats = get_stats()
        logger.info(f"[+] Total files indexed in SQLite: {stats['total_files']}")

        # Interactive loop
        while True:
            try:
                q = input("\n[Search] Enter keyword or filename to search (or 'q' to quit): ").strip()
                if not q or q.lower() == 'q':
                    break
                results, total = search_files(q, limit=10)
                print(f"\nFound {total} match(es):")
                for idx, r in enumerate(results, 1):
                    print(f" {idx}. {r['file_name']} ({r['file_size']} bytes) | @{r['channel_username']} -> {r['message_link']}")
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        logger.info("\n[*] Shutdown requested by user. Goodbye!")
