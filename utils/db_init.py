"""
utils/db_init.py
----------------
Initialises the SQLite database and seeds the default company + admin user.
All writes are protected by db_lock().
"""

import os
import sqlite3
from typing import Optional

from utils.db_lock import db_lock

_DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "app.sqlite")
DB_PATH = os.getenv("SQLITE_PATH", _DEFAULT_DB_PATH)


def get_connection() -> sqlite3.Connection:
    """Return a WAL-mode SQLite connection with row_factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    for col, defn in [("star_rating", "INTEGER"), ("comment", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE feedback ADD COLUMN {col} {defn}")
            conn.commit()
        except Exception:
            pass
    return conn


def init_db() -> None:
    """Create all tables and seed defaults on first run."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

    with db_lock():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                website         TEXT,
                scraping_enabled INTEGER DEFAULT 1,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id    INTEGER NOT NULL,
                email         TEXT    NOT NULL,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL CHECK(role IN ('user','worker','admin')),
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, email)
            );

            CREATE TABLE IF NOT EXISTS documents (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id     INTEGER NOT NULL,
                filename       TEXT    NOT NULL,
                file_type      TEXT    NOT NULL,
                file_size      INTEGER NOT NULL DEFAULT 0,
                visibility     TEXT    NOT NULL DEFAULT 'public'
                                       CHECK(visibility IN ('public','worker')),
                uploaded_by    INTEGER NOT NULL,
                content_hash   TEXT,
                relevance_score REAL   DEFAULT 1.0,
                usage_count    INTEGER DEFAULT 0,
                chunk_count    INTEGER DEFAULT 0,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id)  REFERENCES companies(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                company_id   INTEGER NOT NULL,
                query        TEXT    NOT NULL,
                response     TEXT    NOT NULL,
                lang         TEXT    DEFAULT 'en',
                sources_json TEXT    DEFAULT '[]',
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)    REFERENCES users(id),
                FOREIGN KEY (company_id) REFERENCES companies(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_id         INTEGER NOT NULL,
                score           INTEGER NOT NULL CHECK(score IN (1,-1)),
                star_rating     INTEGER,
                comment         TEXT,
                analysis        TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (user_id)         REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS replay_buffer (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id     INTEGER NOT NULL,
                query          TEXT    NOT NULL,
                response       TEXT    NOT NULL,
                embedding_json TEXT    NOT NULL,
                quality_score  REAL    DEFAULT 0.5,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            );

            CREATE TABLE IF NOT EXISTS scraped_pages (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id   INTEGER NOT NULL,
                url          TEXT    NOT NULL,
                title        TEXT,
                content_hash TEXT,
                chunk_count  INTEGER DEFAULT 0,
                last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_id, url),
                FOREIGN KEY (company_id) REFERENCES companies(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id       INTEGER,
                user_id          INTEGER,
                event_type       TEXT NOT NULL,
                toxic_flag       INTEGER DEFAULT 0,
                payload_encrypted TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ── Seed default company ──────────────────────────────────────────────
        company_id   = int(os.getenv("DEFAULT_COMPANY_ID",   "1"))
        company_name = os.getenv("DEFAULT_COMPANY_NAME",     "AI Assistant")
        company_web  = os.getenv("DEFAULT_COMPANY_WEBSITE",  "https://www.pendo.io")

        cursor.execute("SELECT id FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO companies (id, name, website, scraping_enabled) VALUES (?,?,?,1)",
                (company_id, company_name, company_web),
            )

        # ── Seed default admin user ───────────────────────────────────────────
        import bcrypt
        cursor.execute(
            "SELECT id FROM users WHERE company_id = ? AND role = 'admin'",
            (company_id,),
        )
        if not cursor.fetchone():
            raw_pw = os.getenv("ADMIN_PASSWORD", "admin123")
            pw_hash = bcrypt.hashpw(raw_pw.encode(), bcrypt.gensalt(rounds=12)).decode()
            cursor.execute(
                "INSERT INTO users (company_id, email, password_hash, role) VALUES (?,?,?,?)",
                (company_id, "admin", pw_hash, "admin"),
            )

        # ── Seed default regular user ─────────────────────────────────────────
        cursor.execute(
            "SELECT id FROM users WHERE email = ? AND company_id = ?",
            ("user", company_id),
        )
        if not cursor.fetchone():
            raw_pw = os.getenv("DEFAULT_USER_PASSWORD", "user123")
            pw_hash = bcrypt.hashpw(raw_pw.encode(), bcrypt.gensalt(rounds=12)).decode()
            cursor.execute(
                "INSERT INTO users (company_id, email, password_hash, role) VALUES (?,?,?,?)",
                (company_id, "user", pw_hash, "user"),
            )

        conn.commit()
        conn.close()

    # ── Migrations (outside db_lock to avoid re-entrant lock issues) ─────────
    conn = get_connection()
    for col, definition in [("star_rating", "INTEGER"), ("comment", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE feedback ADD COLUMN {col} {definition}")
            conn.commit()
            print(f"[db] migration: added feedback.{col}")
        except Exception:
            pass
    conn.close()


def get_company(company_id: int) -> Optional[sqlite3.Row]:
    """Return a company row or None."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        conn.close()
        return row
    except Exception as exc:
        raise RuntimeError(f"get_company({company_id}) failed: {exc}") from exc
