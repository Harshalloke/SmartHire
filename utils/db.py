# utils/db.py
import os, sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            role_hint TEXT,
            match_percent REAL,
            ats_score INTEGER,
            created_at TEXT,
            top_keywords TEXT,
            missing_keywords TEXT
        )
        """)
        conn.commit()

def save_run(filename: str, role_hint: str, match_percent: float, ats_score: int,
             top_keywords: list[str], missing_keywords: list[str]):
    from json import dumps
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO runs (filename, role_hint, match_percent, ats_score, created_at, top_keywords, missing_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            filename or "",
            role_hint or "",
            float(match_percent or 0.0),
            int(ats_score or 0),
            datetime.utcnow().isoformat(timespec="seconds"),
            dumps(top_keywords or []),
            dumps(missing_keywords or []),
        ))
        conn.commit()

def list_runs(search: str | None = None, limit: int = 100, offset: int = 0):
    q = "SELECT * FROM runs"
    args = []
    if search:
        q += " WHERE role_hint LIKE ? OR filename LIKE ?"
        like = f"%{search}%"
        args += [like, like]
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    with get_conn() as conn:
        cur = conn.execute(q, args)
        return [dict(row) for row in cur.fetchall()]

def delete_run(run_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.commit()

def clear_runs():
    with get_conn() as conn:
        conn.execute("DELETE FROM runs")
        conn.commit()
