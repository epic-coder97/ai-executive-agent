# agent/memory.py
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (
  user TEXT,
  k TEXT,
  v TEXT,
  PRIMARY KEY (user, k)
);

CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user TEXT,
  action TEXT,
  summary TEXT,
  payload TEXT,
  approved INTEGER DEFAULT 0,
  created_at TEXT
);
"""

class Memory:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        # Ensure base tables exist
        for stmt in SCHEMA.split(";\n"):
            if stmt.strip():
                self.db.execute(stmt)
        self.db.commit()
        # Add any missing columns on existing DBs
        self._migrate_approvals()

    def _migrate_approvals(self):
        cur = self.db.execute("PRAGMA table_info(approvals)")
        cols = {row[1] for row in cur.fetchall()}
        if "user" not in cols:
            self.db.execute("ALTER TABLE approvals ADD COLUMN user TEXT")
        if "created_at" not in cols:
            # No DEFAULT here — SQLite disallows non-constant defaults in ALTER
            self.db.execute("ALTER TABLE approvals ADD COLUMN created_at TEXT")
            # Backfill existing rows
            self.db.execute(
                "UPDATE approvals "
                "SET created_at = STRFTIME('%Y-%m-%dT%H:%M:%SZ','now') "
                "WHERE created_at IS NULL"
            )
        self.db.commit()

    # --- simple note persistence for demo ---
    def add_note(self, user: str, note: str):
        import time
        key = f"note:{int(time.time()*1000)}"
        self.set(user, key, note)
        return key

    def list_notes(self, user: str):
        cur = self.db.execute(
            "SELECT k, v FROM kv WHERE user=? AND k LIKE 'note:%' ORDER BY k DESC",
            (user,)
        )
        return [{"key": k, "note": v} for (k, v) in cur.fetchall()]


    # ---- session KV ----
    def reset_session(self, user: str):
        self.db.execute("DELETE FROM kv WHERE user = ?", (user,))
        self.db.commit()

    def set(self, user: str, k: str, v: str):
        self.db.execute("REPLACE INTO kv(user,k,v) VALUES(?,?,?)", (user, k, v))
        self.db.commit()

    def get(self, user: str, k: str, default: str = "") -> str:
        cur = self.db.execute("SELECT v FROM kv WHERE user=? AND k=?", (user, k))
        row = cur.fetchone()
        return row[0] if row else default

    # ---- approvals (user-scoped) ----
    def insert_approval(self, user: str, action: str, summary: str, payload: str) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        cur = self.db.cursor()
        cur.execute(
            "INSERT INTO approvals(user, action, summary, payload, approved, created_at) "
            "VALUES(?,?,?,?,0,?)",
            (user, action, summary, payload, created_at),
        )
        self.db.commit()
        return cur.lastrowid

    def list_approvals(self, user: str, approved: int = 0):
        cur = self.db.execute(
            "SELECT id, user, action, summary, payload, approved, created_at "
            "FROM approvals WHERE approved=? AND user=? ORDER BY id",
            (approved, user),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def set_approved(self, approval_id: int):
        self.db.execute("UPDATE approvals SET approved=1 WHERE id=?", (approval_id,))
        self.db.commit()

    def get_approval(self, approval_id: int):
        cur = self.db.execute(
            "SELECT id, user, action, summary, payload, approved, created_at "
            "FROM approvals WHERE id=?", (approval_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def clear_pending(self, user: str):
        self.db.execute("DELETE FROM approvals WHERE approved=0 AND user=?", (user,))
        self.db.commit()
