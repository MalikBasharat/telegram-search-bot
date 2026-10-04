# 24/7 Free Cloud Hosting Deployment Guide

This guide explains how to deploy your Telegram Search & Leech Bot to the cloud for free, so it runs **24/7 without needing your PC on**.

---

## 🔑 Your Environment Variables for the Cloud

When creating your service on any cloud provider, add these 5 Environment Variables in their dashboard:

| Variable Name | Value | Where to find it |
| :--- | :--- | :--- |
| `TELEGRAM_API_ID` | `your_api_id` | From your `config/.env` |
| `TELEGRAM_API_HASH` | `your_api_hash` | From your `config/.env` |
| `TELEGRAM_BOT_TOKEN` | `your_bot_token` | From your `config/.env` |
| `ADMIN_USER_IDS` | `your_telegram_id` | Your Telegram User ID (from @userinfobot) |
| `TELEGRAM_USER_SESSION_STRING` | *(Paste string)* | Found inside `config/session_string.txt` |

*(All secrets are kept safely in your cloud dashboard. Never commit `.env` or `session_string.txt` to GitHub!)*

---

## 🚀 Option 1: Koyeb (Recommended — Free & Never Sleeps)

Koyeb provides an **always-on free tier** (512MB RAM, continuous execution) with **no credit card required**.

### Step 1: Push Code to GitHub
1. Go to [GitHub.com](https://github.com) and create a **New Repository** (recommended: **Private**).
2. In your local project folder, open terminal and run:
   ```bash
   git init
   git add .
   git commit -m "Telegram bot cloud ready"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

### Step 2: Deploy on Koyeb
1. Sign up for free at **[https://app.koyeb.com](https://app.koyeb.com)** (sign in with GitHub).
2. Click **Create Service** $\rightarrow$ select **GitHub**.
3. Choose your repository.
4. Under **Builder**, select **Dockerfile** (it automatically detects our `Dockerfile`).
5. Scroll down to **Environment Variables** and add the 5 variables from the table above.
6. Click **Deploy**.

*That's it! Koyeb will build the container, start the bot, and keep it online 24/7/365!*

---

## 🚀 Option 2: Hugging Face Spaces (100% Free — 16GB RAM)

Hugging Face Spaces gives **free 2 vCPU + 16GB RAM Docker instances** with **no credit card required**.

1. Go to **[https://huggingface.co/spaces](https://huggingface.co/spaces)** and sign up / log in.
2. Click **Create new Space**.
3. Name your space (e.g. `telegram-search-bot`).
4. Select **Docker** (Blank) as the Space SDK.
5. Set Space visibility to **Private** (or Public).
6. Click **Create Space**.
7. Go to **Settings** $\rightarrow$ **Variables and secrets** $\rightarrow$ **New secret**:
   * Add each of the 5 variables from the table above.
8. Click **Files** $\rightarrow$ **Add file** $\rightarrow$ **Upload files**:
   * Upload all project files (`main.py`, `Dockerfile`, `requirements.txt`, `bot/`, `crawler/`, `db/`, `leech/`, `server/`, `searches/`).
9. Hugging Face will automatically build and start your bot!

---

## 🌐 Verifying 24/7 Cloud Health

Once deployed, your cloud host will provide a public URL (e.g. `https://your-app.koyeb.app`).
You can visit:
* `https://your-app.koyeb.app/` $\rightarrow$ Live status dashboard showing indexed file counts and uptime.
* `https://your-app.koyeb.app/health` $\rightarrow$ Returns `{"status": "ok", "bot": "running"}`.
