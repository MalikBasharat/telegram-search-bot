"""
Telegram Message Media Parser & Categorizer
-------------------------------------------
Extracts file metadata, sanitizes filenames, and categorizes media types
from Telethon message objects.
"""

from typing import Optional, Dict, Any
from telethon.tl import types

def format_size(size_bytes: Optional[int]) -> str:
    """Converts raw byte count into human-readable string (KB, MB, GB)."""
    if not size_bytes or size_bytes < 0:
        return "0 B"
    num = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f"{num:.1f} {unit}" if unit != 'B' else f"{int(num)} B"
        num /= 1024.0
    return f"{num:.1f} PB"

def categorize_media(filename: str, has_video: bool = False, has_audio: bool = False, has_photo: bool = False) -> str:
    """Categorizes file into document, video, apk, audio, or image."""
    lower_name = filename.lower()
    
    if lower_name.endswith(('.apk', '.xapk', '.apks', '.exe', '.msi', '.dmg', '.iso')):
        return "apk"
    if has_video or lower_name.endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.ts', '.wmv')):
        return "video"
    if has_audio or lower_name.endswith(('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.opus')):
        return "audio"
    if has_photo or lower_name.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')):
        return "image"
    return "document"

def extract_file_metadata(msg: Any, channel_username: str) -> Optional[Dict[str, Any]]:
    """
    Extracts structured file metadata from a Telethon message.
    Returns None if the message has no media or files.
    """
    if not getattr(msg, 'media', None):
        return None

    clean_channel = channel_username.strip().replace("@", "").replace("https://t.me/", "")
    file_name = None
    file_size = 0
    has_video = bool(getattr(msg, 'video', None))
    has_audio = bool(getattr(msg, 'audio', None))
    has_photo = bool(getattr(msg, 'photo', None))

    doc = getattr(msg, 'document', None)
    if doc:
        file_size = doc.size or 0
        for attr in getattr(doc, 'attributes', []):
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                break
            elif isinstance(attr, types.DocumentAttributeVideo):
                has_video = True
            elif isinstance(attr, types.DocumentAttributeAudio):
                has_audio = True
                if attr.title:
                    file_name = f"{attr.performer or 'Artist'} - {attr.title}.mp3"

    if not file_name:
        if has_video:
            file_name = f"video_{msg.id}.mp4"
            if getattr(msg, 'video', None):
                file_size = msg.video.size or 0
        elif has_audio:
            file_name = f"audio_{msg.id}.mp3"
        elif has_photo:
            file_name = f"photo_{msg.id}.jpg"
            file_size = getattr(msg.photo, 'size', 0) if hasattr(msg.photo, 'size') else 0
        else:
            file_name = f"file_{msg.id}.bin"

    media_type = categorize_media(file_name, has_video=has_video, has_audio=has_audio, has_photo=has_photo)
    caption_text = (getattr(msg, 'text', '') or getattr(msg, 'message', '') or '').strip()
    msg_date = msg.date.isoformat() if getattr(msg, 'date', None) else None

    return {
        "channel_username": clean_channel,
        "message_id": msg.id,
        "file_name": file_name,
        "file_size": file_size,
        "media_type": media_type,
        "date": msg_date,
        "caption": caption_text,
        "message_link": f"https://t.me/{clean_channel}/{msg.id}"
    }
