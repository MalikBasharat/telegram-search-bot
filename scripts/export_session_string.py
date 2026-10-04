"""
Export Telegram User Session to StringSession
----------------------------------------------
Converts your local config/user_session.session into a single text string
for easy cloud deployment (Koyeb, Render, Railway, Hugging Face, etc.).

Run:
    py -3.12 scripts/export_session_string.py
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
ENV_FILE = CONFIG_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
load_dotenv(BASE_DIR / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

async def export():
    if not API_ID or not API_HASH:
        print("[!] Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in config/.env")
        return

    session_path = str(CONFIG_DIR / "user_session")
    session_file = Path(f"{session_path}.session")
    if not session_file.exists():
        print(f"[!] Error: No user session found at {session_file}")
        print("    Please run 'py -3.12 login_user.py' first!")
        return

    print("[*] Reading authorized session from disk...")
    client = TelegramClient(session_path, int(API_ID), API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("[!] Error: Session is not authorized. Please run 'py -3.12 login_user.py'.")
        await client.disconnect()
        return

    me = await client.get_me()
    string_token = StringSession.save(client.session)
    await client.disconnect()

    # Save to a private text file for convenience
    output_file = CONFIG_DIR / "session_string.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(string_token)

    print("\n" + "=" * 65)
    print("[+] SUCCESS! Your Cloud StringSession has been generated!")
    print(f"[+] Logged in as: {me.first_name} (@{me.username or 'no_username'})")
    print("=" * 65)
    print("\nYour TELEGRAM_USER_SESSION_STRING:")
    print("-" * 65)
    print(string_token)
    print("-" * 65)
    print(f"\n[+] Also saved to: {output_file}")
    print("\n--> Add this as an Environment Variable in your Cloud Dashboard:")
    print("    Variable Name:  TELEGRAM_USER_SESSION_STRING")
    print("    Variable Value: (paste the string above)\n")


if __name__ == "__main__":
    asyncio.run(export())
