"""
One-Time Telegram User Account Login Utility
---------------------------------------------
Logs in your Telegram account to generate config/user_session.session.
This gives the crawler full permission to read and index all public
channels (which Telegram bots are restricted from doing by default).

Run:
    py -3.12 login_user.py
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import PhoneNumberInvalidError

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
ENV_FILE = CONFIG_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
load_dotenv(BASE_DIR / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

def prompt_phone():
    phone = (os.getenv("TELEGRAM_PHONE_NUMBER") or "").strip()
    if not phone:
        raw = input("Enter your Telegram phone number with country code (e.g. +91XXXXXXXXXX or +1XXXXXXXXXX): ").strip()
        phone = "".join(c for c in raw if c.isdigit() or c == "+")
        
        # If user entered 10 digits without country code (common in India)
        if len(phone) == 10 and not phone.startswith("+") and phone[0] in "6789":
            suggested = f"+91{phone}"
            confirm = input(f"No country code detected. Do you mean {suggested}? (Y/n): ").strip().lower()
            if confirm in ("", "y", "yes"):
                phone = suggested

        if not phone.startswith("+"):
            phone = f"+{phone}"

    return phone

async def login():
    if not API_ID or not API_HASH:
        print("[!] Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in config/.env")
        return

    session_path = str(CONFIG_DIR / "user_session")
    print(f"[*] Connecting to Telegram to create User Session at: {session_path}")
    print("[*] (Telegram will send a verification code to your Telegram app)\n")

    client = TelegramClient(session_path, int(API_ID), API_HASH)
    try:
        await client.start(phone=prompt_phone)
        me = await client.get_me()
        print(f"\n[+] SUCCESS! Logged in as: {me.first_name} (@{me.username or 'no_username'}, ID: {me.id})")
        print("[+] Session saved to: config/user_session.session")
        print("[+] Your crawler now has full access to index all public channels!")
        print("\nNext step: Run 'py -3.12 main.py' to start the crawler and bot!")
    except PhoneNumberInvalidError:
        print("\n[!] Error: The phone number was invalid.")
        print("    Make sure to include your country code with a '+' (e.g., +91 for India, +1 for US/Canada).")
    except Exception as e:
        print(f"\n[!] Login failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(login())
