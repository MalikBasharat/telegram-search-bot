# Network & Proxy Diagnostic Guidelines

## 1. Privacy & Sensitive Telemetry Redaction
- In all user-facing diagnostics, terminal summaries, and generated artifacts, NEVER print the user's raw public IP address or ISP. Always redact it as `[REDACTED_USER_IP]`.

## 2. Windows Network & Download Troubleshooting Invariants
- **curl on Windows:** Always include `--ssl-no-revoke` when executing `curl.exe` commands on Windows to prevent `CRYPT_E_REVOCATION_OFFLINE` failures during Schannel certificate revocation lookups.
- **IDM Proxy Hijacking:** When a user reports that Chrome downloads are stalled, unresponsive, or throwing proxy connection errors on a machine with Internet Download Manager (IDM) installed:
  1. Inspect `HKCU:\Software\DownloadManager` (`UseHttpProxy`, `UseHttpsProxy`, `HttpProxy`, `HttpPort`).
  2. If IDM's proxy points to a dead local port (e.g., `127.0.0.1:12334` or `127.0.0.1:2080`), reset IDM's proxy values to direct (`UseHttpProxy=0`, `UseHttpsProxy=0`, `nProxyMode=0`).
  3. Reset Windows WinINet (`ProxyEnable=0`) and call `InternetSetOptionW` with `INTERNET_OPTION_SETTINGS_CHANGED` and `INTERNET_OPTION_REFRESH` to flush the system proxy cache.

# Telegram Workspace Guidelines

## 1. Runtime & Commands
- **Python on Windows:** Use `py` (or `py -3`) instead of `python` to execute Python scripts in this workspace, as `python` is not registered directly on `PATH`.

## 2. Directory Structure & File Invariants
- **Search Queries & Targets:** Store keyword lists and target channels in `searches/queries/`.
- **Search Output:** Save search dumps and message matches in `searches/results/`.
- **Downloaded Media:** Route raw media, photos, and wallpapers to `files/media/` or `files/downloads/`.
- **Exports:** Save chat dumps and historical exports in `exports/`.
- **Credentials:** Keep all API keys and session tokens in `config/.env` or `config/`, never commit them.

## 3. Strict Git Credential & Personal Data Sanitization
- **Template, Blueprint & Example Files:** `config/.env.example`, `render.yaml`, documentation, and sample configs must NEVER contain real API IDs, API hashes, bot tokens, phone numbers, session strings, or **numeric Telegram User IDs** (`ADMIN_USER_IDS`). 
  - In `render.yaml`: Always set `sync: false` for all sensitive variables including `ADMIN_USER_IDS`.
  - In templates and docs: Always enforce dummy placeholders (`your_token_here`, `your_telegram_id`).
- **Pre-Commit Secret Scan:** Before executing `git commit` or `git push`, inspect all staged files (`git diff --cached`) to verify zero credentials, tokens, user IDs, or secret keys are staged.
- **Git History Purge Protocol:** If secrets or user IDs are ever committed, NEVER make an overwrite commit on top. Immediately perform a `git reset --soft` or amend, rewrite history to permanently erase the sensitive commit, and force-push (`git push --force origin main`). Prompt the user to rotate the exposed token immediately.

## 4. Cloud Hosting & Deployment Invariants
- **Hugging Face Spaces Compute Policy:** Hugging Face Spaces free tier only supports static HTML/JS; Docker and compute spaces require a paid PRO plan ($9/mo). Do not attempt free Docker compute deployment on Hugging Face.
- **Render Free Web Service Configuration:** Deploy 24/7 Python/Docker bots on Render free tier with:
  - Docker runtime (`Dockerfile` with multi-stage build).
  - Port `10000` bound to a lightweight `aiohttp` keep-alive health server (`GET /health` responding `200 OK`).
  - All credentials injected via Render Environment Variables, never via Git.
  - Headless user authentication powered by `TELEGRAM_USER_SESSION_STRING` (`StringSession`) to avoid interactive SMS prompts in container restarts.
- **Headless Container Observability:** The `/health` endpoint must report live authentication telemetry (`user_client_authorized`, `user_name`, `has_session_string`, `total_files`, `total_channels`) to allow instantaneous verification of cloud MTProto session health via HTTP.
- **On-Demand Admin Verification:** Always provide an on-demand `/crawl` command in the bot so administrators can trigger and observe channel indexing without waiting for background polling loops.
