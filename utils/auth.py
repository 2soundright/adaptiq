"""
utils/auth.py
-------------
User authentication: login, register, session helpers.
Passwords are hashed with bcrypt (rounds=12).
All DB writes are protected by db_lock().
"""

import json
import sqlite3
from typing import Dict, Optional, Tuple

import bcrypt

from utils.db_init import get_connection
from utils.db_lock import db_lock
from utils.encryption import encrypt


# ── helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> Dict:
    return dict(row)


# ── public API ────────────────────────────────────────────────────────────────

def login(email: str, password: str, company_id: int) -> Tuple[bool, Optional[Dict], str]:
    """
    Attempt to log in a user.

    Returns:
        (success: bool, user_dict | None, message: str)
    """
    if not email or not password:
        return False, None, "Email and password are required."
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND company_id = ?",
            (email.strip().lower(), company_id),
        ).fetchone()
        conn.close()
    except Exception as exc:
        return False, None, f"Database error during login: {exc}"

    if not row:
        return False, None, "Invalid email or password."

    try:
        match = bcrypt.checkpw(password.encode(), row["password_hash"].encode())
    except Exception as exc:
        return False, None, f"Password check error: {exc}"

    if not match:
        return False, None, "Invalid email or password."

    return True, _row_to_dict(row), "Login successful."


def register(
    email: str,
    password: str,
    company_id: int,
    role: str = "user",
) -> Tuple[bool, str]:
    """
    Register a new user.

    Returns:
        (success: bool, message: str)
    """
    if not email or not password:
        return False, "Email and password are required."
    if role not in ("user", "worker", "admin"):
        return False, f"Invalid role '{role}'."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    try:
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    except Exception as exc:
        return False, f"Password hashing failed: {exc}"

    try:
        with db_lock():
            conn = get_connection()
            conn.execute(
                "INSERT INTO users (company_id, email, password_hash, role) VALUES (?,?,?,?)",
                (company_id, email.strip().lower(), pw_hash, role),
            )
            conn.commit()
            conn.close()
        return True, "User registered successfully."
    except Exception as exc:
        msg = str(exc)
        if "UNIQUE" in msg or "unique" in msg.lower():
            return False, "A user with that email already exists."
        return False, f"Registration failed: {exc}"


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Return a user dict by primary key, or None."""
    try:
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return _row_to_dict(row) if row else None
    except Exception as exc:
        raise RuntimeError(f"get_user_by_id({user_id}) failed: {exc}") from exc


def write_audit_log(
    event_type: str,
    payload: Dict,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
    toxic_flag: bool = False,
) -> None:
    """
    Write an encrypted audit-log entry.
    Payload dict is JSON-serialised then Fernet-encrypted before storage.
    """
    try:
        encrypted = encrypt(json.dumps(payload, ensure_ascii=False))
        with db_lock():
            conn = get_connection()
            conn.execute(
                """INSERT INTO audit_log
                   (company_id, user_id, event_type, toxic_flag, payload_encrypted)
                   VALUES (?,?,?,?,?)""",
                (company_id, user_id, event_type, int(toxic_flag), encrypted),
            )
            conn.commit()
            conn.close()
    except Exception as exc:
        # Audit logging must never crash the main flow
        print(f"[audit_log] Failed to write log entry: {exc}")
