"""FastAPI dependency functions for authentication and authorization.

Functions:
    get_current_user — extracts and validates Bearer token, returns UserInDB.
    get_current_active_user — wraps get_current_user, rejects inactive users.
    require_role — factory that returns a dependency enforcing role membership.
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, Header, status

from auth.jwt import decode_token
from auth.models import UserInDB
from auth.repository import get_user_by_username, get_user_sucursales


async def get_current_user(
    authorization: str | None = Header(None),
) -> UserInDB:
    """Extract and validate a Bearer JWT; return the authenticated UserInDB.

    Args:
        authorization: Value of the HTTP Authorization header (injected by FastAPI).

    Returns:
        UserInDB instance with ``sucursales`` list attached.

    Raises:
        HTTPException(401): When the header is missing/malformed, the token is
            invalid/expired, or the username is not found in the database.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ")

    # decode_token raises HTTPException(401) on invalid/expired token — let it propagate
    payload = decode_token(token)

    username: str | None = payload.get("username")

    user_dict = get_user_by_username(username)
    if user_dict is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sucursales = get_user_sucursales(user_dict["id"])

    user = UserInDB(**user_dict)
    user.sucursales = sucursales
    return user


async def get_current_active_user(
    user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Reject inactive users; pass active ones through unchanged.

    Args:
        user: Authenticated user from ``get_current_user``.

    Returns:
        The same UserInDB if the user is active.

    Raises:
        HTTPException(401): When ``user.is_active`` is False.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )
    return user


def require_role(*roles: str) -> Callable:
    """Factory — returns a FastAPI dependency that enforces role membership.

    Args:
        *roles: One or more allowed role names (e.g. "admin", "gerente").

    Returns:
        An async dependency function suitable for ``Depends(require_role(...))``.

    Example::

        @router.get("/secret")
        def secret(user = Depends(require_role("admin", "gerente"))):
            ...

    Raises:
        HTTPException(403): When the authenticated user's role is not in *roles*.
    """
    async def _check_role(
        user: UserInDB = Depends(get_current_active_user),
    ) -> UserInDB:
        if user.role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return _check_role
