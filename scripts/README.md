# Telegram Scripts & Tools

Place scripts for interacting with Telegram, searching channels, downloading media, and analyzing messages here.

## Recommended Libraries:
- **Telethon**: User API (MTProto) client, ideal for searching public & private channels, message scraping, downloading files without bot file-size limits.
- **Pyrogram**: Modern MTProto client for Python.
- **python-telegram-bot**: Ideal for developing Telegram Bot API bots.

## Available Scripts

1. **`file_search_bot.py`**:
   Interactive Telegram Bot that listens to commands (`/search <query>`, `/doc <query>`, `/video <query>`), queries target channels, returns direct clickable links with file sizes, and saves search output dumps in `searches/results/`.
   ```bash
   py scripts/file_search_bot.py
   ```

2. **`search_channel.py`**:
   CLI script to search specific channel posts and automatically download matched media files into `files/downloads/`.
   ```bash
   py scripts/search_channel.py
   ```

## Getting Started
1. Copy `config/.env.example` to `config/.env` and fill in your API credentials from https://my.telegram.org.
2. If running as a Telegram bot, add your `TELEGRAM_BOT_TOKEN` from [@BotFather](https://t.me/BotFather).
3. Add target channels to `searches/queries/channels.txt`.
4. Run:
   ```bash
   py scripts/file_search_bot.py
   ```

