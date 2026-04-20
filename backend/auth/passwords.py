"""Password hashing and verification using passlib bcrypt.

Uses BCRYPT_ROUNDS from config to control the work factor.
The CryptContext is created at module level for efficiency (avoid re-creating it
on every call, but tests can force a reload via importlib).
"""
from passlib.context import CryptContext

import config

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=config.BCRYPT_ROUNDS,
)


def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        plain: The plain-text password to hash.

    Returns:
        A bcrypt hash string (e.g. ``$2b$12$...``).
    """
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain: The plain-text password to check.
        hashed: The stored bcrypt hash.

    Returns:
        ``True`` if the password matches, ``False`` otherwise.
    """
    return _pwd_context.verify(plain, hashed)


def dummy_verify() -> None:
    """Hash a dummy password to prevent user-enumeration timing attacks.

    Call this when a username is not found in the database so the response
    time is indistinguishable from a successful lookup that fails password
    verification.
    """
    _pwd_context.verify("dummy-password", hash_password("dummy-password"))
