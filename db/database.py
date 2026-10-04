"""
Database Layer for Telegram File Search & Indexing Engine
---------------------------------------------------------
Powered by SQLite WAL mode and FTS5 (Full-Text Search).
Handles concurrent crawling and query operations reliably.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Generator

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "index.db"

def create_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = Path(db_path or DEFAULT_DB_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

@contextmanager
def get_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    conn = create_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: Optional[Path] = None):
    """Initializes tables, FTS5 virtual table, and sync triggers."""
    with get_db(db_path) as conn:
        with conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                title TEXT,
                last_message_id INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_username TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                media_type TEXT DEFAULT 'document',
                date TEXT,
                caption TEXT,
                message_link TEXT,
                UNIQUE(channel_username, message_id)
            );

            CREATE TABLE IF NOT EXISTS whitelist (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_by INTEGER,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- FTS5 full-text search table with external content sync
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                file_name,
                caption,
                channel_username,
                media_type,
                content='files',
                content_rowid='id'
            );

            -- Synchronization Triggers for FTS5
            CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                INSERT INTO files_fts(rowid, file_name, caption, channel_username, media_type)
                VALUES (new.id, new.file_name, new.caption, new.channel_username, new.media_type);
            END;

            CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                INSERT INTO files_fts(files_fts, rowid, file_name, caption, channel_username, media_type)
                VALUES('delete', old.id, old.file_name, old.caption, old.channel_username, old.media_type);
            END;

            CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                INSERT INTO files_fts(files_fts, rowid, file_name, caption, channel_username, media_type)
                VALUES('delete', old.id, old.file_name, old.caption, old.channel_username, old.media_type);
                INSERT INTO files_fts(rowid, file_name, caption, channel_username, media_type)
                VALUES (new.id, new.file_name, new.caption, new.channel_username, new.media_type);
            END;
            """)

def upsert_file(file_data: Dict[str, Any], db_path: Optional[Path] = None) -> bool:
    sql = """
    INSERT INTO files (
        channel_username, message_id, file_name, file_size,
        media_type, date, caption, message_link
    ) VALUES (
        :channel_username, :message_id, :file_name, :file_size,
        :media_type, :date, :caption, :message_link
    ) ON CONFLICT(channel_username, message_id) DO NOTHING;
    """
    with get_db(db_path) as conn:
        with conn:
            cursor = conn.execute(sql, file_data)
            return cursor.rowcount > 0

def clean_fts_query(query: str) -> str:
    cleaned = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_", ".")).strip()
    words = [w.strip() for w in cleaned.split() if w.strip()]
    if not words:
        return ""
    return " ".join(f'"{w}"*' for w in words)

def search_files(
    query: str,
    media_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db_path: Optional[Path] = None
) -> Tuple[List[Dict[str, Any]], int]:
    fts_term = clean_fts_query(query)
    if not fts_term:
        return [], 0

    with get_db(db_path) as conn:
        where_clauses = ["files_fts MATCH ?"]
        params: List[Any] = [fts_term]

        if media_type:
            where_clauses.append("f.media_type = ?")
            params.append(media_type)

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
        SELECT COUNT(*) as total
        FROM files_fts
        JOIN files f ON f.id = files_fts.rowid
        WHERE {where_sql};
        """
        total = conn.execute(count_sql, params).fetchone()["total"]

        select_sql = f"""
        SELECT f.*, bm25(files_fts) as rank
        FROM files_fts
        JOIN files f ON f.id = files_fts.rowid
        WHERE {where_sql}
        ORDER BY rank
        LIMIT ? OFFSET ?;
        """
        query_params = params + [limit, offset]
        rows = conn.execute(select_sql, query_params).fetchall()
        return [dict(r) for r in rows], total

def get_recent_files(limit: int = 10, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with get_db(db_path) as conn:
        rows = conn.execute("""
            SELECT * FROM files ORDER BY id DESC LIMIT ?;
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_file_by_id(file_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    with get_db(db_path) as conn:
        row = conn.execute("SELECT * FROM files WHERE id = ?;", (file_id,)).fetchone()
        return dict(row) if row else None

def get_stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    target_path = Path(db_path or DEFAULT_DB_PATH)
    with get_db(db_path) as conn:
        files_row = conn.execute("""
            SELECT COUNT(*) as total_files, COALESCE(SUM(file_size), 0) as total_bytes
            FROM files;
        """).fetchone()
        channels_row = conn.execute("SELECT COUNT(*) as total_channels FROM channels;").fetchone()
        
        db_size = target_path.stat().st_size if target_path.exists() else 0
        return {
            "total_files": files_row["total_files"],
            "total_bytes": files_row["total_bytes"],
            "total_channels": channels_row["total_channels"],
            "db_size_bytes": db_size
        }

def add_channel(username: str, title: Optional[str] = None, db_path: Optional[Path] = None) -> bool:
    clean_username = username.strip().replace("@", "").replace("https://t.me/", "")
    with get_db(db_path) as conn:
        with conn:
            cursor = conn.execute("""
                INSERT INTO channels (username, title)
                VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET title=COALESCE(excluded.title, channels.title);
            """, (clean_username, title))
            return cursor.rowcount > 0

def get_channels(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT * FROM channels ORDER BY username ASC;").fetchall()
        return [dict(r) for r in rows]

def update_channel_cursor(username: str, last_message_id: int, db_path: Optional[Path] = None):
    clean_username = username.strip().replace("@", "")
    with get_db(db_path) as conn:
        with conn:
            conn.execute("""
                UPDATE channels 
                SET last_message_id = MAX(last_message_id, ?)
                WHERE username = ?;
            """, (last_message_id, clean_username))

def is_whitelisted(user_id: int, admin_ids: Optional[List[int]] = None, db_path: Optional[Path] = None) -> bool:
    if admin_ids and user_id in admin_ids:
        return True
    with get_db(db_path) as conn:
        row = conn.execute("SELECT 1 FROM whitelist WHERE user_id = ?;", (user_id,)).fetchone()
        return bool(row)

def add_whitelist(user_id: int, username: Optional[str] = None, added_by: Optional[int] = None, db_path: Optional[Path] = None) -> bool:
    with get_db(db_path) as conn:
        with conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO whitelist (user_id, username, added_by)
                VALUES (?, ?, ?);
            """, (user_id, username, added_by))
            return cursor.rowcount > 0
