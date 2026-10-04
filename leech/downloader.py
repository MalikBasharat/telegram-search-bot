"""
Asynchronous URL Leech & Mirror Engine
---------------------------------------
High-throughput streaming downloader with progress calculation,
Iranian CDN geoblock bypass detection, and proxy routing.
"""

import os
import re
import time
import ssl
import logging
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional, Callable, Dict, Any, Tuple
import aiohttp
from aiohttp_socks import ProxyConnector

from crawler.parser import format_size

logger = logging.getLogger("leech")
logger.setLevel(logging.INFO)

IRANIAN_DOMAINS = [
    "111.ir.cdn.ir",
    "downloadly.ir",
    "downloadlynet.ir",
    "soft98.ir",
    "yasdl.com",
    "p30download.ir",
    "shatelland.com"
]

def is_iranian_target(url: str) -> bool:
    """Checks if the URL targets an Iranian CDN or geoblocked mirror."""
    hostname = urlparse(url).hostname or ""
    return any(domain in hostname.lower() for domain in IRANIAN_DOMAINS)

def parse_filename(url: str, content_disposition: Optional[str] = None) -> str:
    """Extracts clean filename from Content-Disposition header or URL path."""
    if content_disposition:
        match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)', content_disposition, re.IGNORECASE)
        if match:
            fname = unquote(match.group(1).strip())
            if fname:
                return Path(fname).name

    parsed = urlparse(url)
    clean_path = unquote(parsed.path).strip()
    candidate = Path(clean_path).name
    if candidate and "." in candidate:
        return candidate

    timestamp = int(time.time())
    return f"downloaded_file_{timestamp}.bin"

def make_progress_bar(percent: float, length: int = 10) -> str:
    """Renders visual text progress bar, e.g. [██████░░░░] 60.0%"""
    clamped = max(0.0, min(100.0, percent))
    filled = int(round(length * (clamped / 100.0)))
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {clamped:.1f}%"

def format_eta(seconds: float) -> str:
    if seconds < 0 or seconds > 86400:
        return "Unknown"
    secs = int(seconds)
    if secs < 60:
        return f"{secs}s"
    mins, rem_secs = divmod(secs, 60)
    if mins < 60:
        return f"{mins}m {rem_secs}s"
    hours, rem_mins = divmod(mins, 60)
    return f"{hours}h {rem_mins}m"

async def download_file(
    url: str,
    dest_dir: Path,
    progress_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    iran_proxy: Optional[str] = None,
    chunk_size: int = 1024 * 1024  # 1MB
) -> Dict[str, Any]:
    """
    Asynchronously streams file download to dest_dir with progress updates.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    is_iran = is_iranian_target(url)
    proxy_url = iran_proxy if is_iran and iran_proxy else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    if is_iran:
        headers["Referer"] = "https://downloadly.ir/"

    # Setup SSL context (bypass revocation offline checks on Windows)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = None
    if proxy_url and proxy_url.startswith("socks"):
        connector = ProxyConnector.from_url(proxy_url, ssl=ssl_context)
    else:
        connector = aiohttp.TCPConnector(ssl=ssl_context)

    start_time = time.time()
    last_callback_time = 0.0

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        fetch_kwargs = {"timeout": aiohttp.ClientTimeout(total=3600)}
        if proxy_url and not proxy_url.startswith("socks"):
            fetch_kwargs["proxy"] = proxy_url

        async with session.get(url, **fetch_kwargs) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"HTTP Error {resp.status} from target server: {resp.reason}")

            total_size = int(resp.headers.get("Content-Length", 0))
            disposition = resp.headers.get("Content-Disposition")
            file_name = parse_filename(url, disposition)
            file_path = dest_dir / file_name

            downloaded_bytes = 0

            with open(file_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded_bytes += len(chunk)

                    now = time.time()
                    if progress_callback and (now - last_callback_time >= 3.5 or (total_size and downloaded_bytes >= total_size)):
                        elapsed = max(0.001, now - start_time)
                        speed = downloaded_bytes / elapsed
                        percent = (downloaded_bytes / total_size * 100.0) if total_size else 0.0
                        eta = ((total_size - downloaded_bytes) / speed) if (total_size and speed > 0) else 0.0

                        progress_data = {
                            "file_name": file_name,
                            "downloaded": downloaded_bytes,
                            "total": total_size,
                            "speed": speed,
                            "percent": percent,
                            "eta": eta,
                            "bar": make_progress_bar(percent) if total_size else "[Streaming...]"
                        }
                        try:
                            res = progress_callback(progress_data)
                            if hasattr(res, "__await__"):
                                await res
                        except Exception as e:
                            logger.debug(f"Progress callback error: {e}")
                        last_callback_time = now

            actual_size = file_path.stat().st_size
            return {
                "file_path": file_path,
                "file_name": file_name,
                "file_size": actual_size,
                "is_iranian": is_iran,
                "proxy_used": bool(proxy_url)
            }
