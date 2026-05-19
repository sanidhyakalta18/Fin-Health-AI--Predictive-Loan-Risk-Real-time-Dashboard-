"""
Lightweight local auth for the Streamlit app (JSON-backed, session state).

Not production-grade security — suitable for demos and local portfolios.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from src.core.config import get_config

logger = logging.getLogger(__name__)
USERS_DIR = get_config().users_dir
REGISTRY_PATH = USERS_DIR / "registry.json"

_PBKDF2_ITERATIONS = 120_000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def _verify_password(password: str, salt_hex: str, password_hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, digest_hex = _hash_password(password, salt)
    return secrets.compare_digest(digest_hex, password_hash_hex)


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        return {"users": {}}
    try:
        with REGISTRY_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.exception("User registry is not valid JSON: %s", REGISTRY_PATH)
        raise ValueError(
            f"User registry at {REGISTRY_PATH} is corrupted. "
            "Back it up, remove it, and create accounts again."
        ) from exc
    if "users" not in data:
        data["users"] = {}
    return data


def _save_registry(data: dict[str, Any]) -> None:
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved user registry with %d user(s).", len(data.get("users", {})))


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(email: str, password: str, display_name: str) -> tuple[bool, str]:
    """Create a new account. Returns ``(ok, message)``."""
    email_n = _normalize_email(email)
    if not email_n or "@" not in email_n:
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    name = (display_name or email_n.split("@")[0]).strip()
    if not name:
        return False, "Display name is required."

    reg = _load_registry()
    if email_n in reg["users"]:
        return False, "An account with this email already exists."

    salt_hex, hash_hex = _hash_password(password)
    reg["users"][email_n] = {
        "display_name": name,
        "salt": salt_hex,
        "password_hash": hash_hex,
        "created_at": _now_iso(),
    }
    _save_registry(reg)
    return True, "Account created. You can sign in now."


def authenticate(email: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
    """Validate credentials. Returns ``(ok, message, user_record)``."""
    email_n = _normalize_email(email)
    reg = _load_registry()
    user = reg["users"].get(email_n)
    if not user:
        return False, "Unknown email or incorrect password.", None
    if not _verify_password(password, user["salt"], user["password_hash"]):
        return False, "Unknown email or incorrect password.", None
    return True, "Signed in.", {"email": email_n, "display_name": user["display_name"]}


def user_exists(email: str) -> bool:
    return _normalize_email(email) in _load_registry()["users"]
