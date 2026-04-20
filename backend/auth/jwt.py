"""JWT token creation and validation.

Functions:
    create_access_token — creates a short-lived access JWT (15 min by default).
    create_refresh_token — creates a long-lived refresh JWT (7 days by default).
    decode_token — decodes and validates an access JWT; raises HTTPException(401) on failure.
"""
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from jose import jwt, JWTError

import config


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    sucursales: list[int] | None,
) -> str:
    """Create a signed JWT access token with user identity and role claims.

    Args:
        user_id: Primary key of the user.
        username: Login name (included as a convenience claim).
        role: RBAC role string (e.g. 'admin', 'supervisor', 'vendedor').
        sucursales: List of branch IDs the user can access, or None for admin (all).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict = {
        "sub": str(user_id),          # JWT standard: subject must be a string
        "username": username,
        "role": role,
        "sucursales": sucursales,      # None → admin (unrestricted); list → restricted
        "iat": now,                    # issued-at — spec RF-AUTH-006
        "exp": expire,
    }

    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a signed JWT refresh token.

    The refresh token carries only the user identity and a 'type' discriminator
    so it cannot be misused as an access token.

    Args:
        user_id: Primary key of the user.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }

    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException(401): When the token is expired, has an invalid signature,
            is malformed, or uses an unexpected algorithm.
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],  # explicit allowlist — rejects other algs
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
