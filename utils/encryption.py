"""
utils/encryption.py
-------------------
Fernet symmetric encryption used for audit-log entries.
The key is loaded from ENCRYPTION_KEY env var.
If the key is missing a new one is generated at runtime (dev mode).
"""

import os
import base64
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def _load_fernet() -> Fernet:
    """Load or auto-generate a Fernet cipher instance."""
    key = os.getenv("ENCRYPTION_KEY", "").strip()
    if key:
        # Try as-is first, then try converting standard base64 → url-safe base64
        candidates = [key, key.replace("+", "-").replace("/", "_")]
        for candidate in candidates:
            # Add padding if missing
            pad = len(candidate) % 4
            if pad:
                candidate += "=" * (4 - pad)
            try:
                return Fernet(candidate.encode())
            except Exception:
                continue
        print(
            f"[encryption] WARNING: ENCRYPTION_KEY could not be loaded. "
            f"Falling back to ephemeral key – audit logs won't persist across restarts."
        )
    new_key = Fernet.generate_key().decode()
    print(
        f"[encryption] INFO: Using ephemeral key. "
        f"Set ENCRYPTION_KEY={new_key} to persist audit logs."
    )
    return Fernet(new_key.encode())


_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _load_fernet()
    return _fernet


def encrypt(plaintext: str) -> str:
    """
    Encrypt a UTF-8 string and return a url-safe base64 token string.

    Raises:
        RuntimeError: if encryption fails.
    """
    try:
        token = _get_fernet().encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"Encryption failed: {exc}") from exc


def decrypt(token: str) -> str:
    """
    Decrypt a Fernet token string back to plaintext.

    Returns:
        Decrypted UTF-8 string, or '[decryption error]' on failure.
    """
    try:
        plaintext = _get_fernet().decrypt(token.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken:
        return "[decryption error: invalid token or wrong key]"
    except Exception as exc:
        return f"[decryption error: {exc}]"
