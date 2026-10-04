"""
Cloud Keep-Alive & Healthcheck HTTP Server
------------------------------------------
Lightweight asynchronous web server to keep cloud containers alive
and satisfy healthchecks on Koyeb, Render, Railway, Hugging Face, etc.
"""

import os
import time
import logging
from aiohttp import web
from db.database import get_stats, get_channels

logger = logging.getLogger("health_server")
logger.setLevel(logging.INFO)

START_TIME = time.time()

async def handle_index(request: web.Request) -> web.Response:
    stats = get_stats()
    channels = get_channels()
    uptime_sec = int(time.time() - START_TIME)
    uptime_str = f"{uptime_sec // 3600}h {(uptime_sec % 3600) // 60}m {uptime_sec % 60}s"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram File Search Bot - 24/7 Status</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: #1e293b; padding: 2rem; border-radius: 1rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 480px; width: 100%; border: 1px solid #334155; }}
        .status {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #4ade80; font-weight: bold; background: rgba(74, 222, 128, 0.1); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; }}
        .dot {{ width: 8px; height: 8px; background: #4ade80; border-radius: 50%; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; }}
        .stat-box {{ background: #0f172a; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; }}
        .stat-val {{ font-size: 1.5rem; font-weight: bold; color: #38bdf8; }}
        .stat-lbl {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; margin-top: 0.25rem; }}
        .footer {{ font-size: 0.75rem; color: #64748b; text-align: center; margin-top: 1.5rem; }}
    </style>
</head>
<body>
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 1.25rem;">🤖 Telegram Bot Service</h2>
            <div class="status"><span class="dot"></span> Online 24/7</div>
        </div>
        <div class="grid">
            <div class="stat-box">
                <div class="stat-val">{stats['total_files']}</div>
                <div class="stat-lbl">Indexed Files</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">{len(channels)}</div>
                <div class="stat-lbl">Monitored Channels</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">{uptime_str}</div>
                <div class="stat-lbl">Container Uptime</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">Active</div>
                <div class="stat-lbl">Crawler Status</div>
            </div>
        </div>
        <div class="footer">Powered by Telethon MTProto & SQLite FTS5 Engine</div>
    </div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")

HEALTH_STATUS = {
    "user_client_authorized": False,
    "user_name": None,
    "has_session_string": False,
}

async def handle_health(request: web.Request) -> web.Response:
    stats = get_stats()
    return web.json_response({
        "status": "ok",
        "bot": "running",
        "uptime_seconds": int(time.time() - START_TIME),
        "total_files": stats["total_files"],
        "total_channels": stats["total_channels"],
        "user_client_authorized": HEALTH_STATUS.get("user_client_authorized", False),
        "user_name": HEALTH_STATUS.get("user_name"),
        "has_session_string": HEALTH_STATUS.get("has_session_string", False)
    })

def make_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    return app

async def start_health_server(port: int = 8080):
    """Starts the healthcheck HTTP server."""
    app = make_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"[+] Cloud Keep-Alive HTTP server listening on port {port}")
