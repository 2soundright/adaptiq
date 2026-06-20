"""
utils/db_lock.py
----------------
Provides a reentrant file-lock context manager used for all SQLite
and ChromaDB write operations to prevent concurrent corruption.
"""

import os
from contextlib import contextmanager
from typing import Generator

from filelock import FileLock, Timeout

_DEFAULT_LOCK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "db.lock")
_LOCK_PATH = os.getenv("DB_LOCK_PATH", _DEFAULT_LOCK_PATH)
_LOCK_TIMEOUT = 30  # seconds


@contextmanager
def db_lock() -> Generator[None, None, None]:
    """
    Context manager that acquires an exclusive file lock before any write
    to SQLite or ChromaDB.  FileLock is reentrant for the same thread, so
    nested calls within a single thread are safe.
    """
    os.makedirs(os.path.dirname(_LOCK_PATH) or ".", exist_ok=True)
    lock = FileLock(_LOCK_PATH, timeout=_LOCK_TIMEOUT)
    try:
        with lock:
            yield
    except Timeout:
        raise RuntimeError(
            f"Could not acquire database lock at '{_LOCK_PATH}' "
            f"within {_LOCK_TIMEOUT}s – another process may be holding it."
        )
    except Exception as exc:
        raise RuntimeError(f"Unexpected error with database lock: {exc}") from exc
