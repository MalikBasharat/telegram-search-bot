"""
Test Web Preview Scraper for Telegram Public Channels
"""

import re
import urllib.request

def test_fetch():
    channels = ["coderslearning", "ComputerScienceResources", "chinawenhua"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for ch in channels:
        url = f"https://t.me/s/{ch}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                posts = re.findall(rf'data-post="{ch}/(\d+)"', html, re.IGNORECASE)
                docs = re.findall(r'tgme_widget_message_document_title[^>]*>([^<]+)</div>', html)
                photos = re.findall(r'tgme_widget_message_photo_wrap', html)
                videos = re.findall(r'tgme_widget_message_video_wrap', html)
                print(f"[@{ch}] Total Posts: {len(posts)} | Docs: {len(docs)} | Photos: {len(photos)} | Videos: {len(videos)}")
                if docs:
                    print(f"   Sample docs: {docs[:3]}")
        except Exception as e:
            print(f"Error on @{ch}: {e}")

if __name__ == "__main__":
    test_fetch()
