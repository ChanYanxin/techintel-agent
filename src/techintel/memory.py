"""Local per-session notes; not suitable for untrusted multi-tenant production use."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from threading import Lock


class SessionMemory:
    def __init__(self, db_path: str | Path = ":memory:"):
        self.lock = Lock()
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        with self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                note TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    def add(self, session_id: str, note: str) -> dict:
        if len(session_id) > 80 or not session_id.strip() or len(note) > 1500 or not note.strip():
            raise ValueError("session_id must be 1-80 characters and note 1-1500 characters")
        with self.lock, self.db:
            self.db.execute("INSERT INTO notes(session_id,note) VALUES (?,?)", (session_id, note))
        return {"saved": True, "session_id": session_id}

    def recent(self, session_id: str, limit: int = 5) -> list[str]:
        with self.lock:
            rows = self.db.execute(
                "SELECT note FROM notes WHERE session_id=? ORDER BY id DESC LIMIT ?",
                (session_id, min(max(limit, 1), 10))).fetchall()
        return [r[0] for r in rows]
