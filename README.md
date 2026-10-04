---
title: Telegram Search and Leech Bot
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Telegram Channel Search & File Indexing Bot

An enterprise-grade Telegram file search engine and bot. Continuously indexes files (documents, APKs, videos, archives, audio, images) from monitored Telegram channels into a local SQLite database with Full-Text Search (FTS5). Users search via interactive bot commands (`/search`, `/doc`, `/video`, `/apk`), receive paginated results with file sizes and channel links, and can trigger direct zero-bandwidth file delivery.


---

## 🚀 Features

- **SQLite FTS5 Full-Text Indexing:** Fast keyword search across filenames and captions.
- **WAL Mode Concurrency:** Seamless read/write concurrency during active crawls.
- **Dual-Client Architecture:**
  - **Crawler:** Uses MTProto to crawl public channels or joined private channels.
  - **Bot Interface:** Clean Telegram bot with inline keyboard pagination (`[⬅️ Prev]` `[1/5]` `[Next ➡️]`).
- **Zero-Bandwidth File Forwarding:** `/download <id>` or `/get_<id>` forwards files up to 2GB directly from Telegram's cloud to the user chat without eating server bandwidth.
- **Admin Access Control:** Whitelist enforcement prevents unauthorized access to private indexes.
- **Rate-Limit & FloodWait Safeguards:** Paced batch crawling with automatic sleep on Telegram flood warnings.

---

## 📁 Directory Structure

```
telegram_channel_search_files/
├── bot/
│   └── handlers.py             # Bot commands, inline pagination, access control
├── crawler/
│   ├── crawler.py              # Background channel crawler & event listener
│   └── parser.py               # Media categorization & metadata extraction
├── db/
│   └── database.py             # SQLite WAL database & FTS5 full-text engine
├── data/
│   └── index.db                # SQLite database (auto-created on first run)
├── searches/
│   ├── queries/
│   │   └── channels.txt        # Monitored channels list
│   └── results/                # Saved search query dumps
├── files/
│   └── downloads/              # Downloaded local files
├── config/
│   └── .env.example            # Environment variables template
├── tests/
│   ├── test_db.py              # Database & FTS5 unit tests
│   └── test_parser.py          # Media parser unit tests
├── main.py                     # Main application entrypoint
├── requirements.txt            # Python dependencies
├── .gitignore                  # Safeguards sessions and database files
└── README.md
```

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
py -3.12 -m pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `config/.env.example` to `config/.env`:
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
ADMIN_USER_IDS=your_telegram_user_id
```
* **API ID & Hash:** Get from [https://my.telegram.org/apps](https://my.telegram.org/apps).
* **Bot Token:** Get from [@BotFather](https://t.me/BotFather).
* **Your User ID:** Get from [@userinfobot](https://t.me/userinfobot).

### 3. Set Monitored Channels
Add channel handles to `searches/queries/channels.txt`:
```text
chinawenhua
python_resources
ebooks_channel
```

### 4. Run the Application
```bash
py -3.12 main.py
```

---

## 💬 Bot Commands

| Command | Description |
| :--- | :--- |
| `/leech <url>` | Download any direct URL (up to 2GB) and send file directly to chat |
| `/search <query>` | Search all indexed files with inline pagination |
| `/doc <query>` | Filter search to documents, PDFs, and archives |
| `/video <query>` | Filter search to video files |
| `/apk <query>` | Filter search to Android APKs and software |
| `/recent` | View the 10 most recently indexed files |
| `/get_<id>` | Instantly forward/deliver file to your chat |
| `/stats` | View index statistics (files count, total volume, channels) |
| `/channels` | View currently monitored channels |
| `/syncmychannels` | Automatically import & monitor all channels joined by your Telegram account |
| `/findchannels <keyword>` | Search Telegram's global directory for new public channels |
| `/addchannel @username` | Add and trigger backfill for a new channel |
| `/allow <user_id>` | *(Admin Only)* Grant bot access to a user |


---

## 🧪 Running Automated Tests

```bash
# Run all test suites
py -3.12 -m unittest discover tests/
```
